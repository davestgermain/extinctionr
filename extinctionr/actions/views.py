from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.html import strip_tags
from django.utils.http import http_date
from django.utils.timezone import now
from django.urls import reverse
from django.views.decorators.cache import never_cache

import csv
from datetime import timedelta
from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import Action, ActionRole, Attendee, TalkProposal
from .comm import notify_commitments


BOOTSTRAP_ATTRS = {'class': 'form-control text-center'}


class SignupForm(forms.Form):
    email = forms.EmailField(label="Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    name = forms.CharField(label="Your name", widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))
    promised = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    role = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs=BOOTSTRAP_ATTRS))
    next = forms.CharField(required=False, widget=forms.HiddenInput())
    notes = forms.CharField(required=False, initial='')
    commit = forms.IntegerField(required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control text-center', 'min': 0, 'max': 1000}))

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action')
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = qset = ActionRole.objects.filter(name__in=self.action.available_role_choices)
        if qset:
            self.fields['role'].required = True


class TalkProposalForm(forms.Form):
    location = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Your location'}))
    name = forms.CharField(label="Your name", required=True, widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))
    email = forms.EmailField(label="Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    phone = PhoneNumberField(label="Phone Number", required=False, widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Phone Number'}))


def list_actions(request):
    actions = Action.objects.filter(when__gte=now()).order_by('when')
    if not request.user.is_staff:
        actions = actions.filter(public=True)
    ctx = {
        'actions': actions,
    }
    resp = render(request, 'list_actions.html', ctx)
    if request.user.is_authenticated:
        resp['Cache-Control'] = 'private'
    if actions:
        resp['Last-Modified'] = http_date(actions.last().when.timestamp())
    return resp



def show_action(request, slug):
    action = get_object_or_404(Action, slug=slug)
    ctx = {'action': action}
    if request.user.is_authenticated:
        ctx['attendees'] = Attendee.objects.filter(action=action).select_related('contact').order_by('-mutual_commitment', '-promised')
        ctx['promised'] = ctx['attendees'].filter(promised__isnull=False)

    if action.when < now() and action.public:
        # don't allow signups for public actions that already happened
        ctx['already_happened'] = True
        form = None
    elif request.method == 'POST':
        form = SignupForm(request.POST, action=action)
        if form.is_valid():
            data = form.cleaned_data
            commit = abs(data['commit'] or 0)
            action.signup(data['email'],
                data['role'],
                name=data['name'][:100],
                promised=data['promised'],
                commit=commit,
                notes=data['notes'])
            next_url = data['next'] or request.headers.get('referer', '/')
            messages.success(request, "Thank you for signing up for {}!".format(action.name))
            if commit:
                messages.info(request, "We will notify you once at least %d others commit" % commit)
            return redirect(next_url)
    else:
        form = SignupForm(action=action)
    ctx['form'] = form
    ctx['photos'] = list(action.photos.all())
    resp = render(request, 'action.html', ctx)
    resp['Last-Modified'] = http_date(action.modified.timestamp())
    if request.user.is_authenticated:
        resp['Cache-Control'] = 'private'
    return resp


@never_cache
def show_attendees(request, action_slug):
    action = get_object_or_404(Action, slug=action_slug)
    out_fmt = request.GET.get('fmt', 'json')
    attendees = Attendee.objects.filter(action=action).select_related('contact').order_by('contact__last_name')
    num = attendees.count()
    if num > 10:
        half = int(num / 2)
    else:
        half = None
    if out_fmt == 'html':
        ctx = {'attendees': attendees, 'half': half, 'can_change': request.user.is_staff, 'slug': action_slug}
        resp = render(request, 'attendees.html', ctx)
    elif out_fmt == 'csv' and request.user.has_perm('actions.view_attendee'):
        resp = HttpResponse()
        resp['Content-Type'] = 'text/csv'
        csv_writer = csv.writer(resp)
        header = ('Email', 'First Name', 'Last Name', 'Phone', 'Promised')
        csv_writer.writerow(header)
        for attendee in attendees:
            csv_writer.writerow((attendee.contact.email, attendee.contact.first_name, attendee.contact.last_name, attendee.contact.phone, attendee.promised))
    return resp


@login_required
def send_notifications(request, action_slug):
    action = get_object_or_404(Action, slug=action_slug)
    if request.method == 'POST':
        threshold = int(request.POST['threshold'])
        action_url = request.build_absolute_uri(reverse('actions:action', kwargs={'slug': action_slug}))
        num = notify_commitments(action, threshold, action_url)
        if num:
            messages.success(request, 'Notified %d attendees of their commitment!' % num)
    return redirect(action.get_absolute_url())


def propose_talk(request):
    ctx = {}
    if request.method == 'POST':
        form = TalkProposalForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            sname = data['name'].split(' ', 1)
            if len(sname) == 2:
                first_name, last_name = sname
            else:
                first_name = sname[0]
                last_name = 'unknown'
            prop = TalkProposal.objects.propose(
                strip_tags(data['location']),
                data['email'],
                phone=data['phone'],
                first_name=first_name,
                last_name=last_name)
            ctx['created'] = prop
            messages.success(request, 'Thank you, {}!'.format(prop.requestor))
            messages.info(request, 'Somebody from Extinction Rebellion will contact you soon to arrange a talk at {}'.format(prop.location))
            return redirect(reverse('extinctionr.actions:talk-proposal'))
    else:
        form = TalkProposalForm()
    ctx['form'] = form
    return render(request, 'talkproposal.html', ctx)


@login_required
def mark_promised(request, action_slug):
    if request.user.has_perm('action.change_attendee'):
        attendee = get_object_or_404(Attendee, pk=request.POST['id'], action__slug=action_slug)
        if not attendee.promised:
            attendee.promised = now()
            attendee.save()
    return JsonResponse({'status': 'ok'})


@login_required
@never_cache
def list_proposals(request):
    ctx = {
        'talks': TalkProposal.objects.select_related('requestor').order_by('responded', '-created')
    }
    return render(request, 'list_talks.html', ctx)



@login_required
@never_cache
def talk_respond(request, talk_id):
    talk = get_object_or_404(TalkProposal, pk=talk_id)
    if request.method == 'POST' and not talk.responded:
        talk.responded = now()
        talk.responder = request.user
        talk.save()
    return JsonResponse({'id': talk.id})


@login_required
@never_cache
def convert_proposal_to_action(request, talk_id):
    talk = get_object_or_404(TalkProposal, pk=talk_id)
    if request.method == 'POST' and talk.responded:
        act = Action()
        act.name = "XR Talk at {}".format(talk.location.strip())
        act.when = now() + timedelta(days=7)
        act.public = False
        act.description = '''Heading to extinction (and what to do about it)

This talk will be at {}
'''.format(talk.location)
        act.slug = 'xr-talk-%d' % talk.id
        try:
            act.save()
        except IntegrityError:
            act = Action.objects.get(slug=act.slug)
        url = '/admin/actions/action/%d/change/' % act.id
        return JsonResponse({'next': url})



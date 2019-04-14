from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.html import strip_tags
from django.utils.http import http_date
from django.utils.timezone import now
from django.urls import reverse
from django.views.decorators.cache import never_cache

from datetime import timedelta
from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import Action, ActionRole, Attendee, TalkProposal

BOOTSTRAP_ATTRS = {'class': 'form-control text-center'}


class SignupForm(forms.Form):
    email = forms.EmailField(label="Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    name = forms.CharField(label="Your name", widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))
    promised = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    role = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs=BOOTSTRAP_ATTRS))
    next = forms.CharField(required=False, widget=forms.HiddenInput())
    commit = forms.IntegerField(required=False, initial=0, widget=forms.NumberInput(attrs=BOOTSTRAP_ATTRS))

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


def signup_form(request, action_slug):
    action = get_object_or_404(Action, slug=action_slug)
    ctx = {'action': action}
    if action.when < now():
        ctx['already_happened'] = True
        form = None
    elif request.method == 'POST':
        form = SignupForm(request.POST, action=action)
        if form.is_valid():
            data = form.cleaned_data
            action.signup(data['email'],
                data['role'],
                name=data['name'][:100],
                promised=data['promised'],
                commit=data['commit'] or 0)
            next_url = data['next'] or request.headers.get('referer', '/')
            messages.success(request, "Thank you for signing up for {}!".format(action.name))
            return redirect(next_url)
    else:
        form = SignupForm(action=action)
    ctx['form'] = form
    return render(request, 'signup.html', ctx)


def show_action(request, slug):
    action = get_object_or_404(Action, slug=slug)
    attendees = Attendee.objects.filter(action=action).select_related('contact')
    ctx = {'action': action, 'attendees': attendees}
    if action.when < now():
        ctx['already_happened'] = True
        form = None
    elif request.method == 'POST':
        form = SignupForm(request.POST, action=action)
        if form.is_valid():
            data = form.cleaned_data
            action.signup(data['email'],
                data['role'],
                name=data['name'][:100],
                promised=data['promised'],
                commit=data['commit'])
            next_url = data['next'] or request.headers.get('referer', '/')
            messages.success(request, "Thank you for signing up for {}!".format(action.name))
            return redirect(next_url)
    else:
        form = SignupForm(action=action)
    ctx['form'] = form

    resp = render(request, 'action.html', ctx)
    resp['Last-Modified'] = http_date(action.modified.timestamp())
    if request.user.is_authenticated:
        resp['Cache-Control'] = 'no-cache'
    return resp


@never_cache
def show_attendees(request, action_slug):
    action = get_object_or_404(Action, slug=action_slug)
    out_fmt = request.GET.get('fmt', 'json')
    attendees = Attendee.objects.filter(action=action).select_related('contact')
    if out_fmt == 'html':
        ctx = {'attendees': attendees}
        return render(request, 'attendees.html', ctx)


def propose_talk(request):
    ctx = {}
    if request.method == 'POST':
        form = TalkProposalForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            sname = data['name'].split(' ')
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



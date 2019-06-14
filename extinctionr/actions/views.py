import calendar
import csv

from collections import defaultdict
from datetime import timedelta, datetime

from django.conf import settings
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
from django.views.decorators.cache import never_cache, cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from django import forms
from phonenumber_field.formfields import PhoneNumberField

from extinctionr.utils import get_last_contact, set_last_contact, get_contact
from .models import Action, ActionRole, Attendee, TalkProposal
from .comm import notify_commitments


BOOTSTRAP_ATTRS = {'class': 'form-control text-center'}

class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ('name', 'when', 'description', 'public', 'location', 'tags', 'slug', 'accessibility')


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


@cache_page(1200)
@csrf_protect
def list_actions(request):
    can_add = request.user.has_perm('actions.add_action')
    if request.method == 'POST' and can_add:
        form = ActionForm(request.POST)
        if form.is_valid():
            action = form.save()
            return redirect(action.get_absolute_url())
        else:
            print(form.errors)
    elif request.GET.get('format', '') == 'ical':
        import icalendar
        actions = Action.objects.filter(when__gte=now()).order_by('when')
        if not request.user.is_staff:
            actions = actions.filter(public=True)
        thecal = icalendar.Calendar()
        thecal.add('prodid', '-//XR Calendar//xrmass.org//')
        thecal.add('version', '2.0')
        current_time = now().strftime('%Y%m%dT%H%M%SZ')
        for action in actions:
            evt = icalendar.Event()
            evt['uid'] = '{}@{}'.format(action.id, request.get_host())
            evt['last-modified'] = action.modified.strftime('%Y%m%dT%H%M%SZ')
            evt['summary'] = action.name
            evt['dtstart'] = action.when
            evt['dtend'] = action.when + timedelta(hours=1)
            evt['dtstamp'] = current_time
            evt['location'] = action.location
            thecal.add_component(evt)
        response = HttpResponse(thecal.to_ical(), content_type='text/calendar')
        return response

    today = now().date()
    current_date = today.replace(day=1)
    ctx = {}
    req_date = request.GET.get('month','')
    if req_date:
        current_date = datetime.strptime(req_date, '%Y-%m')
        ctx['is_cal'] = True
        actions = None
    else:
        actions = Action.objects.filter(when__gte=now()).order_by('when')
        if not request.user.is_staff:
            actions = actions.filter(public=True)
        ctx['upcoming'] = actions[:5]
    ctx['next_month'] = current_date + timedelta(days=31)
    ctx['last_month'] = current_date + timedelta(days=-1)

    cal_days = list(calendar.Calendar().itermonthdates(current_date.year, current_date.month))
    this_month = []
    this_week = []
    month_actions = defaultdict(list)
    qset = Action.objects.filter(when__date__range=(cal_days[0], cal_days[-1]))
    if not request.user.is_staff:
        qset = qset.filter(public=True)

    for action in qset:
        month_actions[action.when.date()].append(action)

    for daynum, mdate in enumerate(cal_days, 1):
        todays_actions = month_actions[mdate]
        obj = {
            'day': mdate,
            'events': todays_actions,
        }
        if mdate.month == current_date.month:
            for a in todays_actions:
                tagnames = a.tags.names()
                if 'talk' in tagnames:
                    obj['bg'] = 'xr-bg-pink'
                elif 'action' in tagnames:
                    obj['bg'] = 'xr-bg-light-green'
                elif 'meeting' in tagnames:
                    obj['bg'] = 'xr-bg-lemon'
                elif 'nvda' in tagnames:
                    obj['bg'] = 'xr-bg-light-blue'
                elif 'art' in tagnames:
                    obj['bg'] = 'xr-bg-warm-yellow'
        else:
            # previous month
            obj['bg'] = 'bg-light'
        if mdate == today:
            obj['today'] = True
        this_week.append(obj)
        if daynum % 7 == 0:
            this_month.append(this_week)
            this_week = []
    if this_week:
        this_month.append(this_week)
    ctx['month'] = this_month
    ctx['can_add'] = can_add
    if ctx['can_add']:
        ctx['form'] = ActionForm()
    ctx['current_date'] = current_date
    resp = render(request, 'list_actions.html', ctx)
    resp['Vary'] = 'Cookie'

    if request.user.is_authenticated:
        resp['Cache-Control'] = 'private'
    if actions:
        resp['Last-Modified'] = http_date(actions.last().when.timestamp())
    return resp



@cache_page(1200)
def show_action(request, slug):
    action = get_object_or_404(Action, slug=slug)
    ctx = {'action': action}
    if request.user.is_authenticated:
        ctx['attendees'] = Attendee.objects.filter(action=action).select_related('contact').order_by('-mutual_commitment', '-promised', 'pk')
        ctx['promised'] = ctx['attendees'].filter(promised__isnull=False)
        ctx['default_to_email'] = settings.DEFAULT_FROM_EMAIL
    if action.when < now() and action.public:
        # don't allow signups for public actions that already happened
        ctx['already_happened'] = True
        form = None
    elif request.method == 'POST':
        form = SignupForm(request.POST, action=action)
        if form.is_valid():
            data = form.cleaned_data
            commit = abs(data['commit'] or 0)
            atten = action.signup(data['email'],
                data['role'],
                name=data['name'][:100],
                promised=data['promised'],
                commit=commit,
                notes=data['notes'])
            next_url = data['next'] or request.headers.get('referer', '/')
            messages.success(request, "Thank you for signing up for {}!".format(action.name))
            if commit:
                messages.info(request, "We will notify you once at least %d others commit" % commit)
            set_last_contact(request, atten.contact)
            return redirect(next_url)
    else:
        contact = get_contact(email=request.user.email) if request.user.is_authenticated else get_last_contact(request)
        initial = {}
        if contact:
            initial['email'] = contact.email
            initial['name'] = str(contact)
        form = SignupForm(action=action, initial=initial)
    ctx['form'] = form
    ctx['has_roles'] = list(action.available_role_choices)
    ctx['photos'] = list(action.photos.all())
    resp = render(request, 'action.html', ctx)
    resp['Vary'] = 'Cookie'
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
            prop = TalkProposal.objects.propose(
                strip_tags(data['location']),
                data['email'],
                phone=data['phone'],
                name=data['name'])
            ctx['created'] = prop
            messages.success(request, 'Thank you, {}!'.format(prop.requestor))
            messages.info(request, 'Somebody from Extinction Rebellion will contact you soon to arrange a talk at {}'.format(prop.location))
            set_last_contact(request, prop.requestor)
            return redirect(reverse('extinctionr.actions:talk-proposal'))
    else:
        contact = get_last_contact(request)
        initial = {}
        if contact:
            initial['email'] = contact.email
            initial['name'] = str(contact)
            initial['phone'] = contact.phone
        form = TalkProposalForm(initial=initial)
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
        'talks': TalkProposal.objects.select_related('requestor').order_by('-responded', 'created')
    }
    template = 'list_talks'
    if request.GET.get('format', 'html') == 'csv':
        template += '.csv'
        content_type = 'text/csv'
        content_disposition = 'attachment; filename="talks.csv"'
    else:
        template += '.html'
        content_type = 'text/html'
        content_disposition = None
    response = render(request, template, ctx)
    response['content-type'] = content_type
    if content_disposition:
        response['content-disposition'] = content_disposition
    return response



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


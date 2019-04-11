from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.html import strip_tags
from django.utils.timezone import now

from datetime import timedelta
from django import forms
from phonenumber_field.formfields import PhoneNumberField

from .models import Action, Attendee, TalkProposal


class SignupForm(forms.Form):
    email = forms.EmailField(label="Email", required=True)
    name = forms.CharField(label="Your name")
    promised = forms.BooleanField(required=False)
    role = forms.CharField(required=False)
    next = forms.CharField(required=False)


class TalkProposalForm(forms.Form):
    location = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    name = forms.CharField(label="Your name", required=True)
    email = forms.EmailField(label="Email", required=True)
    phone = PhoneNumberField(label="Phone Number", required=False)


def signup_form(request, action_slug):
    action = get_object_or_404(Action, slug=action_slug)
    ctx = {'action': action}
    if action.when < now():
        ctx['already_happened'] = True
        form = None
    elif request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            action.signup(data['email'], data['role'], name=data['name'][:100], promised=data['promised'])
            next_url = data['next'] or request.headers.get('referer', '/')
            return redirect(next_url)
    else:
        form = SignupForm()
    ctx['form'] = form
    return render(request, 'signup.html', ctx)


def show_action(request, slug):
    action = get_object_or_404(Action, slug=slug)
    attendees = Attendee.objects.filter(action=action).select_related('contact')
    ctx = {'action': action, 'attendees': attendees}
    return render(request, 'action.html', ctx)


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
            first_name, last_name = data['name'].split(' ', 1)
            prop = TalkProposal.objects.propose(
                strip_tags(data['location']),
                data['email'],
                phone=data['phone'],
                first_name=first_name,
                last_name=last_name)
            ctx['created'] = prop
    else:
        form = TalkProposalForm()
    ctx['form'] = form
    return render(request, 'talkproposal.html', ctx)


@login_required
def list_proposals(request):
    ctx = {
        'talks': TalkProposal.objects.select_related('requestor').order_by('responded', '-created')
    }
    return render(request, 'list_talks.html', ctx)


@login_required
def talk_respond(request, talk_id):
    talk = get_object_or_404(TalkProposal, pk=talk_id)
    if request.method == 'POST' and not talk.responded:
        talk.responded = now()
        talk.responder = request.user
        talk.save()
    return JsonResponse({'id': talk.id})


@login_required
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



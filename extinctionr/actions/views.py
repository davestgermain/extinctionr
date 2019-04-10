from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django import forms

from .models import Action, Attendee


class SignupForm(forms.Form):
	email = forms.EmailField(label="Email", required=True)
	name = forms.CharField(label="Your name")
	promised = forms.BooleanField(required=False)
	role = forms.CharField(required=False)
	next = forms.CharField(required=False)


def signup_form(request, action_slug):
	action = get_object_or_404(Action, slug=action_slug)
	if request.method == 'POST':
		form = SignupForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			action.signup(data['email'], data['role'], name=data['name'][:100], promised=data['promised'])
			next_url = data['next'] or request.headers.get('referer', '/')
			return redirect(next_url)
	else:
		form = SignupForm()
	ctx = {'action': action, 'form': form}
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

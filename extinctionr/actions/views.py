from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django import forms

from .models import Action, Attendee


class SignupForm(forms.Form):
	email = forms.EmailField(label="Email", required=True)
	name = forms.CharField(label="Your name")
	promised = forms.BooleanField(required=False)
	role = forms.CharField(required=False)


def signup_form(request, action_id):
	action = get_object_or_404(Action, pk=action_id)
	if request.method == 'POST':
		form = SignupForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			print(data)
			action.signup(data['email'], data['role'])
			return redirect('/')
	else:
		form = SignupForm()
	ctx = {'action': action, 'form': form}
	return render(request, 'signup.html', ctx)


def show_action(request, action_id):
	action = get_object_or_404(Action, pk=action_id)
	attendees = Attendee.objects.filter(action=action).select_related('contact')
	ctx = {'action': action, 'attendees': attendees}
	return render(request, 'action.html', ctx)

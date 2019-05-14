from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib import messages
from django.http import HttpResponseForbidden
from django import forms
from django.views import generic
from extinctionr.utils import get_contact, get_last_contact, set_last_contact
from .models import Circle, Contact
from dal import autocomplete


class ContactForm(forms.Form):
    contact = forms.ModelChoiceField(
        required=False,
        queryset=Contact.objects.all(),
        label='Lookup',
        widget=autocomplete.ModelSelect2(url='circles:person-autocomplete', attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    name = forms.CharField(required=False, label="Name", widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))
    role = forms.CharField(required=True, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data['contact']:
            if cleaned_data['role'] == 'lead':
                raise forms.ValidationError('contact required')
            if not (cleaned_data['email'] and cleaned_data['name']):
                raise forms.ValidationError('email or contact required')
        return cleaned_data


class MembershipRequestForm(forms.Form):
    email = forms.EmailField(label="Email", required=True, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    name = forms.CharField(required=True, label="Name", widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))
    circle_id = forms.IntegerField(required=True, widget=forms.HiddenInput())


@login_required
def add_member(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    form = ContactForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        email = data['email'].lower()
        name = data['name']
        contact = data['contact']
        if data['role'] == 'lead':
            circle.leads.add(contact)
        else:
            circle.add_member(email, name, contact=contact)
    return redirect(circle.get_absolute_url())


@login_required
def del_member(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    contact = get_object_or_404(Contact, pk=request.POST['id'])
    me = get_contact(email=request.user.email)
    if me == contact or circle.can_manage(request.user):
        if request.POST['role'] == 'lead':
            circle.leads.remove(contact)
        else:
            circle.members.remove(contact)
    return redirect(circle.get_absolute_url())

@login_required
def approve_membership(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    contact = get_object_or_404(Contact, pk=request.POST['id'])
    if circle.can_manage(request.user):
        circle.approve_membership(contact, who=get_contact(email=request.user.email))
        messages.success(request, "Approved {}!".format(contact))

    return redirect(circle.get_absolute_url())


def request_membership(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    if request.method == 'POST':
        form = MembershipRequestForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            contact = circle.request_membership(data['email'], data['name'])
            if not request.user.is_authenticated:
                set_last_contact(request, contact)
            messages.success(request, "Thank you for signing up for {}!".format(circle))
    return redirect(circle.get_absolute_url())


@login_required
def person_view(request, contact_id=None):
    if contact_id is None:
        contact = get_contact(email=request.user.email)
    else:
        contact = get_object_or_404(Contact, pk=contact_id)
    ctx = {'contact': contact, 'is_me': contact == get_contact(email=request.user.email)}
    response = render(request, 'circles/person.html', ctx)
    response['Cache-Control'] = 'private'
    return response


@method_decorator(cache_page(1200), name='dispatch')
class CircleView(generic.DetailView):
    template_name = 'circles/circle.html'
    def get_queryset(self):
        return Circle.objects.select_related('parent').prefetch_related('leads', 'members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        circle = context['object']
        if self.request.user.is_authenticated:
            is_lead = circle.can_manage(self.request.user)
            context['is_member'] = circle.is_member(self.request.user)
            context['can_see_members'] = is_lead or self.request.user.has_perm('circles.view_circle')
            context['can_see_leads'] = self.request.user.is_authenticated
            context['is_lead'] = is_lead
            context['members'] = circle.member_list
            context['pending'] = circle.membershiprequest_set.filter(confirmed_by=None)
            context['form'] = ContactForm(initial={'role': 'member'})
            context['lead_form'] = ContactForm(initial={'role': 'lead'})
        if not context.get('is_lead', None):
            initial = {'circle_id': circle.id}
            last_contact = get_last_contact(self.request)
            if last_contact:
                initial['email'] = last_contact.email
                initial['name'] = str(last_contact)
            context['request_form'] = MembershipRequestForm(initial=initial)
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Vary'] = 'Cookie'
        if self.request.user.is_authenticated:
            response['Cache-Control'] = 'private'
        return response


@method_decorator(cache_page(1200), name='dispatch')
class TopLevelView(generic.ListView):
    template_name = 'circles/outer.html'

    def get_queryset(self):
        return Circle.objects.filter(parent__isnull=True).prefetch_related('leads', 'members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_see_members'] = self.request.user.has_perm('circles.view_circle')
        context['can_see_leads'] = self.request.user.is_authenticated
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Vary'] = 'Cookie'
        if self.request.user.is_authenticated:
            response['Cache-Control'] = 'private'
        return response


class ContactAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contact.objects.none()

        qs = Contact.objects.all()

        if self.q:
            qs = qs.filter(email__istartswith=self.q) | qs.filter(first_name__istartswith=self.q)

        return qs


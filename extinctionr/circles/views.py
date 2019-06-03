from io import TextIOWrapper
import csv

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic.edit import FormView
from django.utils.timezone import now
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django import forms
from django.views import generic
from extinctionr.utils import get_contact, get_last_contact, set_last_contact
from extinctionr.actions.models import Action
from .models import Circle, Contact, CircleJob
from dal import autocomplete

from taggit.models import Tag


class ContactForm(forms.Form):
    contact = forms.ModelChoiceField(
        required=False,
        queryset=Contact.objects.all(),
        label='Lookup',
        widget=autocomplete.ModelSelect2(url='circles:person-autocomplete', attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={'class': 'form-control text-center', 'placeholder': 'Email Address'}))
    name = forms.CharField(required=False, label="Name", widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': 'Your Name'}))
    role = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'form-control text-center custom-select custom-select-lg', 'placeholder': 'Role'}))

    def __init__(self, circle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = circle.get_role_choices()

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


class FindPeopleForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Tag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'class': 'form-control', 'placeholder': 'Tags'})
    )
    actions = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Action.objects.all().order_by('-when'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )


@login_required
def add_member(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    form = ContactForm(circle, request.POST)
    if form.is_valid() and circle.can_manage(request.user):
        data = form.cleaned_data
        email = data['email'].lower()
        name = data['name']
        contact = data['contact']
        role = data['role']
        circle.add_member(email, name, contact=contact, role=role)
    return redirect(circle.get_absolute_url())


@login_required
def del_member(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    contact = get_object_or_404(Contact, pk=request.POST['id'])
    me = get_contact(email=request.user.email)
    if me == contact or circle.can_manage(request.user):
        role = request.POST.get('role', 'member')
        circle.remove_member(contact, role=role, who=request.user)
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
            if contact and not request.user.is_authenticated:
                set_last_contact(request, contact)
                circle_requests = request.session.get('circle_requests', {})
                circle_requests[str(circle.id)] = True
                request.session['circle_requests'] = circle_requests
            messages.success(request, "Thank you for signing up for {}!".format(circle))
    return redirect(circle.get_absolute_url())


@login_required
def person_view(request, contact_id=None):
    if contact_id is None:
        contact = get_contact(email=request.user.email)
    else:
        contact = get_object_or_404(Contact, pk=contact_id)
    ctx = {
        'contact': contact,
        'leads': Circle.objects.filter(circlemember__contact=contact, circlemember__role__in=['int','ext']).distinct(),
        'members': Circle.objects.filter(circlemember__contact=contact, circlemember__role='member'),
        'is_me': contact == get_contact(email=request.user.email),
        }
    response = render(request, 'circles/person.html', ctx)
    response['Cache-Control'] = 'private'
    return response


def find_field(fields, search_for):
    for field in fields:
        if field.lower().startswith(search_for):
            return field
    raise ValueError(search_for)


@login_required
def csv_import(request):
    ctx = {}
    can_import = request.user.has_perm('circles.change_circle')
    ctx['can_import'] = can_import
    if can_import and request.method == 'POST':
        f = TextIOWrapper(request.FILES['csv'].file, encoding=request.encoding)
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        email_field = find_field(fields, 'email')
        first_name_field = find_field(fields, ('first', 'first name', 'fname'))
        last_name_field = find_field(fields, ('last', 'last name', 'lname'))
        try:
            wg_field = find_field(fields, ('circle', 'working group', 'wg'))
        except ValueError:
            wg_field = None

        try:
            phone_field = find_field(fields, ('phone number', 'phone'))
        except ValueError:
            phone_field = None

        try:
            tag_field = find_field(fields, ('tags', 'tag'))
        except ValueError:
            tag_field = None

        contacts = set()
        memberships = []
        for row in reader:
            contact = get_contact(row[email_field],
                first_name=row[first_name_field],
                last_name=row[last_name_field],
                phone=row[phone_field] if phone_field else None)
            contacts.add(contact)
            messages.success(request, 'Found {}'.format(contact))
            if wg_field and row[wg_field]:
                wg = row[wg_field].split('-')[0].strip()
                try:
                    circle = Circle.objects.filter(name__iexact=wg).order_by('-pk')[0]
                except IndexError:
                    messages.error(request, 'Could not find circle named {}'.format(wg))
                else:
                    if circle.request_membership(contact=contact):
                        messages.success(request, 'Requested membership for {} to {}'.format(contact, circle))
            if tag_field and row[tag_field]:
                contact.tags.add(*[t.strip() for t in row[tag_field].split(',')])
        return redirect('circles:person-import')
    response = render(request, 'circles/csv.html', ctx)
    response['Cache-Control'] = 'private'
    return response


@method_decorator(cache_page(1200), name='dispatch')
class BaseCircleView(generic.View):
    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Vary'] = 'Cookie'
        if self.request.user.is_authenticated:
            response['Cache-Control'] = 'private'
        return response


class CircleView(BaseCircleView, generic.DetailView):
    template_name = 'circles/circle.html'
    def get_queryset(self):
        return Circle.objects.select_related('parent').prefetch_related('members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        circle = context['object']
        if self.request.user.is_authenticated:
            is_lead = circle.can_manage(self.request.user)
            context['is_member'] = circle.is_member(self.request.user)
            context['can_see_members'] = is_lead or self.request.user.has_perm('circles.view_circle')
            context['can_see_leads'] = self.request.user.is_authenticated
            context['is_lead'] = is_lead
            context['members'] = sorted(circle.recursive_members, key=lambda m: (m[0].last_name.lower(), m[0].first_name.lower()))
            context['pending'] = circle.membershiprequest_set.filter(confirmed_by=None)
            context['form'] = ContactForm(circle, initial={'role': 'member'})
            context['jobs'] = CircleJob.objects.filter(circle=circle)
            # if they're logged in, this is not relevant
            if 'circle_requests' in self.request.session:
                del self.request.session['circle_requests']
        if not context.get('is_lead', None):
            initial = {'circle_id': circle.id}
            last_contact = get_last_contact(self.request)
            if last_contact:
                initial['email'] = last_contact.email
                initial['name'] = str(last_contact)
            if not context.get('is_member'):
                context['request_form'] = MembershipRequestForm(initial=initial)
        if not (context.get('is_lead', None) or context.get('is_member', None)):
            context['is_pending'] = circle.is_pending(self.request)
        return context


class TopLevelView(BaseCircleView, generic.ListView):
    template_name = 'circles/outer.html'

    def get_queryset(self):
        return Circle.objects.filter(parent__isnull=True).prefetch_related('members')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_see_members'] = self.request.user.has_perm('circles.view_circle')
        context['can_see_leads'] = self.request.user.is_authenticated
        return context


class JobView(BaseCircleView, generic.TemplateView):
    template_name = 'circles/jobs.html'

    def post(self, request, *args, **kwargs):
        job = get_object_or_404(CircleJob, pk=request.POST['id'])
        job.filled = get_contact(email=self.request.user.email)
        job.filled_on = now()
        job.save()
        messages.success(request, "Thanks for signing up for this job!")
        return HttpResponse('ok')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobs'] = CircleJob.objects.filter(filled__isnull=True).select_related('circle')
        return context


@method_decorator(login_required, name='dispatch')
class FindFormView(FormView):
    template_name = 'circles/find.html'
    form_class = FindPeopleForm

    def form_valid(self, form):
        tags = form.cleaned_data['tags']
        actions = form.cleaned_data['actions']
        contacts = Contact.objects
        if tags:
            contacts = contacts.filter(tags__in=tags)
        if actions:
            contacts = contacts.filter(attendee__action__in=actions)

        if not (actions or tags):
            contacts = []
        else:
            contacts = contacts.distinct()
        ctx = {
            'form': FindPeopleForm(initial=form.cleaned_data),
            'tags': tags,
            'actions': actions,
            'contacts': contacts,
        }
        response = render(self.request, self.template_name, ctx)
        response['Cache-Control'] = 'private'
        return response


@login_required
def csv_export(request):
    if request.user.has_perm('contacts.view_contact'):
        contact_ids = [c for c in request.GET.get('contacts', '').split(',') if c]
        contacts = Contact.objects.filter(id__in=contact_ids)
    else:
        contacts = []
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="contacts.csv"'
    csv_writer = csv.writer(resp)
    header = ('Email', 'First Name', 'Last Name', 'Phone', 'City', 'Tags')
    csv_writer.writerow(header)
    for contact in contacts:
        csv_writer.writerow((
            contact.email,
            contact.first_name,
            contact.last_name,
            contact.phone,
            contact.address.city if contact.address else None,
            ','.join(contact.tags.names())))
    return resp



class ContactAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contact.objects.none()

        qs = Contact.objects.all()

        if self.q:
            qs = qs.filter(email__istartswith=self.q) | qs.filter(first_name__istartswith=self.q)

        return qs


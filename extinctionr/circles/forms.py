from django import forms
from dal import autocomplete
from taggit.models import Tag
from extinctionr.actions.models import Action
from .models import Contact


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
        queryset=Action.objects.filter(attendee__isnull=False).distinct().order_by('-when'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )


class CouchForm(forms.Form):
    availability = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Dates/times the room or couch is available'}))
    info = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Other info'}))
    public = forms.BooleanField(required=False, label="Show my contact on the public page")


WG_CHOICES = [
    ('ACTION', '<b>ACTION</b> – Help plan non-violent direct actions to engage with the public and demand more from the media and our leaders'),
    ('ART', '<b>ART</b> – Help make our actions memorable with art, drama, dance and music'),
    ('MEDIA', '<b>MEDIA + MESSAGING</b> – Construct press releases, prepare media packets, and communicate with media.'),
    ('OUTREACH', '<b>OUTREACH</b> – Recruit and engage members, build alliances and promote upcoming events'),
    ('REGENERATIVE CULTURE', '<b>REGENERATIVE CULTURE</b> – Foster organizational resilience through community-building and jail support'),
    ('INFRASTRUCTURE', '<b>INFRASTRUCTURE</b> – Create our digital infrastructure and train XR members to leverage it.'),
    ('FINANCE', '<b>FINANCE</b> – Raise money and transparently manage XR finances to ensure we can fund our activities'),
    ('UNKNOWN', "I'm not sure – please contact me"),
]

class IntakeForm(forms.Form):
    email = forms.EmailField(label="Email", required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}))
    zipcode = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zip Code'}))
    interests = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'What draws you to volunteer? What interests and skills do you bring to Extinction Rebellion?'}))
    other_groups = forms.CharField(required=True, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Please list any other climate or social justice groups, schools, labor unions or faith groups. Your answers will help us identify our connections to local organizations and build relationships with coalition partners.'}))
    working_group = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'form-control'}), choices=WG_CHOICES)
    committment = forms.ChoiceField(
            required=True,
            widget=forms.Select(attrs={'class': 'form-control text-center custom-select custom-select-lg'}),
            choices=[
                ('low', '2 hours per month'),
                ('medium', '2 hours, 2-4 times per month'),
                ('high', '1-3 hours per week'),
                ('full', 'as much as possible - this is an emergency')
            ])
    anything_else = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Anything else you want us to know?'}))

    def clean_zipcode(self):
        zipcode = self.cleaned_data['zipcode']
        if not (zipcode.isdigit() and len(zipcode) == 5):
            raise forms.ValidationError('Invalid zipcode')
        return zipcode


class ContactAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contact.objects.none()

        qs = Contact.objects.all()

        if self.q:
            qs = qs.filter(email__istartswith=self.q) | qs.filter(first_name__istartswith=self.q)

        return qs


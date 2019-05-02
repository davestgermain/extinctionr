import datetime
from hashlib import md5
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.timezone import now
from contacts.models import Contact
from extinctionr.info.models import Photo
from extinctionr.utils import get_contact
from markdownx.models import MarkdownxField


USER_MODEL = get_user_model()


class Action(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    when = models.DateTimeField(db_index=True)
    description = MarkdownxField(default='', blank=True, help_text='Markdown formatted')
    slug = models.SlugField(unique=True, help_text='Short form of the title, for URLs')
    public = models.BooleanField(default=True, blank=True, help_text='Whether this action should be listed publicly')
    location = models.TextField(default='', blank=True)
    available_roles = models.CharField(default='', blank=True, max_length=255, help_text='List of comma-separated strings')
    photos = models.ManyToManyField(Photo, blank=True)
    modified = models.DateTimeField(auto_now=True)
    show_commitment = models.BooleanField(blank=True, default=True, help_text='Whether to show the conditional commitment fields')
    max_participants = models.IntegerField(blank=True, default=0, help_text="Maximun number of people allowed to register")

    @property
    def available_role_choices(self):
        for role in self.available_roles.split(','):
            role = role.strip()
            if role:
                yield role
    
    def is_full(self):
        return self.max_participants and self.attendee_set.count() >= self.max_participants

    def get_absolute_url(self):
        return reverse('extinctionr.actions:action', kwargs={'slug': self.slug})

    def signup(self, email, role, name='', notes='', promised=None, commit=0):
        if not isinstance(role, ActionRole):
            role = ActionRole.objects.get_or_create(name=role or '')[0]

        user = get_contact(email, name=name)
        atten, created = Attendee.objects.get_or_create(action=self, contact=user, role=role)
        if not created:
            if notes:
                atten.notes = notes
        else:
            atten.notes = notes
            atten.mutual_commitment = commit
        if promised:
            atten.promised = now()
        atten.save()
        return atten

    def __str__(self):
        return '%s on %s' % (self.name, self.when.strftime('%b %e, %Y @ %H:%M'))

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)
        for role in self.available_role_choices:
            ActionRole.objects.get_or_create(name=role)
        return ret


class ActionRole(models.Model):
    name = models.CharField(max_length=100, db_index=True, unique=True)

    def __str__(self):
        return self.name


class Attendee(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
    role = models.ForeignKey(ActionRole, on_delete=models.DO_NOTHING)
    promised = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(default='', blank=True)
    mutual_commitment = models.IntegerField(default=0, blank=True, db_column='mutual_committment')
    created = models.DateTimeField(auto_now_add=True, null=True)
    notified = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        unique_together = ('action', 'contact', 'role')

    def __str__(self):
        return '%s %s %s' % (self.action, self.contact, self.role)

    def get_absolute_url(self):
        return self.action.get_absolute_url() + '#attendees'


class ProposalManager(models.Manager):
    def propose(self, location, email, phone='', name=''):
        contact = get_contact(email, name=name, phone=phone)
        prop = TalkProposal(requestor=contact)
        prop.location = location
        prop.save()
        return prop


class TalkProposal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    location = models.TextField()
    requestor = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
    responded = models.DateTimeField(null=True, blank=True)
    responder = models.ForeignKey(USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    objects = ProposalManager()

    def __str__(self):
        return 'Talk at %s for %s' % (self.location[:20], self.requestor)

    def get_absolute_url(self):
        return '/talk'


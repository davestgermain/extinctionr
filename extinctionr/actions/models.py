import datetime
from django.db import models, IntegrityError
from django.contrib.auth import get_user_model
from django.urls import reverse
from contacts.models import Contact
from markdownx.models import MarkdownxField


USER_MODEL = get_user_model()


class Action(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    when = models.DateTimeField(db_index=True)
    description = MarkdownxField(default='', blank=True)
    slug = models.SlugField(unique=True)
    public = models.BooleanField(default=True, blank=True)

    def get_absolute_url(self):
        return reverse('extinctionr.actions:action', kwargs={'slug': self.slug})

    def signup(self, email, role, name='', notes='', promised=None):
        db_role = ActionRole.objects.get_or_create(name=role)[0]
        try:
            user = Contact.objects.get(email=email)
        except Contact.DoesNotExist:
            first_name, last_name = name.split(' ', 1)
            user = Contact.objects.create(email=email, first_name=first_name, last_name=last_name)
        atten, created = Attendee.objects.get_or_create(action=self, contact=user, role=db_role)
        if not created:
            if notes:
                atten.notes = notes
        else:
            atten.notes = notes
        if promised:
            atten.promised = datetime.datetime.now()
        atten.save()
        return atten

    def __str__(self):
        return '%s on %s' % (self.name, self.when.strftime('%b %e, %Y @ %H:%M'))


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

    class Meta:
        unique_together = ('action', 'contact', 'role')

    def __str__(self):
        return '%s %s %s' % (self.action, self.contact, self.role)

class ProposalManager(models.Manager):
    def propose(self, location, email, phone='', first_name='', last_name=''):
        try:
            contact = Contact.objects.get(email=email)
        except Contact.DoesNotExist:
            contact = Contact.objects.create(email=email, phone=phone, first_name=first_name, last_name=last_name)

        prop = TalkProposal(requestor=contact)
        prop.location = location
        prop.save()
        return prop


class TalkProposal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    location = models.TextField()
    requestor = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
    responded = models.DateTimeField(null=True, blank=True)
    objects = ProposalManager()

    def __str__(self):
        return 'Talk at %s for %s' % (self.location[:20], self.requestor)


from django.db import models
from django.urls import reverse
from contacts.models import Contact
from extinctionr.utils import get_contact


class Circle(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, db_index=True)
    purpose = models.TextField(default='')
    leads = models.ManyToManyField(Contact, blank=True, related_name='leads')
    members = models.ManyToManyField(Contact, blank=True, related_name='members')
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    color = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        parents = list(p.name for p in self.parents)
        parents.reverse()
        parents.append(self.name)
        return ' :: '.join(parents)

    def get_all_members(self):
        members = set(self.members.all())
        for circle in self.circle_set.all():
            members.update(circle.get_all_members())
        return members

    def get_absolute_url(self):
        return reverse('circles:detail', kwargs={'pk': self.id})

    @property
    def parents(self):
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent

    @property
    def bgcolor(self):
        return self.color or self.parent.bgcolor

    @property
    def has_children(self):
        return self.circle_set.exists()
    
    def get_member_emails(self):
        emails = [m.email for m in self.members.all()]
        emails.extend(m.email for m in self.leads.all())
        return ','.join(emails)

    def add_member(self, email, name, contact=None):
        contact = contact or get_contact(email, name=name)
        self.members.add(contact)



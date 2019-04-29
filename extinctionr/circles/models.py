from django.db import models
from django.urls import reverse
from contacts.models import Contact



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

    def add_member(self, email, name):
        try:
            contact = Contact.objects.get(email=email)
        except Contact.DoesNotExist:
            sname = name.split(' ', 1)
            if len(sname) == 2:
                first_name, last_name = sname
            else:
                first_name = sname[0]
                last_name = '?'

            contact = Contact.objects.create(email=email, first_name=first_name, last_name=last_name)
        self.members.add(contact)



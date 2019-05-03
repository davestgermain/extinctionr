from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.urls import reverse
from contacts.models import Contact
from extinctionr.utils import get_contact
from django.utils.timezone import now


class Circle(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, db_index=True)
    purpose = models.TextField(default='', help_text='Describe the mandates for this group')
    leads = models.ManyToManyField(Contact, blank=True, related_name='leads')
    members = models.ManyToManyField(Contact, blank=True, related_name='members')
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    color = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(max_length=255, blank=True, null=True, help_text='Public email address for this group')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        parents = list(p.name for p in self.parents)
        parents.reverse()
        parents.append(self.name)
        return ' :: '.join(parents)

    def get_all_members(self):
        members = set(self.get_members())
        for circle in self.get_children():
            members.update(circle.get_all_members())
        return members

    def get_children(self):
        children = getattr(self, '_children', None)
        if children is None:
            self._children = children = self.circle_set.all().prefetch_related('members', 'leads')
        return children

    def get_members(self):
        members = getattr(self, '_members', None)
        if members is None:
            self._members = members = self.members.all().order_by('pk')
        return members

    def get_leads(self):
        leads = getattr(self, '_leads', None)
        if leads is None:
            self._leads = leads = self.leads.all()
        return leads

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
    
    @property
    def public_email(self):
        email = self.email
        if not email:
            email = self.parent.public_email if self.parent else ''
        return email

    def get_notification_addresses(self):
        addresses = set()
        public_address = self.public_email
        if public_address:
            addresses.add(public_address)
        for lead in self.get_leads():
            addresses.add(lead.email)
        return addresses

    def get_member_emails(self):
        emails = [m.email for m in self.get_members()]
        emails.extend(m.email for m in self.get_leads())
        return ','.join(emails)

    def add_member(self, email, name, contact=None):
        contact = contact or get_contact(email, name=name)
        self.members.add(contact)

    def request_membership(self, email, name):
        contact = get_contact(email, name=name)
        try:
            MembershipRequest.objects.get_or_create(circle=self, requestor=contact)
        except MultipleObjectsReturned:
            pass
        return contact

    def approve_membership(self, contact, who):
        for req in MembershipRequest.objects.filter(circle=self, requestor=contact):
            req.confirmed_by = who
            req.save()

    def can_manage(self, user):
        return user.has_perm('circles.change_circle') or self.leads.filter(pk=get_contact(email=user.email).id).exists()


class MembershipRequest(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE)
    requestor = models.ForeignKey(Contact, on_delete=models.CASCADE)
    confirmed_by = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL, related_name='confirmation_set')
    confirm_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s -> %s' % (self.requestor, self.circle)

    def get_absolute_url(self):
        return self.circle.get_absolute_url()

    def save(self, *args, **kwargs):
        if self.confirmed_by and not self.confirm_date:
            self.confirm_date = now()
        super().save(*args, **kwargs)
        if self.confirmed_by:
            self.circle.members.add(self.requestor)
        else:
            self.circle.members.remove(self.requestor)

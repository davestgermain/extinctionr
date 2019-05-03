from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.urls import reverse
from contacts.models import Contact
from extinctionr.utils import get_contact
from django.utils.timezone import now
from django.utils.functional import cached_property


class Circle(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, db_index=True)
    purpose = models.TextField(default='', help_text='Describe the mandates for this group')
    sensitive_info = models.TextField(default='', help_text='Information for members only')
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

    @cached_property
    def recursive_members(self):
        members = set(self.member_list)
        for circle in self.children:
            members.update(circle.recursive_members)
        return members

    @cached_property
    def children(self):
        return list(self.circle_set.all().prefetch_related('members', 'leads'))

    @cached_property
    def member_list(self):
        return list(self.members.all().order_by('pk'))

    @cached_property
    def lead_list(self):
        return list(self.leads.all())

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
    
    @cached_property
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
        for lead in self.lead_list:
            addresses.add(lead.email)
        return addresses

    def get_member_emails(self):
        emails = [m.email for m in self.member_list]
        emails.extend(m.email for m in self.lead_list)
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

    def is_member(self, user):
        email = user.email
        for member in self.recursive_members:
            if member.email == email:
                return True
        return False


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

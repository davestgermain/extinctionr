from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.urls import reverse
from contacts.models import Contact
from extinctionr.utils import get_contact
from django.utils.timezone import now
from django.utils.functional import cached_property

ROLE_CHOICES = {
    'int': 'Internal Coordinator',
    'ext': 'External Coordinator',
    'member': 'Member'
}


class Circle(models.Model):
    created = models.DateTimeField(db_index=True, auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, db_index=True)
    purpose = models.TextField(default='', help_text='Describe the mandates for this group')
    sensitive_info = models.TextField(default='', blank=True, help_text='Information for members only')
    members = models.ManyToManyField(to=Contact, through='CircleMember', blank=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    color = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(max_length=255, blank=True, null=True, help_text='Public email address for this group')
    available_roles = models.CharField(max_length=255, blank=True, default='int,ext,member', help_text='Comma-separated names of roles')
    role_description = models.TextField(default='', blank=True, help_text='Describe additional roles (markdown format')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        parents = list(p.name for p in self.parents)
        parents.reverse()
        parents.append(self.name)
        return ' :: '.join(parents)

    def clean(self):
        super().clean()
        available = [a.strip() for a in self.available_roles.split(',') if a.strip()]
        for role in ROLE_CHOICES.keys():
            if role not in available:
                available.append(role)
        self.available_roles = ','.join(available)

    def get_role_choices(self):
        choices = []
        for role in self.available_roles.split(','):
            choice = ROLE_CHOICES.get(role, role.capitalize())
            choices.append((role, choice))
        return choices

    @cached_property
    def recursive_members(self):
        members = set()
        for mem in CircleMember.objects.filter(circle=self).select_related('contact').order_by('role', 'pk'):
            mem.contact.verbose_role = mem.verbose_role
            members.add((mem.contact, mem.role))
        for circle in self.children:
            members.update(circle.recursive_members)
        return members

    @cached_property
    def children(self):
        return list(self.circle_set.all().prefetch_related('members'))

    @cached_property
    def member_list(self):
        return list(CircleMember.objects.filter(circle=self).select_related('contact').order_by('role', 'pk'))

    @cached_property
    def lead_list(self):
        return list(self.leads.all())

    @cached_property
    def leads(self):
        return Contact.objects.filter(circlemember__role__in=['int','ext'], circlemember__circle=self)

    @cached_property
    def coordinators(self):
        return CircleMember.objects.filter(circle=self, role__in=['int', 'ext']).order_by('role', 'pk')

    @property
    def external_coordinators(self):
        return self.coordinators.filter(role='ext')

    @property
    def internal_coordinators(self):
        return self.coordinators.filter(role='int')

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
        emails = set((m.email for m, role in self.recursive_members))
        return ','.join(emails)

    def add_member(self, email, name, contact=None, role='member'):
        contact = contact or get_contact(email, name=name)
        CircleMember.objects.get_or_create(circle=self, contact=contact, role=role)

    def remove_member(self, contact, role='member', who=None):
        """
        Removes the member and/or any requests for membership
        """
        CircleMember.objects.filter(circle=self, contact=contact, role=role).delete()
        MembershipRequest.objects.filter(circle=self, requestor=contact).update(confirmed_by=who)

    def request_membership(self, email='', name='', contact=None):
        contact = contact or get_contact(email, name=name)
        if not self.members.filter(pk=contact.id).exists():
            try:
                MembershipRequest.objects.get_or_create(circle=self, requestor=contact)
            except MultipleObjectsReturned:
                pass
            return contact
        else:
            return False

    def approve_membership(self, contact, who):
        for req in MembershipRequest.objects.filter(circle=self, requestor=contact):
            req.confirmed_by = who
            req.save()

    def can_manage(self, user):
        return user.has_perm('circles.change_circle') or self.leads.filter(pk=get_contact(email=user.email).id).exists()

    def is_member(self, user):
        email = user.email
        for member, role in self.recursive_members:
            if member.email == email:
                return True
        return False

    def is_pending(self, request):
        if request.user.is_authenticated:
            contact = get_contact(request.user.email)
        else:
            contact = None
        if contact:
            try:
                return MembershipRequest.objects.get(circle=self, requestor=contact).confirm_date is None
            except MembershipRequest.DoesNotExist:
                return False
        else:
            return str(self.id) in request.session.get('circle_requests', {})
        return False



class CircleMember(models.Model):
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    role = models.CharField(max_length=255)
    join_date = models.DateTimeField(auto_now_add=True)

    @property
    def verbose_role(self):
        return ROLE_CHOICES.get(self.role, self.role.capitalize())

    class Meta:
        unique_together = ('circle', 'contact', 'role')

    def __str__(self):
        return '{} {}'.format(self.circle, self.contact)

    def get_absolute_url(self):
        return self.circle.get_absolute_url()



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
            self.circle.add_member(self.requestor.email, str(self.requestor), contact=self.requestor, role='member')
        else:
            self.circle.remove_member(self.requestor, role='member')

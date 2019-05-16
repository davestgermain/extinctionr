from django.db.models.signals import m2m_changed, post_save

from django.dispatch import receiver

from .models import Circle, CircleMember, MembershipRequest
from . import comm


@receiver(post_save, sender=MembershipRequest)
def sent_pending_email(sender, instance, **kwargs):
    if not instance.confirmed_by:
        comm.notify_circle_membership(instance.circle, 'pending member', [instance.requestor_id])


@receiver(post_save, sender=CircleMember)
def send_join_email(sender, instance, **kwargs):
    comm.notify_circle_membership(instance.circle, instance.role, [instance.contact_id])

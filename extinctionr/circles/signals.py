from django.db.models.signals import m2m_changed, post_save

from django.dispatch import receiver

from .models import Circle, MembershipRequest
from . import comm


@receiver(post_save, sender=MembershipRequest)
def sent_pending_email(sender, instance, **kwargs):
    if not instance.confirmed_by:
        comm.notify_circle_membership(instance.circle, 'pending member', [instance.requestor_id])


def send_join_email(sender, instance, action, pk_set, **kwargs):
    circle = instance
    member_ids = pk_set
    if action == 'post_add' and member_ids:
        if sender == Circle.leads.through:
            msg_type = 'lead'
        else:
            msg_type = 'member'
        comm.notify_circle_membership(instance, msg_type, pk_set)

m2m_changed.connect(send_join_email, sender=Circle.members.through)
m2m_changed.connect(send_join_email, sender=Circle.leads.through)

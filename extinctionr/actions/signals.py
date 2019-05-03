from django.db.models.signals import post_save
from django.dispatch import receiver
from extinctionr.utils import base_url

from .models import Attendee


@receiver(post_save, sender=Attendee)
def send_commit_email(sender, instance, **kwargs):
    from .comm import notify_commitments
    if instance.promised or instance.mutual_commitment > 0 and not instance.notified:
        action_url = '%s%s' % (base_url(), instance.action.get_absolute_url())
        notify_commitments(instance.action, instance.mutual_commitment, action_url)

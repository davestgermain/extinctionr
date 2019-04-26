from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.sites.models import Site

from .models import Attendee


@receiver(post_save, sender=Attendee)
def send_commit_email(sender, instance, **kwargs):
    from .comm import notify_commitments
    if instance.promised or instance.mutual_commitment > 0 and not instance.notified:
        current_site = Site.objects.get_current()
        scheme = 'http' if settings.DEBUG else 'https'
        action_url = '%s://%s%s' % (scheme, current_site.domain, instance.action.get_absolute_url())
        notify_commitments(instance.action, instance.mutual_commitment, action_url)

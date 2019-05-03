from django.conf import settings
from django.core.mail import send_mass_mail, send_mail
from django.utils.timezone import now, localtime
from django.utils import dateformat
from extinctionr.utils import base_url

from .models import Contact


def notify_circle_membership(circle, msg_type, members):
    addresses = circle.get_notification_addresses()
    contacts = Contact.objects.filter(pk__in=members)
    context = {
        'contact': str(contacts[0]),
        'contact_email': contacts[0].email,
        'circle': str(circle),
        'circle_url': '%s%s' % (base_url(), circle.get_absolute_url()),
    }
    if msg_type == 'pending member':
        context['action'] = 'wants to join'
    else:
        context['action'] = 'joined'
    message = '''
{contact} <{contact_email}> {action} {circle}

{circle_url}#members
'''.format(**context)
    subject = '[XR] %s added to %s' % (msg_type, circle)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, addresses)

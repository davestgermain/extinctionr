from django.conf import settings
from django.core.mail import EmailMessage, send_mass_mail
from django.utils.timezone import now, localtime
from django.utils import dateformat

from .models import Action, Attendee


MESSAGE = '''
Hi {name},

You said you'd commit to attending "{action_name}" if at least {num} people also committed.
We've now got enough other folks to commit! We hope to see you there, on {action_date}.
More details here: {action_url}

Solidarity,
Extinction Rebellion Massachusetts

P.S. If you can't make it, please get in touch. We're all in this together.

'''


def notify_commitments(action, threshold, action_url):
    """
    Send notification email to all attendees who agreed to commit if at least 'threshold'
    number of others commit.
    Will not send notifications for actions which have already happened.
    Will not notify attendees twice.
    """
    if now() > action.when:
        return 0
    attendees = action.attendee_set.filter(promised__isnull=False, mutual_commitment=0) | action.attendee_set.filter(mutual_commitment__lte=threshold)
    if attendees.count() >= threshold:
        to_send = attendees.filter(notified=None, mutual_commitment__gt=0)
        subject = "[XR] We've got enough to commit to %s" % action.name
        messages = []
        modified = set()
        from_email = settings.DEFAULT_FROM_EMAIL
        when = dateformat.format(localtime(action.when), 'l, F jS @ g:iA')
        for attendee in to_send:
            if attendee in modified:
                continue
            full_name = '%s %s' % (attendee.contact.first_name, attendee.contact.last_name)
            msg = MESSAGE.format(
                name=full_name,
                action_name=action.name,
                action_date=when,
                action_url=action_url,
                num=attendee.mutual_commitment,)
            messages.append((subject, msg, from_email, [attendee.contact.email]))
            attendee.notified = now()
            if not attendee.promised:
                attendee.promised = now()
            modified.add(attendee)
        send_mass_mail(messages)
        for attendee in modified:
            attendee.save()
        return len(messages)


RSVP_MSG = '''
Hi {name},

Thank you for signing up for "{action_name}"! We're looking forward to seeing you at
the event on {action_date}.

See event details here: {action_url}

In Solidarity,
Extinction Rebellion Boston
'''


def confirm_rsvp(action, attendee, action_url, ics_data):
    """
    Send notification email to attendee when they register.
    Will not send notifications for actions which have already happened.
    Will not notify attendees twice.
    """
    if now() > action.when:
        return 0
    subject = "[XR] RSVP confirmation for %s" % action.name
    from_email = settings.DEFAULT_FROM_EMAIL
    when = dateformat.format(localtime(action.when), 'l, F jS @ g:iA')
    msg_body = RSVP_MSG.format(
        name=attendee.contact.first_name,
        action_name=action.name,
        action_date=when,
        action_url=action_url,
    )
    attendee.notified = now()
    if not attendee.promised:
        attendee.promised = now()    
    msg = EmailMessage(subject, msg_body, from_email, [attendee.contact.email])
    msg.attach(f'{action.slug}.ics', ics_data, 'text/calendar')
    msg.send()
    attendee.save()

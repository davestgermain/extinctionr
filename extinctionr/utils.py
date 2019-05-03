from contacts.models import Contact
from django.conf import settings
from django.contrib.sites.models import Site


def get_contact(email, name='', first_name='', last_name='', **kwargs):
    email = email.lower().strip()
    assert email
    try:
        user = Contact.objects.get(email=email)
    except Contact.DoesNotExist:
        if not (first_name and last_name):
            sname = name.split(' ', 1)
            if len(sname) == 2:
                first_name, last_name = sname
            else:
                first_name = sname[0]
                last_name = '?'
        user = Contact.objects.create(email=email, first_name=first_name, last_name=last_name, **kwargs)
    resave = False
    for k, v in kwargs.items():
        if v and getattr(user, k, None) is None:
            setattr(user, k, v)
            resave = True
    if resave:
        user.save()
    return user


def get_last_contact(request):
    last = request.session.get('last-contact', None)
    if last:
        return Contact.objects.get(pk=last)


def set_last_contact(request, contact):
    if contact:
        request.session['last-contact'] = contact.id


def base_url():
    current_site = Site.objects.get_current()
    scheme = 'http' if settings.DEBUG else 'https'
    return '%s://%s' % (scheme, current_site.domain)

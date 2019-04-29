from contacts.models import Contact

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
    return user

"""
For monkeypatching things in third party libraries
"""
from django.urls import reverse


def get_absolute_url(self):
    return reverse('common:view_user', kwargs={'pk': self.id})


def do_monkeypatch():
    from common.models import User
    # give users an absolute url
    User.get_absolute_url = get_absolute_url

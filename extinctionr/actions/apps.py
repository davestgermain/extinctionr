from django.apps import AppConfig
from django.urls import reverse


def get_absolute_url(self):
    return reverse('common:view_user', kwargs={'pk': self.id})


class ActionsConfig(AppConfig):
    name = 'extinctionr.actions'

    def ready(self):
        import extinctionr.actions.signals
        from common.models import User
        User.get_absolute_url = get_absolute_url


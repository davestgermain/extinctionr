from django.apps import AppConfig


class CircleConfig(AppConfig):
    name = 'extinctionr.circles'

    def ready(self):
        from . import signals

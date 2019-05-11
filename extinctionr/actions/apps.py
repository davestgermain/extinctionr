from django.apps import AppConfig


class ActionsConfig(AppConfig):
    name = 'extinctionr.actions'

    def ready(self):
        import extinctionr.actions.signals
        from extinctionr.monkeypatch import do_monkeypatch
        do_monkeypatch()

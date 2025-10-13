from django.apps import AppConfig


class NavModelsConfig(AppConfig):
    name = 'nav.models'
    verbose_name = 'NAV models'

    def ready(self):
        import nav.models.signals  # noqa

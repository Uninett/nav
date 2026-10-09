from django.apps import AppConfig
from .checks import default_secret_key_check  # noqa: F401 - needed for check to run


class NavDjangoConfig(AppConfig):
    name = 'nav.django'
    verbose_name = 'NAV Django'

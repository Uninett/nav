from django.core.checks import Warning, register

from nav.django.settings import SECRET_KEY


@register()
def default_secret_key_check(app_configs, **kwargs):
    errors = []
    if secret_key_is_default:
        errors.append(
            Warning(
                "The SECRET_KEY of this NAV installation is still the default value.",
                hint="Set a random SECRET_KEY in 'nav.conf' and restart NAV.",
                obj=SECRET_KEY,
                id="django.E001",
            )
        )
    return errors


def secret_key_is_default():
    return SECRET_KEY in ('Very bad default value!', 'YouShouldReallyChangeThis')

from django.core.management import call_command


def test_django_manage_check():
    """Runs Django's `check` management command to verify the Django project is
    correctly configured.
    """
    call_command('check')

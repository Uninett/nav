import os
from nav.django import settings
from nav.db import get_connection_parameters


def test_db_password_should_not_be_blank():
    params = get_connection_parameters('default')
    print("get_connection_parameters: {!r}".format(params))
    host, port, db, user, password = params
    assert password


def test_django_db_password_should_be_correct():
    """verifies that the configured Django database uses the same password as
    NAV reads from its config file.
    """
    params = get_connection_parameters('django')
    print("get_connection_parameters: {!r}".format(params))
    print("ENVIRONMENT:\n{!r}".format(os.environ))
    print("DATABASES:\n{!r}".format(settings.DATABASES))

    host, port, db, user, password = params
    assert settings.DATABASES['default']['PASSWORD'] == password

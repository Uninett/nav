from nav.ipdevpoll.db import django_debug_cleanup
from nav.models.manage import Netbox
from django.conf import settings
import pytest


@pytest.mark.skipif(
    not settings.DEBUG, reason="can only test when Django DEBUG is enabled"
)
def test_django_debug_cleanup_should_run_without_errors():
    from django.db import connection

    list(Netbox.objects.all())  # generate a query
    assert len(connection.queries) > 0, "no query was logged by Django"

    assert django_debug_cleanup() is None

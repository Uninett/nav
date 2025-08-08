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


def test_delete_stale_job_refresh_notifications_should_delete_stale_notifications(
    stale_refresh_event,
):
    from nav.ipdevpoll.db import delete_stale_job_refresh_notifications
    from nav.models.event import EventQueue

    assert EventQueue.objects.filter(target='ipdevpoll').count() > 0, (
        "no stale job refresh notifications found"
    )
    delete_stale_job_refresh_notifications()
    assert EventQueue.objects.filter(target='ipdevpoll').count() == 0, (
        "stale job refresh notifications still found"
    )


@pytest.fixture
def stale_refresh_event(localhost):
    from nav.event2 import EventFactory

    factory = EventFactory("devBrowse", "ipdevpoll", event_type="notification")
    event = factory.notify(netbox=localhost, subid="inventory")
    event.save()

    yield event

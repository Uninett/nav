from datetime import datetime, timedelta

from django.urls import reverse

from nav.web.navlets.roomstatus import RoomStatus
from nav.web.navlets.feedreader import FeedReaderNavlet
from nav.models.event import AlertHistory, AlertHistoryMessage
from nav.models.profiles import AccountNavlet
from nav.models.fields import INFINITY

import pytest


def test_roomstatus_should_not_fail_on_multiple_messages(alerthist_with_two_messages):
    widget = RoomStatus()
    result = widget.get_context_data_view({})
    print(result)
    assert 'results' in result
    assert len(result['results']) == 1

    problem = result['results'][0]
    assert problem['netbox_object'] == alerthist_with_two_messages.netbox


def test_feedreader_widget_should_get_nav_blog_posts():
    widget = FeedReaderNavlet()
    feed = widget._get_feed('http://blog.nav.uninett.no/rss', maxposts=0)
    print(repr(feed))
    assert len(feed) > 0


def test_get_navlet_should_return_200(client, admin_navlet):
    """Tests a GET request against each of the admin user's navlets"""
    url = reverse('get-user-navlet', kwargs={'navlet_id': admin_navlet.id})
    print(
        "Testing admin navlet instance of {!r} at {!r}".format(admin_navlet.navlet, url)
    )
    response = client.get(url)
    assert response.status_code == 200


#
# Fixtures
#


@pytest.fixture()
def alerthist_with_two_messages(localhost):
    alert = AlertHistory(
        source_id='ipdevpoll',
        netbox=localhost,
        start_time=datetime.now() - timedelta(hours=1),
        end_time=INFINITY,
        event_type_id='boxState',
        value=100,
        severity=3,
    )
    alert.save()
    msg1 = AlertHistoryMessage(
        alert_history=alert,
        state=AlertHistoryMessage.STATE_START,
        type='sms',
        language='en',
        message='Problem detected',
    )
    msg1.save()
    msg2 = AlertHistoryMessage(
        alert_history=alert,
        state=AlertHistoryMessage.STATE_END,
        type='sms',
        language='en',
        message='Problem resolved',
    )
    msg2.save()

    yield alert
    alert.delete()

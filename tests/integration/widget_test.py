from datetime import datetime, timedelta

from django.urls import reverse

from nav.web.navlets.roomstatus import RoomStatus
from nav.web.navlets.feedreader import FeedReaderNavlet
from nav.models.event import AlertHistory, AlertHistoryMessage
from nav.models.profiles import AccountDashboard, AccountNavlet
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


def test_get_pdu_navlet_in_edit_mode_should_return_200(client, admin_account):
    """Tests a GET request against the pdu navlet in edit mode"""
    dashboard = AccountDashboard.objects.create(
        account=admin_account, name="Test Dashboard"
    )
    pdu_navlet = AccountNavlet.objects.create(
        navlet="nav.web.navlets.pdu.PduWidget",
        account=admin_account,
        dashboard=dashboard,
    )
    url = reverse('get-user-navlet', kwargs={'navlet_id': pdu_navlet.id}) + "?mode=EDIT"
    print(
        "Testing admin navlet instance of {!r} at {!r}".format(pdu_navlet.navlet, url)
    )
    response = client.get(url)
    assert response.status_code == 200


def test_get_navlet_with_invalid_id_should_return_404(client):
    """Tests a GET request against a non-existing navlet id"""
    url = reverse('get-user-navlet', kwargs={'navlet_id': 999})
    response = client.get(url)
    assert response.status_code == 404


def test_given_navlet_belonging_to_other_account_when_shared_then_return_200(
    client, admin_account, non_admin_account
):
    """
    Tests a GET request against a navlet belonging to another account

    Should return 200 if `dashboard.is_shared == True`
    """
    dashboard = AccountDashboard.objects.create(
        account=non_admin_account, name="User Dashboard", is_shared=True
    )
    user_navlet = AccountNavlet.objects.create(
        navlet="nav.web.navlets.welcome.WelcomeNavlet",
        account=non_admin_account,
        dashboard=dashboard,
    )
    url = reverse('get-user-navlet', kwargs={'navlet_id': user_navlet.id})
    response = client.get(url)
    assert response.status_code == 200


def test_given_navlet_belonging_to_other_account_when_not_shared_then_return_403(
    client, admin_account, non_admin_account
):
    """
    Tests a GET request against a navlet belonging to another account

    Should return 403 unless `dashboard.is_shared == True`
    """
    dashboard = AccountDashboard.objects.create(
        account=non_admin_account, name="User Dashboard"
    )
    user_navlet = AccountNavlet.objects.create(
        navlet="nav.web.navlets.welcome.WelcomeNavlet",
        account=non_admin_account,
        dashboard=dashboard,
    )
    url = reverse('get-user-navlet', kwargs={'navlet_id': user_navlet.id})
    response = client.get(url)
    assert response.status_code == 403


def test_given_navlet_id_when_navlet_type_is_invalid_then_return_error_widget(
    client, admin_account
):
    """
    Tests a GET request against a navlet with an invalid navlet type

    Should return a navlet with title "Error"
    """

    dashboard = AccountDashboard.objects.create(
        account=admin_account, name="Test Dashboard"
    )
    invalid_navlet = AccountNavlet.objects.create(
        navlet="nav.web.navlets.invalid.InvalidNavlet",
        account=admin_account,
        dashboard=dashboard,
    )
    url = reverse('get-user-navlet', kwargs={'navlet_id': invalid_navlet.id})
    response = client.get(url)

    navlet = response.context['navlet']
    assert navlet.title == "Error"


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

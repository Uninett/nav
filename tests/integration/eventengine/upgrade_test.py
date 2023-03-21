"""Integration tests for the apparent proper processing of deviceNotice events"""

from mock import Mock

import pytest

from nav.eventengine.plugins.upgrade import UpgradeHandler
from nav.models.manage import Netbox, NetboxEntity
from nav.models.event import EventQueue as Event


def test_upgrade_handler_should_copy_old_and_new_version_to_alert_history_if_they_exist(
    netbox_having_sw_upgrade,
):
    fake_engine = Mock()
    fake_event = Event(
        source_id="ipdevpoll",
        target_id="eventEngine",
        event_type_id="deviceNotice",
        netbox=netbox_having_sw_upgrade,
        state=Event.STATE_STATELESS,
    )
    fake_event.varmap = {
        "old_version": "old version",
        "new_version": "new version",
        "alerttype": "deviceSwUpgrade",
    }
    fake_event.save()
    plugin = UpgradeHandler(fake_event, fake_engine)
    plugin.handle()

    alert = (
        netbox_having_sw_upgrade.alert_history_set.filter(event_type__id="deviceNotice")
        .filter(variables__isnull=False)
        .first()
    )
    assert alert, "no alert was posted on software upgrade"
    variables = alert.variables.all()
    assert variables.get(variable="old_version").value == "old version"
    assert variables.get(variable="new_version").value == "new version"


def test_upgrade_handler_should_not_fail_if_old_and_new_version_do_not_exist(
    netbox_having_sw_upgrade,
):
    fake_engine = Mock()
    fake_event = Event(
        source_id="ipdevpoll",
        target_id="eventEngine",
        event_type_id="deviceNotice",
        netbox=netbox_having_sw_upgrade,
        state=Event.STATE_STATELESS,
    )
    fake_event.varmap = {
        "alerttype": "deviceSwUpgrade",
    }
    fake_event.save()
    plugin = UpgradeHandler(fake_event, fake_engine)
    plugin.handle()

    alert = (
        netbox_having_sw_upgrade.alert_history_set.filter(event_type__id="deviceNotice")
        .filter(variables__isnull=False)
        .first()
    )
    assert alert, "no alert was posted on software upgrade"
    variables = alert.variables.all()
    assert variables.get(variable="old_version").value == "N/A"
    assert variables.get(variable="new_version").value == "N/A"


########################
#                      #
# fixtures and helpers #
#                      #
########################


@pytest.fixture()
def netbox_having_sw_upgrade():
    box = Netbox(
        ip="10.254.254.254",
        sysname="upgradehost.example.org",
        organization_id="myorg",
        room_id="myroom",
        category_id="SW",
    )
    box.save()
    entity = NetboxEntity(
        index=1,
        netbox=box,
        software_revision="even newer version",
    )
    entity.save()
    yield box
    print("teardown test device")
    box.delete()
    entity.delete()

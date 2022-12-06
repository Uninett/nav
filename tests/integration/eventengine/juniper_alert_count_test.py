"""Black-box integration tests for the apparent proper processing of
juniperYellowAlarmState and juniperRedAlarmState events
"""
try:
    from subprocess32 import STDOUT, check_output, TimeoutExpired, CalledProcessError
except ImportError:
    from subprocess import STDOUT, check_output, TimeoutExpired, CalledProcessError

import pytest

from nav.models.manage import Netbox, NetboxEntity
from nav.models.event import EventQueue as Event


class TestBlackBox:
    def test_eventengine_should_copy_alert_count_to_alert_history_on_yellow_start_event(
        self,
        netbox_having_new_alarm_count,
    ):
        count = 2
        post_fake_yellow_alarm_start_event(netbox_having_new_alarm_count, count)
        get_eventengine_output(6)
        alert = (
            netbox_having_new_alarm_count.get_unresolved_alerts(
                "juniperYellowAlarmState"
            )
            .filter(variables__isnull=False)
            .first()
        )
        assert alert, "no alert was posted on changed alarm count"
        variables = alert.variables.all()
        assert int(variables.get(variable="count").value) == count

    def test_eventengine_should_create_new_alert_history_entry_on_second_yellow_start_event_with_changed_count(
        self,
        netbox_having_new_alarm_count,
    ):
        old_count = 2
        new_count = 3
        post_fake_yellow_alarm_start_event(netbox_having_new_alarm_count, old_count)
        post_fake_yellow_alarm_start_event(netbox_having_new_alarm_count, new_count)
        get_eventengine_output(6)
        alerts = netbox_having_new_alarm_count.get_unresolved_alerts(
            "juniperYellowAlarmState"
        ).filter(variables__isnull=False)
        alert_count = alerts.count()
        assert (
            alert_count == 1
        ), "more or less than one unresolved alerts exist after changing alarm count"
        variables = alerts.first().variables.all()
        assert int(variables.get(variable="count").value) == new_count

    def test_eventengine_should_set_alert_history_entry_to_closed_on_yellow_end_event(
        self,
        netbox_having_new_alarm_count,
    ):
        post_fake_yellow_alarm_start_event(netbox_having_new_alarm_count)
        post_fake_yellow_alarm_end_event(netbox_having_new_alarm_count)
        get_eventengine_output(6)
        assert not netbox_having_new_alarm_count.get_unresolved_alerts(
            "juniperYellowAlarmState"
        ).exists(), "an unresolved alert exists after posting end event"

    def test_eventengine_should_copy_alert_count_to_alert_history_on_red_start_event(
        self,
        netbox_having_new_alarm_count,
    ):
        count = 2
        post_fake_red_alarm_start_event(netbox_having_new_alarm_count, count)
        get_eventengine_output(6)
        alert = (
            netbox_having_new_alarm_count.get_unresolved_alerts("juniperRedAlarmState")
            .filter(variables__isnull=False)
            .first()
        )
        assert alert, "no alert was posted on changed alarm count"
        variables = alert.variables.all()
        assert int(variables.get(variable="count").value) == count

    def test_eventengine_should_create_new_alert_history_entry_on_second_red_start_event_with_changed_count(
        self,
        netbox_having_new_alarm_count,
    ):
        old_count = 2
        new_count = 3
        post_fake_red_alarm_start_event(netbox_having_new_alarm_count, old_count)
        post_fake_red_alarm_start_event(netbox_having_new_alarm_count, new_count)
        get_eventengine_output(6)
        alerts = netbox_having_new_alarm_count.get_unresolved_alerts(
            "juniperRedAlarmState"
        ).filter(variables__isnull=False)
        alert_count = alerts.count()
        assert (
            alert_count == 1
        ), "more or less than one unresolved alerts exist after changing alarm count"
        variables = alerts.first().variables.all()
        assert int(variables.get(variable="count").value) == new_count

    def test_eventengine_should_set_alert_history_entry_to_closed_on_red_end_event(
        self,
        netbox_having_new_alarm_count,
    ):
        post_fake_red_alarm_start_event(netbox_having_new_alarm_count)
        post_fake_red_alarm_end_event(netbox_having_new_alarm_count)
        get_eventengine_output(6)
        assert not netbox_having_new_alarm_count.get_unresolved_alerts(
            "juniperRedAlarmState"
        ), "an unresolved alert exists after posting end event"


########################
#                      #
# fixtures and helpers #
#                      #
########################
def post_fake_yellow_alarm_start_event(netbox, count: int = 2):
    event = Event(
        source_id="ipdevpoll",
        target_id="eventEngine",
        event_type_id="juniperYellowAlarmState",
        netbox=netbox,
        state=Event.STATE_START,
    )
    event.varmap = {
        "count": count,
        "alerttype": "juniperYellowAlarmOn",
    }
    event.save()


def post_fake_yellow_alarm_end_event(netbox):
    event = Event(
        source_id="ipdevpoll",
        target_id="eventEngine",
        event_type_id="juniperYellowAlarmState",
        netbox=netbox,
        state=Event.STATE_END,
    )
    event.varmap = {
        "alerttype": "juniperYellowAlarmOff",
    }
    event.save()


def post_fake_red_alarm_start_event(netbox, count: int = 2):
    event = Event(
        source_id="ipdevpoll",
        target_id="eventEngine",
        event_type_id="juniperRedAlarmState",
        netbox=netbox,
        state=Event.STATE_START,
    )
    event.varmap = {
        "count": count,
        "alerttype": "juniperRedAlarmOn",
    }
    event.save()


def post_fake_red_alarm_end_event(netbox):
    event = Event(
        source_id="ipdevpoll",
        target_id="eventEngine",
        event_type_id="juniperRedAlarmState",
        netbox=netbox,
        state=Event.STATE_END,
    )
    event.varmap = {
        "alerttype": "juniperRedAlarmOff",
    }
    event.save()


def get_eventengine_output(timeout=10):
    """
    Runs eventengine in foreground mode, kills it after timeout seconds and
    returns the combined stdout+stderr output from the process.
    Also asserts that pping shouldn't unexpectedly exit with a zero exitcode.
    """
    cmd = ["eventengine", "-f"]
    try:
        output = check_output(cmd, stderr=STDOUT, timeout=timeout)
    except TimeoutExpired as error:
        # this is the normal case, since we need to kill eventengine after the timeout
        print(error.output.decode("utf-8"))
        return error.output.decode("utf-8")
    except CalledProcessError as error:
        print(error.output.decode("utf-8"))
        raise
    else:
        print(output)
        assert False, "eventengine exited with non-zero status"


@pytest.fixture()
def netbox_having_new_alarm_count():
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
        software_revision="new version",
    )
    entity.save()
    yield box
    print("teardown test device")
    box.delete()
    entity.delete()

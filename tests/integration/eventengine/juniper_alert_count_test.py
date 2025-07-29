"""Integration tests for the proper processing of juniperYellowAlarmState and
juniperRedAlarmState events
"""

import datetime
import logging
import pytest


from nav.eventengine import unresolved, get_eventengine_output
from nav.eventengine.engine import EventEngine
from nav.eventengine.plugins.juniperalertcount import JuniperAlertCountHandler
from nav.models.fields import INFINITY
from nav.models.manage import Netbox, NetboxEntity
from nav.models.event import AlertHistory, AlertType, EventQueue as Event

LOGGER = logging.getLogger(__name__)


class TestBlackBox:
    def test_eventengine_should_copy_alert_count_to_alert_history_on_yellow_start_event(  # noqa:E501
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

    def test_eventengine_should_create_new_alert_history_entry_on_second_yellow_start_event_with_changed_count(  # noqa:E501
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
        assert alert_count == 1, (
            "more or less than one unresolved alerts exist after changing alarm count"
        )
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

    def test_eventengine_should_create_new_alert_history_entry_on_second_red_start_event_with_changed_count(  # noqa:E501
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
        assert alert_count == 1, (
            "more or less than one unresolved alerts exist after changing alarm count"
        )
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


class TestStatelessEvent:
    def test_ignore_stateless_events(self, netbox_having_new_alarm_count, caplog):
        stateless_event = post_fake_stateless_event(netbox_having_new_alarm_count)
        eventengine = EventEngine()
        handler = JuniperAlertCountHandler(event=stateless_event, engine=eventengine)
        with caplog.at_level(logging.INFO):
            handler.handle()

        assert "Ignoring stateless juniperYellowAlarmState event" in caplog.text
        with pytest.raises(Event.DoesNotExist):
            stateless_event.refresh_from_db()
        assert getattr(handler, "event", None)


class TestHandleStart:
    def test_handle_start_ignores_irrelevant_alert_type(
        self, netbox_having_new_alarm_count, caplog
    ):
        start_event = post_fake_yellow_alarm_start_event(netbox_having_new_alarm_count)
        start_event.varmap = {
            "count": start_event.varmap["count"],
            "alerttype": "wrong_type",
        }
        start_event.save()
        eventengine = EventEngine()
        handler = JuniperAlertCountHandler(event=start_event, engine=eventengine)
        with caplog.at_level(logging.INFO):
            handler.handle()

        assert (
            "Ignoring juniperYellowAlarmState start event with alert type wrong_type"
            in caplog.text
        )
        with pytest.raises(Event.DoesNotExist):
            start_event.refresh_from_db()
        assert getattr(handler, "event", None)

    def test_handle_start_posts_alert_if_none_is_yet_posted(
        self,
        netbox_having_new_alarm_count,
    ):
        count = 2
        start_event = post_fake_yellow_alarm_start_event(
            netbox_having_new_alarm_count, count
        )
        eventengine = EventEngine()
        handler = JuniperAlertCountHandler(event=start_event, engine=eventengine)
        handler.handle()

        alert = (
            netbox_having_new_alarm_count.get_unresolved_alerts(
                "juniperYellowAlarmState"
            )
            .filter(variables__isnull=False)
            .first()
        )
        assert alert, "no alert was posted on start event"
        variables = alert.variables.all()
        assert int(variables.get(variable="count").value) == count

    def test_handle_start_resolves_existing_alert_with_different_count(
        self,
        netbox_having_new_alarm_count,
    ):
        start_event = post_fake_yellow_alarm_start_event(
            netbox_having_new_alarm_count, 3
        )
        alert = AlertHistory.objects.create(
            source_id="ipdevpoll",
            netbox=netbox_having_new_alarm_count,
            start_time=datetime.datetime.now(),
            end_time=INFINITY,
            event_type_id="juniperYellowAlarmState",
            alert_type=AlertType.objects.get(name="juniperYellowAlarmOn"),
            value=100,
        )
        alert.varmap = {"s": {"count": 3}}
        alert.save()
        unresolved.update()
        start_event.varmap.update({"count": 2})
        start_event.save()
        eventengine = EventEngine()
        handler = JuniperAlertCountHandler(event=start_event, engine=eventengine)
        handler.handle()

        alert.refresh_from_db()

        assert getattr(alert, "end_time", None) == start_event.time

    def test_handle_start_does_nothing_if_alert_exists_with_same_count(
        self, netbox_having_new_alarm_count, caplog
    ):
        start_event = post_fake_yellow_alarm_start_event(
            netbox_having_new_alarm_count, 3
        )
        alert = AlertHistory.objects.create(
            source_id="ipdevpoll",
            netbox=netbox_having_new_alarm_count,
            start_time=datetime.datetime.now(),
            end_time=INFINITY,
            event_type_id="juniperYellowAlarmState",
            alert_type=AlertType.objects.get(name="juniperYellowAlarmOn"),
            value=100,
        )
        alert.varmap = {"s": {"count": 3}}
        alert.save()
        unresolved.update()
        eventengine = EventEngine()
        handler = JuniperAlertCountHandler(event=start_event, engine=eventengine)
        with caplog.at_level(logging.INFO):
            handler.handle()

        assert "Ignoring duplicate juniperYellowAlarmState start event" in caplog.text
        with pytest.raises(Event.DoesNotExist):
            start_event.refresh_from_db()
        assert getattr(handler, "event", None)


class TestHandleEnd:
    def test_handle_end_ignores_irellevant_alert_type(
        self, netbox_having_new_alarm_count, caplog
    ):
        end_event = post_fake_yellow_alarm_end_event(netbox_having_new_alarm_count)
        end_event.varmap = {
            "alerttype": "wrong_type",
        }
        end_event.save()
        eventengine = EventEngine()
        handler = JuniperAlertCountHandler(event=end_event, engine=eventengine)
        with caplog.at_level(logging.INFO):
            handler.handle()

        assert (
            "Ignoring juniperYellowAlarmState end event with alert type wrong_type"
            in caplog.text
        )
        with pytest.raises(Event.DoesNotExist):
            end_event.refresh_from_db()
        assert getattr(handler, "event", None)

    def test_handle_end_resolves_start_alert(
        self,
        netbox_having_new_alarm_count,
    ):
        start_alert = AlertHistory.objects.create(
            source_id="ipdevpoll",
            netbox=netbox_having_new_alarm_count,
            start_time=datetime.datetime.now(),
            end_time=INFINITY,
            event_type_id="juniperYellowAlarmState",
            alert_type=AlertType.objects.get(name="juniperYellowAlarmOn"),
            value=100,
        )
        start_alert.varmap = {"s": {"count": 3}}
        start_alert.save()
        unresolved.update()
        end_event = post_fake_yellow_alarm_end_event(
            netbox_having_new_alarm_count,
        )
        eventengine = EventEngine()
        handler = JuniperAlertCountHandler(event=end_event, engine=eventengine)
        handler.handle()

        assert not netbox_having_new_alarm_count.get_unresolved_alerts(
            "juniperYellowAlarmState"
        ).exists(), "there are still unresolved alerts"

    def test_handle_end_does_nothing_if_no_start_alert_exists(
        self, netbox_having_new_alarm_count, caplog
    ):
        end_event = post_fake_yellow_alarm_end_event(netbox_having_new_alarm_count)
        eventengine = EventEngine()
        handler = JuniperAlertCountHandler(event=end_event, engine=eventengine)
        with caplog.at_level(logging.INFO):
            handler.handle()

        subject = end_event.get_subject()
        assert (
            f"no unresolved juniperYellowAlarmState for {subject}, ignoring end event"
            in caplog.text
        )
        with pytest.raises(Event.DoesNotExist):
            end_event.refresh_from_db()
        assert getattr(handler, "event", None)


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

    return event


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

    return event


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

    return event


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

    return event


def post_fake_stateless_event(netbox):
    event = Event(
        source_id="ipdevpoll",
        target_id="eventEngine",
        event_type_id="juniperYellowAlarmState",
        netbox=netbox,
        state=Event.STATE_STATELESS,
    )
    event.save()

    return event


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

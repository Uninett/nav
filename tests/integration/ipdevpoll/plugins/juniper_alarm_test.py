from mock import Mock

import pytest
import pytest_twisted

from nav.ipdevpoll.jobs import JobHandler
from nav.ipdevpoll.plugins import juniperalarm, plugin_registry
from nav.models.event import EventQueue
from nav.models.manage import NetboxInfo, NetboxType


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_start_events_should_be_posted_on_new_alarms(juniper_netbox, db):
    plugin_registry['juniperalarm'] = juniperalarm.JuniperChassisAlarm
    job = JobHandler('juniperalarm', juniper_netbox.pk, plugins=['juniperalarm'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()
    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 1,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 2,
    }
    start_events = EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        netbox_id=juniper_netbox.pk,
        state=EventQueue.STATE_START,
    )
    yellow_start_events = start_events.filter(event_type='juniperYellowAlarmState')
    red_start_events = start_events.filter(event_type='juniperRedAlarmState')
    yellow_start_events_count = yellow_start_events.count()
    red_start_events_count = red_start_events.count()

    yield job.run()

    assert agent.walk.called
    assert yellow_start_events.count() != 0
    assert yellow_start_events.count() != yellow_start_events_count
    assert red_start_events.count() != 0
    assert red_start_events.count() != red_start_events_count

    netbox_info = NetboxInfo.objects.filter(netbox__id=juniper_netbox.id).filter(
        key="juniperalarm"
    )
    yellow_saved_count = netbox_info.filter(variable="yellow_count").first().value
    red_saved_count = netbox_info.filter(variable="red_count").first().value
    assert yellow_saved_count.isdigit()
    assert red_saved_count.isdigit()
    assert int(yellow_saved_count) == 1
    assert int(red_saved_count) == 2


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_no_start_event_should_be_posted_on_new_zero_alarms(juniper_netbox, db):
    plugin_registry['juniperalarm'] = juniperalarm.JuniperChassisAlarm
    job = JobHandler('juniperalarm', juniper_netbox.pk, plugins=['juniperalarm'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()
    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 0,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 0,
    }
    start_events = EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        netbox_id=juniper_netbox.pk,
        state=EventQueue.STATE_START,
    )
    yellow_start_events = start_events.filter(event_type='juniperYellowAlarmState')
    red_start_events = start_events.filter(event_type='juniperRedAlarmState')
    yellow_start_events_count = yellow_start_events.count()
    red_start_events_count = red_start_events.count()

    yield job.run()

    assert agent.walk.called
    assert yellow_start_events.count() == yellow_start_events_count
    assert red_start_events.count() == red_start_events_count

    netbox_info = NetboxInfo.objects.filter(netbox__id=juniper_netbox.id).filter(
        key="juniperalarm"
    )
    yellow_saved_count = netbox_info.filter(variable="yellow_count").first().value
    red_saved_count = netbox_info.filter(variable="red_count").first().value
    assert yellow_saved_count.isdigit()
    assert red_saved_count.isdigit()
    assert int(yellow_saved_count) == 0
    assert int(red_saved_count) == 0


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_no_start_event_should_be_posted_on_old_zero_alarms(juniper_netbox, db):
    plugin_registry['juniperalarm'] = juniperalarm.JuniperChassisAlarm
    job = JobHandler('juniperalarm', juniper_netbox.pk, plugins=['juniperalarm'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()
    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 0,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 0,
    }

    yield job.run()

    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 0,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 0,
    }
    start_events = EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        netbox_id=juniper_netbox.pk,
        state=EventQueue.STATE_START,
    )
    yellow_start_events = start_events.filter(event_type='juniperYellowAlarmState')
    red_start_events = start_events.filter(event_type='juniperRedAlarmState')
    yellow_start_events_count = yellow_start_events.count()
    red_start_events_count = red_start_events.count()

    yield job.run()

    assert agent.walk.called
    assert yellow_start_events.count() == yellow_start_events_count
    assert red_start_events.count() == red_start_events_count

    netbox_info = NetboxInfo.objects.filter(netbox__id=juniper_netbox.id).filter(
        key="juniperalarm"
    )
    yellow_saved_count = netbox_info.filter(variable="yellow_count").first().value
    red_saved_count = netbox_info.filter(variable="red_count").first().value
    assert yellow_saved_count.isdigit()
    assert red_saved_count.isdigit()
    assert int(yellow_saved_count) == 0
    assert int(red_saved_count) == 0


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_no_start_event_should_be_posted_on_old_non_zero_alarms(juniper_netbox, db):
    plugin_registry['juniperalarm'] = juniperalarm.JuniperChassisAlarm
    job = JobHandler('juniperalarm', juniper_netbox.pk, plugins=['juniperalarm'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()
    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 1,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 2,
    }

    yield job.run()

    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 1,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 2,
    }
    start_events = EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        netbox_id=juniper_netbox.pk,
        state=EventQueue.STATE_START,
    )
    yellow_start_events = start_events.filter(event_type='juniperYellowAlarmState')
    red_start_events = start_events.filter(event_type='juniperRedAlarmState')
    yellow_start_events_count = yellow_start_events.count()
    red_start_events_count = red_start_events.count()

    yield job.run()

    assert agent.walk.called
    assert yellow_start_events.count() == yellow_start_events_count
    assert red_start_events.count() == red_start_events_count

    netbox_info = NetboxInfo.objects.filter(netbox__id=juniper_netbox.id).filter(
        key="juniperalarm"
    )
    yellow_saved_count = netbox_info.filter(variable="yellow_count").first().value
    red_saved_count = netbox_info.filter(variable="red_count").first().value
    assert yellow_saved_count.isdigit()
    assert red_saved_count.isdigit()
    assert int(yellow_saved_count) == 1
    assert int(red_saved_count) == 2


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_start_events_should_be_posted_on_changed_alarms(juniper_netbox, db):
    plugin_registry['juniperalarm'] = juniperalarm.JuniperChassisAlarm
    job = JobHandler('juniperalarm', juniper_netbox.pk, plugins=['juniperalarm'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()
    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 2,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 1,
    }

    yield job.run()

    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 3,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 2,
    }

    start_events = EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        netbox_id=juniper_netbox.pk,
        state=EventQueue.STATE_START,
    )
    yellow_start_events = start_events.filter(event_type='juniperYellowAlarmState')
    red_start_events = start_events.filter(event_type='juniperRedAlarmState')
    yellow_start_events_count = yellow_start_events.count()
    red_start_events_count = red_start_events.count()

    yield job.run()

    assert agent.walk.called
    assert yellow_start_events.count() != 0
    assert yellow_start_events.count() != yellow_start_events_count
    assert red_start_events.count() != 0
    assert red_start_events.count() != red_start_events_count

    netbox_info = NetboxInfo.objects.filter(netbox__id=juniper_netbox.id).filter(
        key="juniperalarm"
    )
    yellow_saved_count = netbox_info.filter(variable="yellow_count").first().value
    red_saved_count = netbox_info.filter(variable="red_count").first().value
    assert yellow_saved_count.isdigit()
    assert red_saved_count.isdigit()
    assert int(yellow_saved_count) == 3
    assert int(red_saved_count) == 2


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_start_events_should_be_posted_on_changed_from_zero_alarms(juniper_netbox, db):
    plugin_registry['juniperalarm'] = juniperalarm.JuniperChassisAlarm
    job = JobHandler('juniperalarm', juniper_netbox.pk, plugins=['juniperalarm'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()
    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 0,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 0,
    }

    yield job.run()

    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 3,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 2,
    }

    start_events = EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        netbox_id=juniper_netbox.pk,
        state=EventQueue.STATE_START,
    )
    yellow_start_events = start_events.filter(event_type='juniperYellowAlarmState')
    red_start_events = start_events.filter(event_type='juniperRedAlarmState')
    yellow_start_events_count = yellow_start_events.count()
    red_start_events_count = red_start_events.count()

    yield job.run()

    assert agent.walk.called
    assert yellow_start_events.count() != 0
    assert yellow_start_events.count() != yellow_start_events_count
    assert red_start_events.count() != 0
    assert red_start_events.count() != red_start_events_count

    netbox_info = NetboxInfo.objects.filter(netbox__id=juniper_netbox.id).filter(
        key="juniperalarm"
    )
    yellow_saved_count = netbox_info.filter(variable="yellow_count").first().value
    red_saved_count = netbox_info.filter(variable="red_count").first().value
    assert yellow_saved_count.isdigit()
    assert red_saved_count.isdigit()
    assert int(yellow_saved_count) == 3
    assert int(red_saved_count) == 2


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_end_events_should_be_posted_on_changed_to_zero_alarms(juniper_netbox, db):
    plugin_registry['juniperalarm'] = juniperalarm.JuniperChassisAlarm
    job = JobHandler('juniperalarm', juniper_netbox.pk, plugins=['juniperalarm'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()
    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 2,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 1,
    }

    yield job.run()

    agent.walk.return_value = {
        '.1.3.6.1.4.1.2636.3.4.2.2.2.0': 0,
        '.1.3.6.1.4.1.2636.3.4.2.3.2.0': 0,
    }

    end_events = EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        netbox_id=juniper_netbox.pk,
        state=EventQueue.STATE_END,
    )
    yellow_end_events = end_events.filter(event_type='juniperYellowAlarmState')
    red_end_events = end_events.filter(event_type='juniperRedAlarmState')
    yellow_end_events_count = yellow_end_events.count()
    red_end_events_count = red_end_events.count()

    yield job.run()

    assert agent.walk.called
    assert yellow_end_events.count() != 0
    assert yellow_end_events.count() != yellow_end_events_count
    assert red_end_events.count() != 0
    assert red_end_events.count() != red_end_events_count


@pytest.fixture()
def juniper_netbox(management_profile):
    from nav.models.manage import Netbox, NetboxProfile

    box = Netbox(
        ip='127.0.0.1',
        sysname='localhost.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SRV',
    )
    box.save()
    box.type = NetboxType.objects.get(sysobjectid="1.3.6.1.4.1.2636.1.1.1.2.6")
    box.save()
    NetboxProfile(netbox=box, profile=management_profile).save()
    yield box
    print("teardown test device")
    box.delete()

from mock import Mock
from datetime import datetime

import pytest
import pytest_twisted
from twisted.internet import defer

from nav.ipdevpoll.jobs import JobHandler, SuggestedReschedule
from nav.ipdevpoll.plugins import snmpcheck, plugin_registry
from nav.models.event import EventQueue, AlertHistory
from nav.models.fields import INFINITY


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_short_outage(localhost, db):
    plugin_registry['snmpcheck'] = snmpcheck.SnmpCheck
    job = JobHandler('snmpcheck', localhost.pk, plugins=['snmpcheck'])
    agent = Mock()
    job.agent = agent
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()
    agent.walk.return_value = defer.succeed(False)
    events = EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        event_type='snmpAgentState',
        netbox_id=localhost.pk,
    )
    start_events = events.filter(state=EventQueue.STATE_START)
    end_events = events.filter(state=EventQueue.STATE_END)
    start_events_first_count = start_events.count()
    end_events_first_count = end_events.count()

    with pytest.raises(SuggestedReschedule):
        yield job.run()

    assert agent.walk.called
    assert localhost.info_set.filter(
        key=snmpcheck.INFO_KEY_NAME, variable=snmpcheck.INFO_VARIABLE_NAME, value="down"
    ).exists()
    assert start_events.count() == start_events_first_count + 1

    with pytest.raises(SuggestedReschedule):
        yield job.run()
    assert localhost.info_set.filter(
        key=snmpcheck.INFO_KEY_NAME, variable=snmpcheck.INFO_VARIABLE_NAME, value="down"
    ).exists()
    assert start_events.count() == start_events_first_count + 2

    # now fake an AlertHist entry from event engine
    AlertHistory(
        source_id='ipdevpoll',
        event_type_id='snmpAgentState',
        netbox_id=localhost.pk,
        start_time=datetime.now(),
        end_time=INFINITY,
        value=100,
        severity=3,
    ).save()

    # and make sure snmpcheck tries to resolve it when the box is up
    agent.walk.return_value = defer.succeed(True)
    yield job.run()
    assert localhost.info_set.filter(
        key=snmpcheck.INFO_KEY_NAME, variable=snmpcheck.INFO_VARIABLE_NAME, value="up"
    ).exists()
    assert end_events.count() == end_events_first_count + 1

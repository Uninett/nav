from mock import Mock

import pytest
import pytest_twisted
from twisted.internet import defer

from nav.ipdevpoll.jobs import JobHandler, SuggestedReschedule
from nav.ipdevpoll.plugins import snmpcheck, plugin_registry
from nav.models.event import EventQueue


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
    with pytest.raises(SuggestedReschedule):
        yield job.run()
    assert agent.walk.called
    assert localhost.info_set.filter(
        key=snmpcheck.INFO_KEY_NAME,
        variable=snmpcheck.INFO_VARIABLE_NAME,
        value="down").exists()
    assert EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        event_type='snmpAgentState',
        netbox_id=localhost.pk,
        state=EventQueue.STATE_START).count() == 1
    yield job.run()
    assert localhost.info_set.filter(
        key=snmpcheck.INFO_KEY_NAME,
        variable=snmpcheck.INFO_VARIABLE_NAME,
        value="down").exists()
    assert EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        event_type='snmpAgentState',
        netbox_id=localhost.pk,
        state=EventQueue.STATE_START).count() == 1

    agent.walk.return_value = defer.succeed(True)
    yield job.run()
    assert localhost.info_set.filter(
        key=snmpcheck.INFO_KEY_NAME,
        variable=snmpcheck.INFO_VARIABLE_NAME,
        value="up").exists()
    assert EventQueue.objects.filter(
        source_id='ipdevpoll',
        target_id='eventEngine',
        event_type='snmpAgentState',
        netbox_id=localhost.pk,
        state=EventQueue.STATE_END).count() == 1

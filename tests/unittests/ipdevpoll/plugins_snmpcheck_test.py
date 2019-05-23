from mock import Mock

import pytest
import pytest_twisted
from twisted.internet import defer

from nav.ipdevpoll.jobs import SuggestedReschedule
from nav.ipdevpoll.plugins.snmpcheck import SnmpCheck


@pytest.fixture
def plugin():
    netbox = Mock()
    agent = Mock()
    containers = dict()
    return SnmpCheck(netbox, agent, containers)


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_stays_up(plugin):
    plugin._currently_down = Mock(return_value=False)
    plugin._currently_down.__name__ = '_currently_down'
    plugin.agent.walk.return_value = defer.succeed(True)
    plugin._mark_as_up = Mock()
    plugin._mark_as_down = Mock()
    yield plugin.handle()
    plugin._mark_as_up.assert_not_called()
    plugin._mark_as_down.assert_not_called()


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_stays_down(plugin):
    plugin._currently_down = Mock(return_value=True)
    plugin._currently_down.__name__ = '_currently_down'
    plugin.agent.walk.return_value = defer.succeed(False)
    plugin._mark_as_up = Mock()
    plugin._mark_as_down = Mock()
    yield plugin.handle()
    plugin._mark_as_up.assert_not_called()
    plugin._mark_as_down.assert_not_called()


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_going_down(plugin):
    plugin._currently_down = Mock(return_value=False)
    plugin._currently_down.__name__ = '_currently_down'
    plugin.agent.walk.return_value = defer.succeed(False)
    plugin._mark_as_up = Mock()
    plugin._mark_as_down = Mock()
    with pytest.raises(SuggestedReschedule):
        yield plugin.handle()
    plugin._mark_as_up.assert_not_called()
    plugin._mark_as_down.assert_called()


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_going_up(plugin):
    plugin._currently_down = Mock(return_value=True)
    plugin._currently_down.__name__ = '_currently_down'
    plugin.agent.walk.return_value = defer.succeed(True)
    plugin._mark_as_up = Mock()
    plugin._mark_as_down = Mock()
    yield plugin.handle()
    plugin._mark_as_down.assert_not_called()
    plugin._mark_as_up.assert_called()


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_timeout(plugin):
    plugin.agent.walk.return_value = defer.fail(defer.TimeoutError())
    res = yield plugin._do_check()
    assert res is False

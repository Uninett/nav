import pytest
import pytest_twisted

from nav.mibs import netswitch_mib


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_hp_get_memory_usage(snmp_agent_proxy):
    snmp_agent_proxy.community = 'hp-memory'
    snmp_agent_proxy.open()
    mib = netswitch_mib.NetswitchMib(snmp_agent_proxy)
    res = yield mib.get_memory_usage()
    assert res == {'global1': (5103056, 12299872), 'local1': (5103056, 12299872)}

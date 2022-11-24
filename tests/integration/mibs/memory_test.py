import pytest
import pytest_twisted

from nav.mibs import cisco_memory_pool_mib, juniper_mib, netswitch_mib


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_juniper_get_memory_usage(snmp_agent_proxy):
    snmp_agent_proxy.community = 'juniper-memory'
    snmp_agent_proxy.open()
    mib = juniper_mib.JuniperMib(snmp_agent_proxy)
    res = yield mib.get_memory_usage()

    assert set(res.keys()) == {
        '"FPC: EX2200-48T-4G @ 0/*/*"',
        '"FPC: EX2200-48T-4G @ 1/*/*"',
        '"FPC: EX2200-48T-4G @ 2/*/*"',
        '"Routing Engine 0"',
        '"Routing Engine 1"',
    }
    assert res['"FPC: EX2200-48T-4G @ 0/*/*"'] == (
        pytest.approx(257698037.76),
        pytest.approx(279172874.24),
    )
    assert res['"FPC: EX2200-48T-4G @ 1/*/*"'] == (
        pytest.approx(204010946.56),
        pytest.approx(332859965.44),
    )
    assert res['"FPC: EX2200-48T-4G @ 2/*/*"'] == (
        pytest.approx(182536110.08),
        pytest.approx(354334801.91999996),
    )
    assert res['"Routing Engine 0"'] == (
        pytest.approx(257698037.76),
        pytest.approx(279172874.24),
    )
    assert res['"Routing Engine 1"'] == (
        pytest.approx(204010946.56),
        pytest.approx(332859965.44),
    )


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_hp_get_memory_usage(snmp_agent_proxy):
    snmp_agent_proxy.community = 'hp-memory'
    snmp_agent_proxy.open()
    mib = netswitch_mib.NetswitchMib(snmp_agent_proxy)
    res = yield mib.get_memory_usage()
    assert res == {'global1': (5103056, 12299872), 'local1': (5103056, 12299872)}


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_cisco_get_memory_usage(snmp_agent_proxy):
    snmp_agent_proxy.community = 'cisco-memory'
    snmp_agent_proxy.open()
    mib = cisco_memory_pool_mib.CiscoMemoryPoolMib(snmp_agent_proxy)
    res = yield mib.get_memory_usage()
    assert res == {
        '"Driver text"': (40, 1048536),
        '"I/O"': (1664884, 2521228),
        '"Processor"': (10204640, 20055088),
    }

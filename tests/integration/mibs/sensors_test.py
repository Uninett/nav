from itertools import cycle
import subprocess

import pytest
import pytest_twisted

from nav.ipdevpoll.snmp import snmpprotocol, AgentProxy
from nav.ipdevpoll.snmp.common import SNMPParameters
from nav.mibs import comet, powernet_mib


ports = cycle([snmpprotocol.port() for i in range(50)])


@pytest.fixture(scope='session')
def snmpsim():
    proc = subprocess.Popen([
        '/usr/local/bin/snmpsimd.py',
        '--data-dir=/source/tests/integration/snmp_fixtures',
        '--log-level=error',
        '--agent-udpv4-endpoint=127.0.0.1:1024'], env={'HOME': '/source'})
    yield
    proc.kill()


@pytest.fixture()
def snmp_agent(snmpsim):
    port = next(ports)
    agent = AgentProxy(
        '127.0.0.1', 1024,
        community='placeholder',
        snmpVersion='v2c',
        protocol=port.protocol,
        snmp_parameters=SNMPParameters(timeout=0.5, max_repetitions=5,
                                       throttle_delay=0)
    )
    return agent


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_apc_pdu(snmp_agent):
    snmp_agent.community = 'apc-pdu'
    snmp_agent.open()
    mib = powernet_mib.PowerNetMib(snmp_agent)
    res = yield mib.get_all_sensors()
    assert res == [
        {
            'description': 'PDU Phase 1 ampere load',
            'internal_name': 'rPDULoadStatusLoad1',
            'mib': 'PowerNet-MIB',
            'name': 'PDU Phase 1',
            'oid': '.1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.1',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': 'amperes'
        },
        {
            'description': 'PDU Bank 1 ampere load',
            'internal_name': 'rPDULoadStatusLoad2',
            'mib': 'PowerNet-MIB',
            'name': 'PDU Bank 1',
            'oid': '.1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.2',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': 'amperes'
        },
        {
            'description': 'PDU Bank 2 ampere load',
            'internal_name': 'rPDULoadStatusLoad3',
            'mib': 'PowerNet-MIB',
            'name': 'PDU Bank 2',
            'oid': '.1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.3',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': 'amperes'
        },
    ]


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_P8652(snmp_agent):
    snmp_agent.community = 'P8652'
    snmp_agent.open()
    mib = comet.Comet(snmp_agent)
    res = yield mib.get_all_sensors()
    assert res == [
        {
            'description': u'Channel 1',
            'internal_name': 'channel1',
            'mib': 'P8652-MIB',
            'name': 'Channel 1',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.1.3.0',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': u'celsius'
        },
        {
            'description': u'Channel 2',
            'internal_name': 'channel2',
            'mib': 'P8652-MIB',
            'name': 'Channel 2',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.2.3.0',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': u'%RH'
        },
        {
            'description': u'Channel 3',
            'internal_name': 'channel3',
            'mib': 'P8652-MIB',
            'name': 'Channel 3',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.3.3.0',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': u''
        },
        {
            'description': u'Channel 4',
            'internal_name': 'channel4',
            'mib': 'P8652-MIB',
            'name': 'Channel 4',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.4.3.0',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': u''
        },
        {
            'description': u'vann-gulv-gang',
            'internal_name': 'bin1',
            'mib': 'P8652-MIB',
            'name': 'BIN 1',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.6.3.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean'
        },
        {
            'description': u'vann-gulv-gang alarm',
            'internal_name': 'bin1Alarm',
            'mib': 'P8652-MIB',
            'name': 'BIN 1 Alarm',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.6.5.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean'
        },
        {
            'description': u'vann-gulv-A',
            'internal_name': 'bin2',
            'mib': 'P8652-MIB',
            'name': 'BIN 2',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.7.3.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean'
        },
        {
            'description': u'vann-gulv-A alarm',
            'internal_name': 'bin2Alarm',
            'mib': 'P8652-MIB',
            'name': 'BIN 2 Alarm',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.7.5.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean'
        },
        {
            'description': u'vann-lagerrom',
            'internal_name': 'bin3',
            'mib': 'P8652-MIB',
            'name': 'BIN 3',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.8.3.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean'
        },
        {
            'description': u'vann-lagerrom alarm',
            'internal_name': 'bin3Alarm',
            'mib': 'P8652-MIB',
            'name': 'BIN 3 Alarm',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.8.5.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean'
        },
    ]

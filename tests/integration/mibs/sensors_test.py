import pytest
import pytest_twisted

from nav.mibs import comet, pdu2_mib, powernet_mib


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_apc_pdu(snmp_agent_proxy):
    snmp_agent_proxy.community = 'apc-pdu'
    snmp_agent_proxy.open()
    mib = powernet_mib.PowerNetMib(snmp_agent_proxy)
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
            'unit_of_measurement': 'amperes',
        },
        {
            'description': 'PDU Bank 1 ampere load',
            'internal_name': 'rPDULoadStatusLoad2',
            'mib': 'PowerNet-MIB',
            'name': 'PDU Bank 1',
            'oid': '.1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.2',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': 'amperes',
        },
        {
            'description': 'PDU Bank 2 ampere load',
            'internal_name': 'rPDULoadStatusLoad3',
            'mib': 'PowerNet-MIB',
            'name': 'PDU Bank 2',
            'oid': '.1.3.6.1.4.1.318.1.1.12.2.3.1.1.2.3',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': 'amperes',
        },
    ]


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_P8652(snmp_agent_proxy):
    snmp_agent_proxy.community = 'P8652'
    snmp_agent_proxy.open()
    mib = comet.Comet(snmp_agent_proxy)
    res = yield mib.get_all_sensors()
    assert res == [
        {
            'description': 'Channel 1',
            'internal_name': 'channel1',
            'mib': 'P8652-MIB',
            'name': 'Channel 1',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.1.3.0',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': 'celsius',
        },
        {
            'description': 'Channel 2',
            'internal_name': 'channel2',
            'mib': 'P8652-MIB',
            'name': 'Channel 2',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.2.3.0',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': '%RH',
        },
        {
            'description': 'Channel 3',
            'internal_name': 'channel3',
            'mib': 'P8652-MIB',
            'name': 'Channel 3',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.3.3.0',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': '',
        },
        {
            'description': 'Channel 4',
            'internal_name': 'channel4',
            'mib': 'P8652-MIB',
            'name': 'Channel 4',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.4.3.0',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': '',
        },
        {
            'description': 'vann-gulv-gang',
            'internal_name': 'bin1',
            'mib': 'P8652-MIB',
            'name': 'BIN 1',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.6.3.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean',
        },
        {
            'description': 'vann-gulv-gang alarm',
            'internal_name': 'bin1Alarm',
            'mib': 'P8652-MIB',
            'name': 'BIN 1 Alarm',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.6.5.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean',
            'on_message': 'vann-gulv-gang alarm triggered',
            'off_message': 'vann-gulv-gang alarm not triggered',
            'on_state': 1,
        },
        {
            'description': 'vann-gulv-A',
            'internal_name': 'bin2',
            'mib': 'P8652-MIB',
            'name': 'BIN 2',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.7.3.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean',
        },
        {
            'description': 'vann-gulv-A alarm',
            'internal_name': 'bin2Alarm',
            'mib': 'P8652-MIB',
            'name': 'BIN 2 Alarm',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.7.5.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean',
            'on_message': 'vann-gulv-A alarm triggered',
            'off_message': 'vann-gulv-A alarm not triggered',
            'on_state': 1,
        },
        {
            'description': 'vann-lagerrom',
            'internal_name': 'bin3',
            'mib': 'P8652-MIB',
            'name': 'BIN 3',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.8.3.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean',
        },
        {
            'description': 'vann-lagerrom alarm',
            'internal_name': 'bin3Alarm',
            'mib': 'P8652-MIB',
            'name': 'BIN 3 Alarm',
            'oid': '.1.3.6.1.4.1.22626.1.5.2.8.5.0',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'boolean',
            'on_message': 'vann-lagerrom alarm triggered',
            'off_message': 'vann-lagerrom alarm not triggered',
            'on_state': 1,
        },
    ]


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_raritan_pdu(snmp_agent_proxy):
    snmp_agent_proxy.community = 'raritan'
    snmp_agent_proxy.open()
    mib = pdu2_mib.PDU2Mib(snmp_agent_proxy)
    res = yield mib.get_all_sensors()
    res = sorted(res, key=lambda x: x['description'])
    assert res == [
        {
            'description': 'pdu 1 inlet I1 activeEnergy',
            'internal_name': 'pdu1_I1_activeEnergy',
            'maximum': None,
            'mib': 'PDU2-MIB',
            'minimum': 0.0,
            'name': 'pdu 1 inlet I1 activeEnergy',
            'oid': '.1.3.6.1.4.1.13742.6.5.2.3.1.4.1.1.8',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'watthours',
        },
        {
            'description': 'pdu 1 inlet I1 activePower',
            'internal_name': 'pdu1_I1_activePower',
            'maximum': 10000.0,
            'mib': 'PDU2-MIB',
            'minimum': 0.0,
            'name': 'pdu 1 inlet I1 activePower',
            'oid': '.1.3.6.1.4.1.13742.6.5.2.3.1.4.1.1.5',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'watts',
        },
        {
            'description': 'pdu 1 inlet I1 apparentPower',
            'internal_name': 'pdu1_I1_apparentPower',
            'maximum': 10000.0,
            'mib': 'PDU2-MIB',
            'minimum': 0.0,
            'name': 'pdu 1 inlet I1 apparentPower',
            'oid': '.1.3.6.1.4.1.13742.6.5.2.3.1.4.1.1.6',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'voltsamperes',
        },
        {
            'description': 'pdu 1 inlet I1 powerFactor',
            'internal_name': 'pdu1_I1_powerFactor',
            'maximum': 1.0,
            'mib': 'PDU2-MIB',
            'minimum': 0.0,
            'name': 'pdu 1 inlet I1 powerFactor',
            'oid': '.1.3.6.1.4.1.13742.6.5.2.3.1.4.1.1.7',
            'precision': 2,
            'scale': None,
            'unit_of_measurement': 'unknown',
        },
        {
            'description': 'pdu 1 inlet I1 rmsCurrent',
            'internal_name': 'pdu1_I1_rmsCurrent',
            'maximum': 32.0,
            'mib': 'PDU2-MIB',
            'minimum': 0.0,
            'name': 'pdu 1 inlet I1 rmsCurrent',
            'oid': '.1.3.6.1.4.1.13742.6.5.2.3.1.4.1.1.1',
            'precision': 1,
            'scale': None,
            'unit_of_measurement': 'amperes',
        },
        {
            'description': 'pdu 1 inlet I1 rmsVoltage',
            'internal_name': 'pdu1_I1_rmsVoltage',
            'maximum': 264.0,
            'mib': 'PDU2-MIB',
            'minimum': 0.0,
            'name': 'pdu 1 inlet I1 rmsVoltage',
            'oid': '.1.3.6.1.4.1.13742.6.5.2.3.1.4.1.1.4',
            'precision': 0,
            'scale': None,
            'unit_of_measurement': 'voltsAC',
        },
    ]

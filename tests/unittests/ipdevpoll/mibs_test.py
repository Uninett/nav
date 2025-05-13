#
# Copyright (C) 2008, 2009, 2011, 2012, 2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import datetime
from IPy import IP

from twisted.internet import defer
from twisted.python import failure

from mock import Mock
import pytest

from nav.ipdevpoll.shadows import PowerSupplyOrFan, Device
from nav.mibs.cisco_hsrp_mib import CiscoHSRPMib
from nav.models.manage import NetboxEntity
from nav.oids import OID
from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib
from nav.mibs.entity_mib import (
    EntityMib,
    parse_dateandtime_tc,
    _entity_to_powersupply_or_fan,
)
from nav.mibs.snmpv2_mib import Snmpv2Mib
from nav.mibs import itw_mib, itw_mibv3, itw_mibv4


class TestIpMib(object):
    def test_ipv4_syntax_with_length_should_be_parsed_correctly(self):
        ip_tuple = (1, 4, 192, 0, 2, 1)
        expected = IP('192.0.2.1')
        ip = IpMib.inetaddress_to_ip(ip_tuple)
        assert ip == expected

    def test_invalid_ipv4_syntax_should_raise_error(self):
        ip_tuple = (1, 4, 300, 300, 300, 300)
        with pytest.raises(ValueError):
            IpMib.inetaddress_to_ip(ip_tuple)

    def test_too_short_ipv4_address_should_raise_exception(self):
        ip_tuple = (1, 4, 1, 2)
        with pytest.raises(IndexToIpException):
            IpMib.inetaddress_to_ip(ip_tuple)

    def test_ipv4_syntax_not_annotated_with_size_should_parse_ok(self):
        ip_tuple = (1, 192, 0, 2, 1)
        expected = IP('192.0.2.1')
        ip = IpMib.inetaddress_to_ip(ip_tuple)
        assert ip == expected

    def test_too_long_ipv6_address_should_raise_exception(self):
        ip_tuple = (2, 16, 32, 1, 13, 184, 18, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
        with pytest.raises(IndexToIpException):
            IpMib.inetaddress_to_ip(ip_tuple)

    def test_ipv6_syntax_with_length_should_be_parsed_correctly(self):
        ip_tuple = (2, 16, 32, 1, 13, 184, 18, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
        expected = IP('2001:db8:1234::1')
        ip = IpMib.inetaddress_to_ip(ip_tuple)
        assert ip == expected

    _ipAddressPrefixEntry = (1, 3, 6, 1, 2, 1, 4, 32, 1)

    def test_ipv4_prefix_rowpointer_should_be_parsed_correctly(self):
        rowpointer = self._ipAddressPrefixEntry + (
            5,
            439541760,
            1,
            4,
            192,
            168,
            70,
            0,
            24,
        )
        expected = IP('192.168.70/24')
        prefix = IpMib.prefix_index_to_ip(rowpointer)
        assert prefix == expected

    def test_ipv6_prefix_rowpointer_should_be_parsed_correctly(self):
        rowpointer = self._ipAddressPrefixEntry + (
            5,
            11,
            2,
            16,
            32,
            1,
            7,
            0,
            0,
            0,
            5,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            64,
        )
        expected = IP('2001:700:0:500::/64')
        prefix = IpMib.prefix_index_to_ip(rowpointer)
        assert prefix == expected

    def test_nxos_ipv4_prefix_rowpointer_should_be_parsed_correctly(self):
        rowpointer = self._ipAddressPrefixEntry + (439541760, 1, 4, 192, 168, 70, 0, 24)
        expected = IP('192.168.70/24')
        prefix = IpMib.prefix_index_to_ip(rowpointer)
        assert prefix == expected

    def test_nxos_ipv6_prefix_rowpointer_should_be_parsed_correctly(self):
        rowpointer = self._ipAddressPrefixEntry + (
            11,
            2,
            16,
            32,
            1,
            7,
            0,
            0,
            0,
            5,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            64,
        )
        expected = IP('2001:700:0:500::/64')
        prefix = IpMib.prefix_index_to_ip(rowpointer)
        assert prefix == expected


class TestIpv6Mib(object):
    def test_ipv6mib_index(self):
        ip_tuple = (32, 1, 13, 184, 18, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
        expected = IP('2001:db8:1234::1')
        ip = Ipv6Mib.ipv6address_to_ip(ip_tuple)
        assert ip == expected


class TestEntityMib(object):
    def test_empty_logical_type_should_not_raise(self):
        mib = EntityMib(Mock('AgentProxy'))

        def mock_retrieve(columns):
            return defer.succeed(
                {
                    1: {
                        'entLogicalDescr': None,
                        'entLogicalType': None,
                        'entLogicalCommunity': None,
                    }
                }
            )

        mib.retrieve_columns = mock_retrieve
        df = mib.retrieve_alternate_bridge_mibs()
        assert df.called
        if isinstance(df.result, failure.Failure):
            df.result.raiseException()

    def test_entity_to_powersupply_or_fan(self):
        entity = {
            "entPhysicalName": "PSU 1",
            "entPhysicalModelName": "ABCDEF 720",
            "entPhysicalDescr": "Next-gen PSU Power fidelity foobar",
            "entPhysicalClass": NetboxEntity.CLASS_POWERSUPPLY,
            "entPhysicalSerialNum": "123ABC",
            0: OID('.1'),
        }
        unit = _entity_to_powersupply_or_fan(entity)
        assert isinstance(unit, PowerSupplyOrFan)
        assert isinstance(unit.device, Device)

    @pytest.mark.parametrize(
        "func,expected_count", [("get_power_supplies", 2), ("get_fans", 1)]
    )
    def test_get_power_supplies_or_fans_should_return_correct_number_of_units(
        self, entity_physical_table, func, expected_count
    ):
        """Tests that the correct number of fans or psus are filtered from an
        entPhysicalTable result.

        """
        result = self._get_units(func, entity_physical_table)
        assert len(result) == expected_count

    @pytest.mark.parametrize("func", ["get_power_supplies", "get_fans"])
    def test_get_power_supplies_or_fans_should_return_lists_of_correct_type(
        self, entity_physical_table, func
    ):
        result = self._get_units(func, entity_physical_table)
        assert result
        assert all(isinstance(unit, PowerSupplyOrFan) for unit in result)

    @staticmethod
    def _get_units(func, entity_physical_table):
        mib = EntityMib(Mock("AgentProxy"))

        def mock_retrieve(columns):
            return defer.succeed(entity_physical_table)

        mib.retrieve_columns = mock_retrieve
        df = getattr(mib, func)()
        assert df.called
        if isinstance(df.result, failure.Failure):
            df.result.raiseException()
        return df.result


class TestSnmpv2Mib(object):
    def test_simple_uptime_deviation_should_be_correct(self):
        first_uptime = (1338372778.0, 10000)
        second_uptime = (1338372900.0, 22200)
        dev = Snmpv2Mib.get_uptime_deviation(first_uptime, second_uptime)
        assert abs(dev) < 0.5, "deviation is higher than 0.5: %r" % dev

    def test_wrapped_uptime_deviation_should_be_correct(self):
        first_uptime = (1338372778.0, 4294967196)
        second_uptime = (1338372900.0, 12100)
        dev = Snmpv2Mib.get_uptime_deviation(first_uptime, second_uptime)
        assert abs(dev) < 0.5, "deviation is higher than 0.5: %r" % dev

    def test_none_uptime_should_not_crash(self):
        uptime1 = (0, None)
        uptime2 = (10, 10)
        dev = Snmpv2Mib.get_uptime_deviation(uptime1, uptime2)
        assert dev is None


class TestCiscoHSRPMib(object):
    def test_virtual_address_map(self):
        class MockedMib(CiscoHSRPMib):
            def retrieve_column(self, column):
                return defer.succeed(
                    {
                        OID('.153.1'): '10.0.1.1',
                        OID('.155.1'): '10.0.42.1',
                    }
                )

        mib = MockedMib(None)
        df = mib.get_virtual_addresses()
        assert df.called
        assert (IP('10.0.1.1'), 153) in df.result.items()
        assert (IP('10.0.42.1'), 155) in df.result.items()


def test_short_dateandtime_parses_properly():
    parsed = parse_dateandtime_tc(b'\xdf\x07\x05\x0e\x0c\x1e*\x05')
    assert parsed == datetime.datetime(2015, 5, 14, 12, 30, 42, 500000)


def test_long_dateandtime_parses_properly():
    parsed = parse_dateandtime_tc(b'\xdf\x07\x05\x0e\x0c\x1e*\x05+\x02\x00')
    assert parsed == datetime.datetime(2015, 5, 14, 12, 30, 42, 500000)


def test_zero_dateandtime_parses_properly():
    parsed = parse_dateandtime_tc(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    assert parsed is None


def test_non_bytes_dateandtime_should_not_be_parsed():
    parsed = parse_dateandtime_tc('\xdf\x07\x05\x0e\x0c\x1e*\x05+\x02\x00')
    assert parsed is None


def test_crazy_dateandtime_should_not_crash():
    assert parse_dateandtime_tc(b"FOOBAR") is None


def is_col_of(mib, col, table):
    return mib['nodes'][table]['oid'].is_a_prefix_of(mib['nodes'][col]['oid'])


@pytest.mark.parametrize(
    'cls',
    [itw_mib.ItWatchDogsMib, itw_mibv3.ItWatchDogsMibV3, itw_mibv4.ItWatchDogsMibV4],
)
def test_itw_tables(cls):
    mib = cls.mib
    for table, groups in cls.TABLES.items():
        for group in groups:
            cols = ['serial', 'name']
            if 'avail' in group:
                cols.append('avail')
            for col in cols:
                assert group[col] in mib['nodes'], group[col]
                assert is_col_of(mib, group[col], table)
            for sensor in group['sensors']:
                assert sensor in mib['nodes'], sensor
                assert is_col_of(mib, sensor, table)


@pytest.fixture
def entity_physical_table(scope="session"):
    """Returns a sample entPhysicalTable response"""
    return {
        OID(".1"): {
            0: OID(".1"),
            "entPhysicalDescr": "Chassis",
            "entPhysicalContainedIn": 0,
            "entPhysicalClass": NetboxEntity.CLASS_CHASSIS,
            "entPhysicalParentRelPos": 0,
            "entPhysicalName": "My Chassis",
            "entPhysicalHardwareRev": None,
            "entPhysicalFirmwareRev": None,
            "entPhysicalSoftwareRev": None,
            "entPhysicalSerialNum": None,
            "entPhysicalModelName": None,
            "entPhysicalIsFRU": 0,
        },
        OID(".2"): {
            0: OID(".2"),
            "entPhysicalDescr": "A power supply",
            "entPhysicalContainedIn": 1,
            "entPhysicalClass": NetboxEntity.CLASS_POWERSUPPLY,
            "entPhysicalParentRelPos": 0,
            "entPhysicalName": "PSU 1",
            "entPhysicalHardwareRev": None,
            "entPhysicalFirmwareRev": None,
            "entPhysicalSoftwareRev": None,
            "entPhysicalSerialNum": None,
            "entPhysicalModelName": None,
            "entPhysicalIsFRU": 1,
        },
        OID(".3"): {
            0: OID(".3"),
            "entPhysicalDescr": "Another power supply",
            "entPhysicalContainedIn": 1,
            "entPhysicalClass": NetboxEntity.CLASS_POWERSUPPLY,
            "entPhysicalParentRelPos": 1,
            "entPhysicalName": "PSU 2",
            "entPhysicalHardwareRev": None,
            "entPhysicalFirmwareRev": None,
            "entPhysicalSoftwareRev": None,
            "entPhysicalSerialNum": None,
            "entPhysicalModelName": None,
            "entPhysicalIsFRU": 1,
        },
        OID(".4"): {
            0: OID(".4"),
            "entPhysicalDescr": "A fan",
            "entPhysicalContainedIn": 1,
            "entPhysicalClass": NetboxEntity.CLASS_FAN,
            "entPhysicalParentRelPos": 0,
            "entPhysicalName": "FAN 1",
            "entPhysicalHardwareRev": None,
            "entPhysicalFirmwareRev": None,
            "entPhysicalSoftwareRev": None,
            "entPhysicalSerialNum": None,
            "entPhysicalModelName": None,
            "entPhysicalIsFRU": 1,
        },
    }

# ruff: noqa: E501

import datetime
import pytest
from mock import Mock
import random
import logging

logging.raiseExceptions = False

from nav import logengine

now = datetime.datetime.now()


@pytest.fixture
def loglines():
    return """
Oct 28 13:15:06 10.0.42.103 1030: Oct 28 13:15:05.310 CEST: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet1/0/29, changed state to up
Oct 28 13:15:21 10.0.42.103 1031: Oct 28 13:15:20.191 CEST: %EC-5-COMPATIBLE: Gi1/0/30 is compatible with port-channel members
Oct 28 13:15:21 10.0.42.103 1032: Oct 28 13:15:21.181 CEST: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet1/0/29, changed state to down
Oct 28 13:15:23 10.0.42.103 1033: Oct 28 13:15:22.196 CEST: %LINK-3-UPDOWN: Interface GigabitEthernet1/0/29, changed state to down
Oct 28 13:15:27 10.0.42.103 1034: Oct 28 13:15:26.390 CEST: %LINK-3-UPDOWN: Interface GigabitEthernet1/0/29, changed state to up
Oct 28 13:15:28 10.0.80.11 877630: Oct 28 13:15:27.383 CEST: %SEC-6-IPACCESSLOGP: list hpc-v2 denied udp 87.202.31.111(59646) (TenGigabitEthernet3/3 0022.bd37.c800) -> 128.39.62.195(45134), 1 packet
Oct 28 13:15:28 10.0.42.103 1035: Oct 28 13:15:27.388 CEST: %EC-5-CANNOT_BUNDLE2: Gi1/0/29 is not compatible with Gi1/0/30 and will be suspended (speed of Gi1/0/29 is 1000M, Gi1/0/30 is 100M)
Oct 28 13:15:40 10.0.42.103 1036: Oct 28 13:15:39.769 CEST: %EC-5-COMPATIBLE: Gi1/0/29 is compatible with port-channel members
Oct 28 13:15:42 10.0.42.103 1037: Oct 28 13:15:41.774 CEST: %LINK-3-UPDOWN: Interface GigabitEthernet1/0/30, changed state to down
Oct 28 13:15:44 10.0.42.103 1038: Oct 28 13:15:43.468 CEST: %SPANTREE-5-TOPOTRAP: Topology Change Trap for vlan 1
Oct 28 13:15:44 10.0.42.103 1039: Oct 28 13:15:44.382 CEST: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet1/0/29, changed state to up
Oct 28 13:15:46 10.0.42.103 1040: Oct 28 13:15:45.372 CEST: %LINK-3-UPDOWN: Interface Port-channel10, changed state to up
Oct 28 13:15:46 10.0.42.103 1041: Oct 28 13:15:46.379 CEST: %LINEPROTO-5-UPDOWN: Line protocol on Interface Port-channel10, changed state to up
Oct 28 13:15:52 10.0.42.103 1042: Oct 28 13:15:51.915 CEST: %LINK-3-UPDOWN: Interface GigabitEthernet1/0/30, changed state to up
Oct 28 13:15:52 10.0.128.13 71781: *Oct 28 2010 12:08:49 CET: %MV64340_ETHERNET-5-LATECOLLISION: GigabitEthernet0/1, late collision error
Oct 28 13:15:58 10.0.42.103 1043: Oct 28 13:15:57.560 CEST: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet1/0/30, changed state to up
""".strip().split("\n")


def test_parse_without_exceptions(loglines):
    for line in loglines:
        msg = logengine.create_message(line)
        assert msg, "unparseable: %s" % line
        assert msg.facility is not None, "Message has no facility: {0!r}\n{1!r}".format(
            line, vars(msg)
        )


def test_insert(loglines):
    for line in loglines:
        database = Mock('cursor')
        database.fetchone = lambda: [random.randint(1, 10000)]

        def execute(sql, params=()):
            return sql % params

        database.execute = execute
        message = logengine.create_message(line)
        assert message, "unparseable: %s" % line
        logengine.insert_message(message, database, {}, {}, {}, {}, {}, {})


def test_swallow_generic_exceptions():
    @logengine.swallow_all_but_db_exceptions
    def raiser():
        raise Exception("This is an ex-parrot")

    raiser()


def test_raise_db_exception():
    from nav.db import driver

    @logengine.swallow_all_but_db_exceptions
    def raiser():
        raise driver.Error("This is an ex-database")

    with pytest.raises(driver.Error):
        raiser()


def test_non_failing_function_should_run_fine():
    @logengine.swallow_all_but_db_exceptions
    def nonraiser(input):
        return input

    value = 'foo'
    assert nonraiser(value) == value


class TestParsing(object):
    message = "Oct 28 13:15:58 10.0.42.103 1043: Oct 28 13:15:57.560 CEST: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet1/0/30, changed state to up"
    timestamp = datetime.datetime(now.year, 10, 28, 13, 15, 57)
    facility = 'LINEPROTO'
    priority = 5
    mnemonic = 'UPDOWN'
    description = (
        "Line protocol on Interface GigabitEthernet1/0/30, changed state to up"
    )

    def test_should_parse_without_exception(self):
        assert logengine.create_message(self.message)

    def test_should_parse_timestamp_correctly(self):
        msg = logengine.create_message(self.message)
        assert msg.time == self.timestamp

    def test_should_parse_facility_correctly(self):
        msg = logengine.create_message(self.message)
        assert msg.facility == self.facility

    def test_should_parse_priority_correctly(self):
        msg = logengine.create_message(self.message)
        assert msg.priorityid == self.priority

    def test_should_parse_mnemonic_correctly(self):
        msg = logengine.create_message(self.message)
        assert msg.mnemonic == self.mnemonic

    def test_should_parse_description_correctly(self):
        msg = logengine.create_message(self.message)
        assert msg.description == self.description


class TestParseMessageWithStrangeGarbage(TestParsing):
    message = "Mar 25 10:54:25 somedevice 72: AP:000b.adc0.ffee: *Mar 25 10:15:51.666: %LINK-3-UPDOWN: Interface Dot11Radio0, changed state to up"

    timestamp = datetime.datetime(now.year, 3, 25, 10, 15, 51)
    facility = 'LINK'
    priority = 3
    mnemonic = 'UPDOWN'
    description = "Interface Dot11Radio0, changed state to up"


class TestParseMessageEndingWithColon(TestParsing):
    """Regression test for issue LP#720024"""

    message = "Feb 16 11:55:08 10.0.1.15 22877425: Feb 16 11:55:09.436 MET: %HA_EM-6-LOG: on_high_cpu: CPU utilization is over 80%:"

    timestamp = datetime.datetime(now.year, 2, 16, 11, 55, 9)
    facility = 'HA_EM'
    priority = 6
    mnemonic = 'LOG'
    description = "on_high_cpu: CPU utilization is over 80%:"


class TestParseMessageWithNoOriginTimestamp(TestParsing):
    message = "Nov 13 11:21:02 10.0.1.15 : %ASA-3-321007: System is low on free memory blocks of size 8192 (0 CNT out of 250 MAX)"

    timestamp = datetime.datetime(now.year, 11, 13, 11, 21, 2)
    facility = 'ASA'
    priority = 3
    mnemonic = '321007'
    description = (
        "System is low on free memory blocks of size 8192 (0 CNT out of 250 MAX)"
    )


non_conforming_lines = [
    "Dec 20 15:16:04 10.0.101.179 SNTP[141365768]: sntp_client.c(1917) 2945474 %% SNTP: system clock synchronized on THU DEC 20 15:16:04 2012 UTC. Indicates that SNTP has successfully synchronized the time of the box with the server.",
    "Dec 20 16:23:37 10.0.3.15 2605010: CPU utilization for five seconds: 86%/14%; one minute: 33%; five minutes: 31%",
    "Jan 29 10:21:26 10.0.129.61 %LINK-W-Down:  e30",
    "pr 18 05:12:59.716 CEST: %SISF-6-ENTRY_CHANGED: Entry changed A=FE80::10F1:F7E9:6EDF:2129 V=204 I=Gi0/8 P=0005 M=",
]


@pytest.mark.parametrize("line", non_conforming_lines)
def test_non_conforming_lines(line):
    msg = logengine.create_message(line)
    assert msg is None, "line shouldn't be parseable: %s" % line

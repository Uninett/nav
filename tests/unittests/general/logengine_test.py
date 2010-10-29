from minimock import Mock
from unittest import TestCase
import random

from nav import logengine

class TestParseAndInsertWithMockedDatabase(TestCase):
    def setUp(self):
        self.loglines = """
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

    def test_parse(self):
        for line in self.loglines:
            print line
            logengine.createMessage(line)

    def test_insert(self):
        for line in self.loglines:
            print line
            database = Mock('cursor')
            database.fetchone = lambda: [random.randint(1, 10000)]
            def execute(sql, params=()):
                return sql % params
            database.execute = execute
            message = logengine.createMessage(line)
            logengine.insert_message(message, database,
                                     {}, {}, {},
                                     {}, {}, {})


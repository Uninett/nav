# ruff: noqa E501

from unittest import TestCase

from nav.ipdevpoll.plugins.system import parse_version


class SysDescrParseTests(TestCase):
    def test_should_parse_cisco2950_sysdescr(self):
        sysdescr = """Cisco Internetwork Operating System Software
IOS (tm) C2950 Software (C2950-I6K2L2Q4-M), Version 12.1(22)EA11, RELEASE SOFTWARE (fc2)
Copyright (c) 1986-2008 by cisco Systems, Inc.
Compiled Tue 08-Jan-08 11:12 by amvarma"""

        self.assertEqual(parse_version(sysdescr), "12.1(22)EA11")

    def test_should_parse_cisco6509_sysdescr(self):
        sysdescr = """Cisco IOS Software, s72033_rp Software (s72033_rp-ADVIPSERVICESK9_WAN-M), Version 12.2(33)SXI4a, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2010 by Cisco Systems, Inc.
Compiled Fri 16-Jul-10 19:51 by p"""

        self.assertEqual(parse_version(sysdescr), "12.2(33)SXI4a")

    def test_should_parse_nortel5510_sysdescr(self):
        sysdescr = """Ethernet Routing Switch 5510-48T      HW:31       FW:6.0.0.8   SW:v6.1.1.017 BN:17 (c) Nortel Networks"""

        self.assertEqual(parse_version(sysdescr), "v6.1.1.017")

    def test_should_parse_virtual_hp_rack_sysdescr(self):
        sysdescr = """HP 1/10Gb VC-Enet Module Virtual Connect 2.34"""
        self.assertEqual(parse_version(sysdescr), "2.34")

    def test_should_parse_juniper_t640_sysdescr(self):
        sysdescr = """Juniper Networks, Inc. t640 internet router, kernel JUNOS 10.4R5.5 #0: 2011-06-14 02:02:06 UTC     builder@warth.juniper.net:/volume/build/junos/10.4/release/10.4R5.5/obj-i386/bsd/sys/compile/JUNIPER Build date: 2011-06-14 01:35:21 UTC Copyright (c) 1996"""

        self.assertEqual(parse_version(sysdescr), "10.4R5.5")

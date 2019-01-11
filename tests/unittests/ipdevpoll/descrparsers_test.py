#
# Copyright (C) 2010 Uninett AS
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
"""Unit tests for descrparser module."""

import unittest

from nav.ipdevpoll import descrparsers


class NtnuConventionTest(unittest.TestCase):

    def setUp(self):
        self.sysname = 'foo-sw'

    def test_lan(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'lan,math,staff')
        self.assertNotEquals(d, None)
        self.assertEqual(d['org'], 'math')
        self.assertEqual(d['usage'], 'staff')
        self.assertEqual(d['netident'], 'math,staff')

    def test_lan_with_comment_and_vlan(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'lan,physics,students,campus_dragv,340')
        self.assertNotEquals(d, None)
        self.assertEqual(d['org'], 'physics')
        self.assertEqual(d['usage'], 'students')
        self.assertEqual(d['comment'], 'campus_dragv')
        self.assertEqual(d['netident'], 'physics,students,campus_dragv')
        self.assertEqual(d['vlan'], 340)

    def test_lan_with_numbered_usage_and_comment(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'lan,math,staff12,campus_lade')
        self.assertNotEquals(d, None)
        self.assertEqual(d['org'], 'math')
        self.assertEqual(d['usage'], 'staff')
        self.assertEqual(d['n'], 12)
        self.assertEqual(d['netident'], 'math,staff12,campus_lade')
        self.assertEqual(d['comment'], 'campus_lade')

    def test_lan_with_spaces(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'lan ,physics,students,  campus_dragv, 340')
        self.assertNotEquals(d, None)
        self.assertEqual(d['org'], 'physics')
        self.assertEqual(d['usage'], 'students')
        self.assertEqual(d['comment'], 'campus_dragv')
        self.assertEqual(d['netident'], 'physics,students,campus_dragv')
        self.assertEqual(d['vlan'], 340)

    def test_lan_invalid(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'lan,foo')
        self.assertEquals(d, None)

    def test_link(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'link,mts-gw')
        self.assertNotEquals(d, None)
        self.assertEqual(d['to_router'], 'mts-gw')

    def test_link_with_comment_and_vlan(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'link,moholt-gw,Tn_20022350,923')
        self.assertEqual(d['to_router'], 'moholt-gw')
        self.assertEqual(d['comment'], 'Tn_20022350')
        self.assertEqual(d['netident'], '%s,%s' % (self.sysname, 'moholt-gw'))
        self.assertEqual(d['vlan'], 923)

    def test_core(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'core,it,wlan')
        self.assertNotEquals(d, None)
        self.assertEqual(d['org'], 'it')
        self.assertEqual(d['usage'], 'wlan')
        self.assertEqual(d['netident'], 'it,wlan')

    def test_core_with_comment_and_vlan(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'core,it,fddi,manring,180')
        self.assertNotEquals(d, None)
        self.assertEqual(d['org'], 'it')
        self.assertEqual(d['usage'], 'fddi')
        self.assertEqual(d['comment'], 'manring')
        self.assertEqual(d['netident'], 'it,fddi,manring')
        self.assertEqual(d['vlan'], 180)

    def test_core_invalid(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'core,foo')
        self.assertEquals(d, None)

    def test_elink(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'elink,trd-gw,uninett')
        self.assertNotEquals(d, None)
        self.assertEqual(d['to_router'], 'trd-gw')
        self.assertEqual(d['to_org'], 'uninett')
        self.assertEqual(d['netident'], '%s,%s' % (self.sysname, 'trd-gw'))

    def test_elink_with_empty_comment(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'elink,sintef-gw,sintef,,902')
        self.assertNotEquals(d, None)
        self.assertEqual(d['to_router'], 'sintef-gw')
        self.assertEqual(d['to_org'], 'sintef')
        self.assertFalse(d['comment'])
        self.assertEqual(d['netident'], '%s,%s' % (self.sysname, 'sintef-gw'))
        self.assertEqual(d['vlan'], 902)

    def test_invalid(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'foobar,bar,baz')
        self.assertEquals(d, None)


class UninettConventionTest(unittest.TestCase):
    def test_simple(self):
        d = descrparsers.parse_uninett_convention(
            'foo-sw', 'lokal link, uninett-gw.teknobyen-gw2')
        self.assertEquals(d['comment'], 'lokal link')
        self.assertEquals(d['netident'], 'uninett-gw.teknobyen-gw2')

    def test_invalid(self):
        d = descrparsers.parse_uninett_convention(
            'foo-sw', 'KX182')
        self.assertEquals(d, None)

if __name__ == '__main__':
        unittest.main()

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

from nav.ipdevpoll import descrparsers


class TestNtnuConvention(object):
    sysname = 'foo-sw'

    def test_lan(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'lan,math,staff')
        assert d is not None
        assert d['org'] == 'math'
        assert d['usage'] == 'staff'
        assert d['netident'] == 'math,staff'

    def test_lan_with_comment_and_vlan(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'lan,physics,students,campus_dragv,340'
        )
        d is not None
        assert d['org'] == 'physics'
        assert d['usage'] == 'students'
        assert d['comment'] == 'campus_dragv'
        assert d['netident'] == 'physics,students,campus_dragv'
        assert d['vlan'] == 340

    def test_lan_with_numbered_usage_and_comment(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'lan,math,staff12,campus_lade'
        )
        d is not None
        assert d['org'] == 'math'
        assert d['usage'] == 'staff'
        assert d['n'] == 12
        assert d['netident'] == 'math,staff12,campus_lade'
        assert d['comment'] == 'campus_lade'

    def test_lan_with_spaces(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'lan ,physics,students,  campus_dragv, 340'
        )
        d is not None
        assert d['org'] == 'physics'
        assert d['usage'] == 'students'
        assert d['comment'] == 'campus_dragv'
        assert d['netident'] == 'physics,students,campus_dragv'
        assert d['vlan'] == 340

    def test_lan_invalid(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'lan,foo')
        assert d is None

    def test_link(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'link,mts-gw')
        d is not None
        assert d['to_router'] == 'mts-gw'

    def test_link_with_comment_and_vlan(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'link,moholt-gw,Tn_20022350,923'
        )
        assert d['to_router'] == 'moholt-gw'
        assert d['comment'] == 'Tn_20022350'
        assert d['netident'] == '%s,%s' % (self.sysname, 'moholt-gw')
        assert d['vlan'] == 923

    def test_core(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'core,it,wlan')
        d is not None
        assert d['org'] == 'it'
        assert d['usage'] == 'wlan'
        assert d['netident'] == 'it,wlan'

    def test_core_with_comment_and_vlan(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'core,it,fddi,manring,180')
        d is not None
        assert d['org'] == 'it'
        assert d['usage'] == 'fddi'
        assert d['comment'] == 'manring'
        assert d['netident'] == 'it,fddi,manring'
        assert d['vlan'] == 180

    def test_core_invalid(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'core,foo')
        assert d is None

    def test_elink(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'elink,trd-gw,uninett')
        d is not None
        assert d['to_router'] == 'trd-gw'
        assert d['to_org'] == 'uninett'
        assert d['netident'] == '%s,%s' % (self.sysname, 'trd-gw')

    def test_elink_with_empty_comment(self):
        d = descrparsers.parse_ntnu_convention(
            self.sysname, 'elink,sintef-gw,sintef,,902'
        )
        d is not None
        assert d['to_router'] == 'sintef-gw'
        assert d['to_org'] == 'sintef'
        assert not d['comment']
        assert d['netident'] == '%s,%s' % (self.sysname, 'sintef-gw')
        assert d['vlan'] == 902

    def test_invalid(self):
        d = descrparsers.parse_ntnu_convention(self.sysname, 'foobar,bar,baz')
        assert d is None


class TestUninettConvention(object):
    def test_simple(self):
        d = descrparsers.parse_uninett_convention(
            'foo-sw', 'lokal link, uninett-gw.teknobyen-gw2'
        )
        assert d['comment'] == 'lokal link'
        assert d['netident'] == 'uninett-gw.teknobyen-gw2'

    def test_invalid(self):
        d = descrparsers.parse_uninett_convention('foo-sw', 'KX182')
        assert d is None

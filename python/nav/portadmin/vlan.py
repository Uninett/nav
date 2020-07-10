#
# Copyright (C) 2012, 2013, 2017 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""VLAN specific data structures for use in PortAdmin"""
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class FantasyVlan(object):
    """A container object for storing vlans for a netbox

    This object is needed because we mix "real" vlans that NAV know about
    and "fake" vlan that NAV does not know about but exists on the switch.
    They need to be compared and sorted, and this class does that.

    """

    def __init__(self, vlan, netident=None, descr=None):
        self.vlan = vlan
        self.net_ident = netident
        self.descr = descr

    def __str__(self):
        if self.net_ident:
            return "%s (%s)" % (self.vlan, self.net_ident)
        else:
            return str(self.vlan)

    def __hash__(self):
        return hash(self.vlan)

    def __lt__(self, other):
        return self.vlan < other.vlan

    def __eq__(self, other):
        return self.vlan == other.vlan

    def __repr__(self):
        return (
            "{self.__class__.__name__}(vlan={self.vlan!r}, "
            "netident={self.net_ident!r}, descr={self.descr!r})"
        ).format(self=self)

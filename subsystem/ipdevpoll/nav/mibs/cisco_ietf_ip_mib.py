# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Implements a MibRetriever for the CISCO-IETF-IP-MIB."""
from nav.mibs.ip_mib import IpMib

class CiscoIetfIpMib(IpMib):
    """CISCO-IETF-IP-MIB is based on a a draft version of IETF's
    revised IP-MIB (with address type agnostic extensions).  Its
    structure is basically the same, with altered object names and
    ids. 

    We try to avoid code redundancies by inheriting from the IpMib
    MibRetriever implementation, which was written using the revised
    IP-MIB.

    """
    from nav.smidumps.cisco_ietf_ip_mib import MIB as mib

    @classmethod
    def address_index_to_ip(cls, index):
        """Convert a row index from cIpAddressTable to an IP object."""

        entry = cls.nodes['cIpAddressEntry']
        if entry.oid.isaprefix(index):
            # Chop off the entry OID+column prefix
            index = index[(len(entry.oid) + 1):]

        return super(CiscoIetfIpMib, cls).address_index_to_ip(index)

    @classmethod
    def prefix_index_to_ip(cls, index):
        """Convert a row index from cIpAddressPfxTable to an IP object."""

        entry = cls.nodes['cIpAddressPfxEntry']
        if entry.oid.isaprefix(index):
            # Chop off the entry OID+column prefix
            index = index[(len(entry.oid) + 1):]

        return super(CiscoIetfIpMib, cls).prefix_index_to_ip(index)

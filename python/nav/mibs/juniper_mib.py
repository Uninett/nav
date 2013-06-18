#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""JUNIPER-MIB MibRetriever"""
from twisted.internet import defer
from nav.mibs.mibretriever import MibRetriever


class JuniperMib(MibRetriever):
    """JUNIPER-MIB MibRetriever"""
    from nav.smidumps.juniper_mib import MIB as mib

    @defer.inlineCallbacks
    def get_serial_number(self):
        """Tries to get a serial number from a Juniper device"""
        serial = yield self.get_next('jnxBoxSerialNo')
        if serial:
            defer.returnValue(serial)

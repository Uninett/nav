#
# Copyright (C) 2015 Uninett AS
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
from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever


class HPHTTPManageableMib(MibRetriever):
    """HP-httpManageable-MIB (SEMI-MIB) MibRetriever"""

    mib = get_mib('SEMI-MIB')

    @defer.inlineCallbacks
    def get_serial_number(self):
        """Tries to get a chassis serial number from old HP switches"""
        serial = yield self.get_next('hpHttpMgSerialNumber')
        if serial:
            if isinstance(serial, bytes):
                serial = serial.decode("utf-8")
            return serial

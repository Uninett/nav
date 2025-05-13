#
# Copyright (C) 2011-2015, 2019 Uninett AS
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
"""Hewlett-Packard specific PortAdmin SNMP handling"""

from nav.oids import OID
from nav.portadmin.snmp.base import SNMPHandler, translate_protocol_errors
from nav.enterprise.ids import VENDOR_ID_HEWLETT_PACKARD


class HP(SNMPHandler):
    """A specialized class for handling ports in HP switches."""

    VENDOR = VENDOR_ID_HEWLETT_PACKARD

    # From HP-DOT1X-EXTENSIONS-MIB
    # hpicfDot1xPaePortAuth return INTEGER { true(1), false(2) }
    dot1xPortAuth = '1.3.6.1.4.1.11.2.14.11.5.1.25.1.1.1.1.1'

    def __init__(self, netbox, **kwargs):
        super(HP, self).__init__(netbox, **kwargs)

    @translate_protocol_errors
    def is_dot1x_enabled(self, interface):
        """Returns True or False based on state of dot1x"""
        return int(self._query_netbox(self.dot1xPortAuth, interface.ifindex)) == 1

    @translate_protocol_errors
    def get_dot1x_enabled_interfaces(self):
        names = self._get_interface_names()
        return {
            names.get(OID(oid)[-1]): state == 1
            for oid, state in self._bulkwalk(self.dot1xPortAuth)
        }

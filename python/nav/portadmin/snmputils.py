#
# Copyright (C) 2011-2015, 2020 Uninett AS
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
"""This is a utility library made especially for PortAdmin."""
from nav.enterprise.ids import (
    VENDOR_ID_CISCOSYSTEMS,
    VENDOR_ID_HEWLETT_PACKARD,
    VENDOR_ID_H3C,
    VENDOR_ID_DELL_INC,
)

from nav.errors import NoNetboxTypeError
from nav.portadmin.snmp.base import SNMPHandler
from nav.portadmin.snmp.cisco import Cisco
from nav.portadmin.snmp.dell import Dell
from nav.portadmin.snmp.h3c import H3C
from nav.portadmin.snmp.hp import HP


class SNMPFactory(object):
    """Factory class for returning SNMP-handles depending
    on a netbox' vendor identification."""

    @classmethod
    def get_instance(cls, netbox, **kwargs):
        """Get and SNMP-handle depending on vendor type"""
        if not netbox.type:
            raise NoNetboxTypeError()
        vendor_id = netbox.type.get_enterprise_id()
        if vendor_id == VENDOR_ID_CISCOSYSTEMS:
            return Cisco(netbox, **kwargs)
        if vendor_id == VENDOR_ID_HEWLETT_PACKARD:
            return HP(netbox, **kwargs)
        if vendor_id == VENDOR_ID_H3C:
            return H3C(netbox, **kwargs)
        if vendor_id == VENDOR_ID_DELL_INC:
            return Dell(netbox, **kwargs)
        return SNMPHandler(netbox, **kwargs)

    def __init__(self):
        pass

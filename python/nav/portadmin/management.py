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
from nav.errors import NoNetboxTypeError
from nav.models import manage
from nav.portadmin.handlers import ManagementHandler
from nav.portadmin.snmp.base import SNMPHandler
from nav.portadmin.snmp.cisco import Cisco
from nav.portadmin.snmp.dell import Dell
from nav.portadmin.snmp.h3c import H3C
from nav.portadmin.snmp.hp import HP
from nav.portadmin.napalm.juniper import Juniper

VENDOR_MAP = {cls.VENDOR: cls for cls in (Cisco, Dell, H3C, HP, Juniper)}


class ManagementFactory(object):
    """Factory class for returning management handles, depending
    on a netbox' vendor identification and its management configuration."""

    @classmethod
    def get_instance(cls, netbox: manage.Netbox, **kwargs) -> ManagementHandler:
        """Get and SNMP-handle depending on vendor type"""
        if not netbox.type:
            raise NoNetboxTypeError()

        vendor_id = netbox.type.get_enterprise_id()
        handler = VENDOR_MAP.get(vendor_id, SNMPHandler)
        return handler(netbox, **kwargs)

    def __init__(self):
        pass

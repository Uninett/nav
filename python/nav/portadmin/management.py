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

SUPPORTED_HANDLERS = (Cisco, Dell, H3C, HP, Juniper)
FALLBACK_HANDLER = SNMPHandler


class ManagementFactory(object):
    """Factory class for returning management handles, depending
    on a netbox' vendor identification and its management configuration."""

    @classmethod
    def get_instance(cls, netbox: manage.Netbox, **kwargs) -> ManagementHandler:
        """Get and SNMP-handle depending on vendor type"""
        if not netbox.type:
            raise NoNetboxTypeError()

        matched_handlers = (h for h in SUPPORTED_HANDLERS if h.can_handle(netbox))
        chosen_handler = next(matched_handlers, FALLBACK_HANDLER)
        return chosen_handler(netbox, **kwargs)

    def __init__(self):
        pass

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
from nav.portadmin.cnaas_nms.proxy import CNaaSNMSMixIn
from nav.portadmin.config import CONFIG
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
        """Returns a ManagementHandler implementation, depending on Netbox vendor and
        configured management protocol.
        """
        if not netbox.type:
            raise NoNetboxTypeError()

        vendor_id = netbox.type.get_enterprise_id()
        handler = VENDOR_MAP.get(vendor_id, SNMPHandler)

        if CONFIG.is_cnaas_nms_enabled():
            handler = cls._hybridize_cnaas_nms_handler(handler)

        return handler(netbox, **kwargs)

    @classmethod
    def _hybridize_cnaas_nms_handler(cls, handler):
        """Builds and returns a hybrid ManagementHandler class.

        The class will have two base classes, the CNaaSNMSMixIn class and handler,
        thereby letting the CNaaSMixIn implementation override methods from handler
        as it sees fit.
        """

        class HybridProxyHandler(CNaaSNMSMixIn, handler):
            pass

        return HybridProxyHandler

    def __init__(self):
        pass

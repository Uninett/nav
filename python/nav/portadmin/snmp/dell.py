#
# Copyright (C) 2017, 2019 UNINETT
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
"""Dell specific PortAdmin SNMP handling"""

import logging

from nav.portadmin.snmp.base import SNMPHandler, translate_protocol_errors
from nav.smidumps import get_mib
from nav.enterprise.ids import VENDOR_ID_DELL_INC


_logger = logging.getLogger(__name__)


class Dell(SNMPHandler):
    """Dell INC handler

    Uses DNOS-SWITCHING-MIB
    """

    VENDOR = VENDOR_ID_DELL_INC

    DNOSNODES = get_mib('DNOS-SWITCHING-MIB')['nodes']

    PORT_MODE_ACCESS = 1
    PORT_MODE_TRUNK = 2
    PORT_MODE_GENERAL = 3

    PORT_MODE_OID = DNOSNODES['agentPortSwitchportMode']['oid']
    NATIVE_VLAN_ID = DNOSNODES['agentPortNativeVlanID']['oid']
    # Overriding members
    VlAN_OID = DNOSNODES['agentPortAccessVlanID']['oid']
    VLAN_EGRESS_PORTS = DNOSNODES['agentVlanSwitchportTrunkStaticEgressPorts']['oid']
    WRITE_MEM_OID = DNOSNODES['agentSaveConfig']['oid'] + '.0'

    def __init__(self, netbox, **kwargs):
        super(Dell, self).__init__(netbox, **kwargs)

    @translate_protocol_errors
    def commit_configuration(self):
        """Use DNOS-SWITCHING-MIB agentSaveConfig to write to memory.
        Write configuration into non-volatile memory."""
        handle = self._get_read_write_handle()
        return handle.set(self.WRITE_MEM_OID, 'i', 1)

    @translate_protocol_errors
    def set_vlan(self, interface, vlan):
        baseport = interface.baseport
        try:
            vlan = int(vlan)
        except ValueError:
            raise TypeError('Not a valid vlan %s' % vlan)
        # Fetch current vlan
        fromvlan = self.get_interface_native_vlan(interface)
        # fromvlan and vlan is the same, there's nothing to do
        if fromvlan == vlan:
            _logger.debug('fromvlan and vlan is the same - skip')
            return None

        self._set_netbox_value(self.VlAN_OID, baseport, "i", vlan)

    @translate_protocol_errors
    def set_access(self, interface, access_vlan):
        self._set_swport_mode(interface, self.PORT_MODE_ACCESS)
        self.set_vlan(interface, access_vlan)
        interface.vlan = access_vlan
        interface.trunk = False
        interface.save()

    @translate_protocol_errors
    def set_trunk(self, interface, native_vlan, trunk_vlans):
        self._set_swport_mode(interface, self.PORT_MODE_TRUNK)
        self.set_trunk_vlans(interface, trunk_vlans)
        self.set_native_vlan(interface, native_vlan)
        interface.vlan = native_vlan
        interface.trunk = True
        interface.save()

    def _set_swport_mode(self, interface, mode):
        baseport = interface.baseport
        self._set_netbox_value(self.PORT_MODE_OID, baseport, 'i', mode)

    @translate_protocol_errors
    def get_interface_native_vlan(self, interface):
        # FIXME This override is potentially only applicable for trunk ports
        baseport = interface.baseport
        return self._query_netbox(self.NATIVE_VLAN_ID, baseport)

    @translate_protocol_errors
    def set_native_vlan(self, interface, vlan):
        """Set native vlan on a trunk interface"""
        baseport = interface.baseport
        self._set_netbox_value(self.NATIVE_VLAN_ID, baseport, "i", vlan)

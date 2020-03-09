#
# Copyright (C) 2011-2015, 2020 UNINETT
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
import time
from operator import attrgetter
import logging

from django.utils import six

from nav import Snmp
from nav.Snmp import safestring, OID
from nav.Snmp.errors import UnsupportedSnmpVersionError, SnmpError, NoSuchObjectError
from nav.bitvector import BitVector

from nav.models.manage import Vlan, SwPortAllowedVlan
from nav.portadmin.handlers import ManagementHandler
from nav.portadmin.vlan import FantasyVlan
from nav.smidumps import get_mib


_logger = logging.getLogger(__name__)


class SNMPHandler(ManagementHandler):
    """Implements PortAdmin management functions for SNMP-enabled switches"""
    VENDOR = None

    QBRIDGENODES = get_mib('Q-BRIDGE-MIB')['nodes']

    SYSOBJECTID = '.1.3.6.1.2.1.1.2.0'
    SYSLOCATION = '1.3.6.1.2.1.1.6.0'
    IF_ALIAS_OID = '1.3.6.1.2.1.31.1.1.1.18'  # From IF-MIB
    IF_ADMIN_STATUS = '1.3.6.1.2.1.2.2.1.7'
    IF_ADMIN_STATUS_UP = 1
    IF_ADMIN_STATUS_DOWN = 2
    IF_OPER_STATUS = '1.3.6.1.2.1.2.2.1.8'

    # The VLAN ID assigned to untagged frames
    VlAN_OID = QBRIDGENODES['dot1qPvid']['oid']

    # List of all available vlans on this netbox as by the command "show vlans"
    VLAN_ROW_STATUS = QBRIDGENODES['dot1qVlanStaticRowStatus']['oid']

    # List of all ports on a vlan as a hexstring (including native vlan)
    VLAN_EGRESS_PORTS = QBRIDGENODES['dot1qVlanStaticEgressPorts']['oid']

    # The .0 is the timefilter that we set to 0 to (hopefully) deactivate the filter
    CURRENT_VLAN_EGRESS_PORTS = QBRIDGENODES['dot1qVlanCurrentEgressPorts']['oid'] + '.0'

    # dot1x

    # dot1xPaeSystemAuthControl: The administrative enable/ disable state for
    # Port Access Control in a System.
    dot1xPaeSystemAuthControl = '1.0.8802.1.1.1.1.1.1.0'

    def __init__(self, netbox, **kwargs):
        super().__init__(netbox, **kwargs)
        self.read_only_handle = None
        self.read_write_handle = None
        self.available_vlans = None
        self.timeout = kwargs.get('timeout', 3)
        self.retries = kwargs.get('retries', 3)

    def _bulkwalk(self, oid):
        """Walk all branches for the given oid."""
        handle = self._get_read_only_handle()
        result = []
        try:
            result = handle.bulkwalk(oid)
        except UnsupportedSnmpVersionError as unsup_ex:
            _logger.info("_bulkwalk: UnsupportedSnmpVersionError = %s",
                         unsup_ex)
            try:
                result = handle.walk(oid)
            except SnmpError as ex:
                _logger.error("_bulkwalk: Exception = %s", ex)
        return result

    def _jog(self, oid):
        """Do a jog"""
        handle = self._get_read_only_handle()
        try:
            return handle.jog(oid)
        except SnmpError as _error:
            return []

    @staticmethod
    def _get_legal_if_index(if_index):
        """Check if the given index is a legal interface-index."""
        return str(int(if_index))

    def _get_query(self, oid, if_index):
        """Concat given oid and interface-index."""
        return oid + ("." + self._get_legal_if_index(if_index))

    def _get_read_only_handle(self):
        """Get a read only SNMP-handle."""
        if self.read_only_handle is None:
            self.read_only_handle = Snmp.Snmp(self.netbox.ip,
                                              self.netbox.read_only,
                                              self.netbox.snmp_version,
                                              retries=self.retries,
                                              timeout=self.timeout)
        return self.read_only_handle

    def _query_netbox(self, oid, if_index):
        """Query the given interface."""
        handle = self._get_read_only_handle()
        result = None
        try:
            result = handle.get(self._get_query(oid, if_index))
        except NoSuchObjectError as no_such_ex:
            _logger.debug("_query_netbox: NoSuchObjectError = %s", no_such_ex)
        return result

    def _get_read_write_handle(self):
        """Get a read and write SNMP-handle.

        :rtype: nav.Snmp.Snmp
        """
        if self.read_write_handle is None:
            self.read_write_handle = Snmp.Snmp(
                self.netbox.ip, self.netbox.read_write,
                self.netbox.snmp_version, retries=self.retries,
                timeout=self.timeout)
        return self.read_write_handle

    def _set_netbox_value(self, oid, if_index, value_type, value):
        """Set a value for the given interface."""
        handle = self._get_read_write_handle()
        return handle.set(self._get_query(oid, if_index), value_type, value)

    @staticmethod
    def _chunkify(bitvector, chunks):
        """Divide bitvector into chunks number of chunks

        :returns a new bitvector instance with the chunk

        """
        hexes = bitvector.to_hex()
        chunksize = len(bitvector.to_hex()) // chunks
        for i in range(0, len(hexes), chunksize):
            yield BitVector.from_hex(hexes[i:i + chunksize])

    def test_read(self):
        handle = self._get_read_only_handle()
        try:
            handle.get(self.SYSOBJECTID)
            return True
        except SnmpError as error:
            return False

    def test_write(self):
        handle = self._get_read_write_handle()
        try:
            value = handle.get(self.SYSLOCATION)
            handle.set(self.SYSLOCATION, 's', value)
            return True
        except SnmpError as error:
            return False

    def get_if_alias(self, if_index):
        return safestring(self._query_netbox(self.IF_ALIAS_OID, if_index))

    def get_all_if_alias(self):
        return {
            OID(oid)[-1]: safestring(value)
            for oid, value in self._bulkwalk(self.IF_ALIAS_OID)
        }

    def set_if_alias(self, if_index, if_alias):
        if isinstance(if_alias, six.text_type):
            if_alias = if_alias.encode('utf8')
        return self._set_netbox_value(self.IF_ALIAS_OID, if_index, "s",
                                      if_alias)

    def get_vlan(self, interface):
        return self._query_netbox(self.VlAN_OID, interface.baseport)

    def get_all_vlans(self):
        return {OID(index)[-1]: value for index, value in self._bulkwalk(self.VlAN_OID)}

    @staticmethod
    def _compute_octet_string(hexstring, port, action='enable'):
        """
        hexstring: the returnvalue of the snmpquery
        port: the number of the port to add
        """
        bit = BitVector(hexstring)
        # Add port to string
        port -= 1
        if action == 'enable':
            bit[port] = 1
        else:
            bit[port] = 0
        return bit.to_bytes()

    def set_vlan(self, interface, vlan):
        base_port = interface.baseport
        try:
            vlan = int(vlan)
        except ValueError:
            raise TypeError('Not a valid vlan %s' % vlan)
        # Fetch current vlan
        fromvlan = self.get_vlan(interface)
        # fromvlan and vlan is the same, there's nothing to do
        if fromvlan == vlan:
            _logger.debug('fromvlan and vlan is the same - skip')
            return None
        # Add port to vlan. This makes the port active on both old and new vlan
        _logger.debug('Enabling port %s on vlan %s', base_port, vlan)
        self._set_netbox_value(self.VlAN_OID, base_port, "u", vlan)
        # Remove port from list of ports on old vlan
        hexstring = self._query_netbox(self.VLAN_EGRESS_PORTS, fromvlan)
        modified_hexport = self._compute_octet_string(hexstring, base_port,
                                                      'disable')
        _logger.debug('Disabling port %s on old vlan %s', base_port, fromvlan)
        return self._set_netbox_value(self.VLAN_EGRESS_PORTS,
                                      fromvlan, 's', modified_hexport)

    def set_native_vlan(self, interface, vlan):
        self.set_vlan(interface, vlan)

    def set_if_up(self, if_index):
        return self._set_netbox_value(self.IF_ADMIN_STATUS, if_index, "i",
                                      self.IF_ADMIN_STATUS_UP)

    def set_if_down(self, if_index):
        return self._set_netbox_value(self.IF_ADMIN_STATUS, if_index, "i",
                                      self.IF_ADMIN_STATUS_DOWN)

    def restart_if(self, if_index, wait=5):
        wait = int(wait)
        self.set_if_down(if_index)
        _logger.debug('Interface set administratively down - '
                      'waiting %s seconds', wait)
        time.sleep(wait)
        self.set_if_up(if_index)
        _logger.debug('Interface set administratively up')

    def write_mem(self):
        pass

    def get_if_admin_status(self, if_index):
        return self._query_netbox(self.IF_ADMIN_STATUS, if_index)

    def get_if_oper_status(self, if_index):
        return self._query_netbox(self.IF_OPER_STATUS, if_index)

    @staticmethod
    def _get_last_number(oid):
        """Get the last index for an OID."""
        # TODO: This method is superfluous, use nav.oids.OID objects instead
        if not (isinstance(oid, six.string_types)):
            raise TypeError('Illegal value for oid')
        splits = oid.split('.')
        last = splits[-1]
        if isinstance(last, six.string_types):
            if last.isdigit():
                last = int(last)
        return last

    def _get_if_stats(self, stats):
        """Make a list with tuples.  Each tuple contain
         interface-index and corresponding status-value"""
        available_stats = []
        for (if_index, stat) in stats:
            if_index = self._get_last_number(if_index)
            if isinstance(if_index, int):
                available_stats.append((if_index, stat))
        return available_stats

    def get_netbox_admin_status(self):
        if_admin_stats = self._bulkwalk(self.IF_ADMIN_STATUS)
        return self._get_if_stats(if_admin_stats)

    def get_netbox_oper_status(self):
        if_oper_stats = self._bulkwalk(self.IF_OPER_STATUS)
        return self._get_if_stats(if_oper_stats)

    def get_netbox_vlans(self):
        numerical_vlans = self.get_available_vlans()
        vlan_objects = Vlan.objects.filter(
            swportvlan__interface__netbox=self.netbox).distinct()
        vlans = []
        for numerical_vlan in numerical_vlans:
            try:
                vlan_object = vlan_objects.get(vlan=numerical_vlan)
            except (Vlan.DoesNotExist, Vlan.MultipleObjectsReturned):
                fantasy_vlan = FantasyVlan(numerical_vlan)
            else:
                fantasy_vlan = FantasyVlan(numerical_vlan,
                                           netident=vlan_object.net_ident,
                                           descr=vlan_object.description)
            vlans.append(fantasy_vlan)

        return sorted(list(set(vlans)), key=attrgetter('vlan'))

    def get_available_vlans(self):
        if self.available_vlans is None:
            self.available_vlans = [
                int(self._extract_index_from_oid(oid))
                for oid, status in self._bulkwalk(self.VLAN_ROW_STATUS)
                if status == 1]
        return self.available_vlans

    def set_voice_vlan(self, interface, voice_vlan):
        self.set_trunk(interface, interface.vlan, [voice_vlan])

    @staticmethod
    def _extract_index_from_oid(oid):
        # TODO: This method is also superfluous, use nav.oids.OID objects instead
        return int(oid.split('.')[-1])

    def get_native_and_trunked_vlans(self, interface):
        native_vlan = self.get_native_vlan(interface)

        bitvector_index = interface.baseport - 1
        vlans = []
        for vlan in self.get_available_vlans():
            if vlan == native_vlan:
                continue
            octet_string = self._query_netbox(
                self.CURRENT_VLAN_EGRESS_PORTS, vlan
            ) or b''
            bitvector = BitVector(octet_string)

            try:
                if bitvector[bitvector_index]:
                    vlans.append(vlan)
            except IndexError:
                _logger.error('Baseport index was out of bounds '
                              'for StaticEgressPorts')

        return native_vlan, vlans

    def _get_egress_interfaces_as_bitvector(self, vlan):
        octet_string = self._query_netbox(self.CURRENT_VLAN_EGRESS_PORTS, vlan)
        return BitVector(octet_string)

    def get_native_vlan(self, interface):
        return self.get_vlan(interface)

    def set_trunk_vlans(self, interface, vlans):
        base_port = interface.baseport
        native_vlan = self.get_native_vlan(interface)
        bitvector_index = base_port - 1

        _logger.debug('base_port: %s, native_vlan: %s, trunk_vlans: %s',
                      base_port, native_vlan, vlans)

        vlans = [int(vlan) for vlan in vlans]

        for available_vlan in self.get_available_vlans():
            if native_vlan == available_vlan:
                _logger.debug('native vlan (%s) == available vlan (%s) - skip',
                              native_vlan, available_vlan)
                continue

            bitvector = self._get_egress_interfaces_as_bitvector(
                available_vlan)

            original_value = bitvector[bitvector_index]
            if available_vlan in vlans:
                bitvector[bitvector_index] = 1
            else:
                bitvector[bitvector_index] = 0

            if bitvector[bitvector_index] != original_value:
                _logger.debug('vlan %(vlan)s: state for port %(port)s changed',
                              {'port': base_port, 'vlan': available_vlan})
                self._set_egress_interfaces(available_vlan, bitvector)

    def _set_egress_interfaces(self, vlan, bitvector):
        try:
            _logger.debug('Setting egress ports for vlan %s, set bits: %s',
                          vlan, bitvector.get_set_bits())
            self._set_netbox_value(self.VLAN_EGRESS_PORTS,
                                   vlan, 's', bitvector.to_bytes())
        except SnmpError as error:
            _logger.error("Error setting egress ports: %s", error)
            raise error

    def set_access(self, interface, access_vlan):
        _logger.debug('Setting access mode vlan %s on interface %s',
                      access_vlan, interface)
        self.set_vlan(interface, access_vlan)
        self.set_trunk_vlans(interface, [])
        interface.vlan = access_vlan
        interface.trunk = False
        interface.save()

    def set_trunk(self, interface, native_vlan, trunk_vlans):
        self.set_vlan(interface, native_vlan)
        self.set_trunk_vlans(interface, trunk_vlans)
        self._save_trunk_interface(interface, native_vlan, trunk_vlans)

    def _save_trunk_interface(self, interface, native_vlan, trunk_vlans):
        interface.vlan = native_vlan
        interface.trunk = True
        self._set_interface_hex(interface, trunk_vlans)
        interface.save()

    @staticmethod
    def _set_interface_hex(interface, trunk_vlans):
        try:
            allowedvlan = interface.swportallowedvlan
        except SwPortAllowedVlan.DoesNotExist:
            allowedvlan = SwPortAllowedVlan(interface=interface)

        allowedvlan.set_allowed_vlans(trunk_vlans)
        allowedvlan.save()

    def is_dot1x_enabled(self, interfaces):
        """Explicitly returns None as we do not know on a SNMP-generic basis"""
        return None

    def get_dot1x_enabled_interfaces(self):
        return {}

    def is_port_access_control_enabled(self):
        handle = self._get_read_only_handle()
        return int(handle.get(self.dot1xPaeSystemAuthControl)) == 1

    # These are not relevant for this generic subclass
    get_cisco_voice_vlans = None
    set_cisco_voice_vlan = None
    enable_cisco_cdp = None
    disable_cisco_voice_vlan = None
    disable_cisco_cdp = None

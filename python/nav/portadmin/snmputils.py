#
# Copyright (C) 2011-2015 Uninett AS
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
import time
import logging
from operator import attrgetter

from django.utils import six
from django.utils.encoding import python_2_unicode_compatible

from nav import Snmp
from nav.errors import NoNetboxTypeError
from nav.Snmp.errors import (SnmpError, UnsupportedSnmpVersionError,
                             NoSuchObjectError)
from nav.bitvector import BitVector
from nav.models.manage import Vlan, SwPortAllowedVlan
from nav.enterprise.ids import (VENDOR_ID_CISCOSYSTEMS,
                                VENDOR_ID_H3C,
                                VENDOR_ID_DELL_INC,
                                VENDOR_ID_HEWLETT_PACKARD)


_logger = logging.getLogger("nav.portadmin.snmputils")
CHARS_IN_1024_BITS = 128

# TODO: Fix get_vlans as it does not return all vlans, see get_available_vlans


@python_2_unicode_compatible
class FantasyVlan(object):
    """A container object for storing vlans for a netbox

    This object is needed because we mix "real" vlans that NAV know about
    and "fake" vlan that NAV does not know about but exists on the switch.
    They need to be compared and sorted, and this class does that.

    """

    def __init__(self, vlan, netident=None, descr=None):
        self.vlan = vlan
        self.net_ident = netident
        self.descr = descr

    def __str__(self):
        if self.net_ident:
            return "%s (%s)" % (self.vlan, self.net_ident)
        else:
            return str(self.vlan)

    def __hash__(self):
        return hash(self.vlan)

    def __lt__(self, other):
        return self.vlan < other.vlan

    def __eq__(self, other):
        return self.vlan == other.vlan


@python_2_unicode_compatible
class SNMPHandler(object):
    """A basic class for SNMP-read and -write to switches."""

    from nav.smidumps.qbridge_mib import MIB as qbridgemib
    QBRIDGENODES = qbridgemib['nodes']

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

    netbox = None

    def __init__(self, netbox, **kwargs):
        self.netbox = netbox
        self.read_only_handle = None
        self.read_write_handle = None
        self.available_vlans = None
        self.timeout = kwargs.get('timeout', 3)
        self.retries = kwargs.get('retries', 3)

    def __str__(self):
        return self.netbox.type.vendor.id

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
        return oid + "." + self._get_legal_if_index(if_index)

    def _get_read_only_handle(self):
        """Get a read only SNMP-handle."""
        if self.read_only_handle is None:
            self.read_only_handle = Snmp.Snmp(self.netbox.ip, self.netbox.read_only,
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
        """Test if read works"""
        handle = self._get_read_only_handle()
        try:
            handle.get(self.SYSOBJECTID)
            return True
        except SnmpError as error:
            return False

    def test_write(self):
        """Test if write works"""
        handle = self._get_read_write_handle()
        try:
            value = handle.get(self.SYSLOCATION)
            handle.set(self.SYSLOCATION, 's', value)
            return True
        except SnmpError as error:
            return False

    def get_if_alias(self, if_index):
        """ Get alias on a specific interface """
        return self._query_netbox(self.IF_ALIAS_OID, if_index)

    def get_all_if_alias(self):
        """Get all aliases for all interfaces."""
        return self._bulkwalk(self.IF_ALIAS_OID)

    def set_if_alias(self, if_index, if_alias):
        """Set alias on a specific interface."""
        if isinstance(if_alias, six.text_type):
            if_alias = if_alias.encode('utf8')
        return self._set_netbox_value(self.IF_ALIAS_OID, if_index, "s",
                                      if_alias)

    def get_vlan(self, interface):
        """Get vlan on a specific interface."""
        return self._query_netbox(self.VlAN_OID, interface.baseport)

    def get_all_vlans(self):
        """Get all vlans on the switch"""
        return self._bulkwalk(self.VlAN_OID)

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
        """Set a new vlan on the given interface and remove
        the previous vlan"""
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
        """Set native vlan on a trunk interface"""
        self.set_vlan(interface, vlan)

    def set_if_up(self, if_index):
        """Set interface.to up"""
        return self._set_netbox_value(self.IF_ADMIN_STATUS, if_index, "i",
                                      self.IF_ADMIN_STATUS_UP)

    def set_if_down(self, if_index):
        """Set interface.to down"""
        return self._set_netbox_value(self.IF_ADMIN_STATUS, if_index, "i",
                                      self.IF_ADMIN_STATUS_DOWN)

    def restart_if(self, if_index, wait=5):
        """ Take interface down and up.
            wait = number of seconds to wait between down and up."""
        wait = int(wait)
        self.set_if_down(if_index)
        _logger.debug('Interface set administratively down - '
                      'waiting %s seconds', wait)
        time.sleep(wait)
        self.set_if_up(if_index)
        _logger.debug('Interface set administratively up')

    def write_mem(self):
        """ Do a write memory on netbox if available"""
        pass

    def get_if_admin_status(self, if_index):
        """Query administration status for a given interface."""
        return self._query_netbox(self.IF_ADMIN_STATUS, if_index)

    def get_if_oper_status(self, if_index):
        """Query operational status of a given interface."""
        return self._query_netbox(self.IF_OPER_STATUS, if_index)

    @staticmethod
    def _get_last_number(oid):
        """Get the last index for an OID."""
        if not (isinstance(oid, str) or isinstance(oid, unicode)):
            raise TypeError('Illegal value for oid')
        splits = oid.split('.')
        last = splits[-1]
        if isinstance(last, str):
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
        """Walk all ports and get their administration status."""
        if_admin_stats = self._bulkwalk(self.IF_ADMIN_STATUS)
        return self._get_if_stats(if_admin_stats)

    def get_netbox_oper_status(self):
        """Walk all ports and get their operational status."""
        if_oper_stats = self._bulkwalk(self.IF_OPER_STATUS)
        return self._get_if_stats(if_oper_stats)

    def get_netbox_vlans(self):
        """Create Fantasyvlans for all vlans on this netbox"""
        numerical_vlans = self.get_available_vlans()
        vlan_objects = Vlan.objects.filter(
            swportvlan__interface__netbox=self.netbox)
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
        """Get available vlans from the box

        This is similar to the terminal command "show vlans"

        """
        if self.available_vlans is None:
            self.available_vlans = [
                int(self._extract_index_from_oid(oid))
                for oid, status in self._bulkwalk(self.VLAN_ROW_STATUS)
                if status == 1]
        return self.available_vlans

    def set_voice_vlan(self, interface, voice_vlan):
        """Activate voice vlan on this interface

        Use set_trunk to make sure the interface is put in trunk mode

        """
        self.set_trunk(interface, interface.vlan, [voice_vlan])

    def get_cisco_voice_vlans(self):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    def set_cisco_voice_vlan(self, interface, voice_vlan):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    def disable_cisco_voice_vlan(self, interface):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    @staticmethod
    def _extract_index_from_oid(oid):
        return int(oid.split('.')[-1])

    def get_native_and_trunked_vlans(self, interface):
        """Get the trunked vlans on this interface

        For each available vlan, fetch list of interfaces that forward this
        vlan. If the interface index is in this list, add the vlan to the
        return list.

        :returns native vlan + list of trunked vlan

        """
        native_vlan = self.get_native_vlan(interface)

        bitvector_index = interface.baseport - 1
        vlans = []
        for vlan in self.get_available_vlans():
            if vlan == native_vlan:
                continue
            octet_string = self._query_netbox(
                self.CURRENT_VLAN_EGRESS_PORTS, vlan)
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
        """Trunk the vlans on interface

        Egress_Ports includes native vlan. Be sure to not alter that.

        Get all available vlans. For each available vlan fetch list of
        interfaces that forward this vlan. Set or remove the interface from
        this list based on if it is in the vlans list.

        """
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
        """Set this port in access mode and set access vlan

        Means - remove all vlans except access vlan from this interface
        """
        _logger.debug('Setting access mode vlan %s on interface %s',
                      access_vlan, interface)
        self.set_vlan(interface, access_vlan)
        self.set_trunk_vlans(interface, [])
        interface.vlan = access_vlan
        interface.trunk = False
        interface.save()

    def set_trunk(self, interface, native_vlan, trunk_vlans):
        """Set this port in trunk mode and set native vlan"""
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

    @staticmethod
    def _find_vlans_for_interface(interface):
        """Find vland for the given interface."""
        interface_vlans = interface.swportvlan_set.all()
        vlans = []
        if interface_vlans:
            for swportvlan in interface_vlans:
                vlan = swportvlan.vlan
                if vlan.vlan:
                    vlans.append(FantasyVlan(vlan.vlan, vlan.net_ident))
        elif interface.vlan:
            vlans = [FantasyVlan(vlan=interface.vlan)]
        return vlans

    def is_dot1x_enabled(self, interfaces):
        """Explicitly returns None as we do not know"""
        return None

    def get_dot1x_enabled_interfaces(self):
        """"""
        return {}

    def is_port_access_control_enabled(self):
        """Returns state of port access control"""
        handle = self._get_read_only_handle()
        return int(handle.get(self.dot1xPaeSystemAuthControl)) == 1


class Cisco(SNMPHandler):
    """A specialized class for handling ports in CISCO switches."""

    from nav.smidumps.cisco_vtp_mib import MIB as vtp_mib
    VTPNODES = vtp_mib['nodes']

    VTPVLANSTATE = VTPNODES['vtpVlanState']['oid']
    VTPVLANTYPE = VTPNODES['vtpVlanType']['oid']
    TRUNKPORTNATIVEVLAN = VTPNODES['vlanTrunkPortNativeVlan']['oid']
    TRUNKPORTVLANSENABLED = VTPNODES['vlanTrunkPortVlansEnabled']['oid']
    TRUNKPORTVLANSENABLED2K = VTPNODES['vlanTrunkPortVlansEnabled2k']['oid']
    TRUNKPORTVLANSENABLED3K = VTPNODES['vlanTrunkPortVlansEnabled3k']['oid']
    TRUNKPORTVLANSENABLED4K = VTPNODES['vlanTrunkPortVlansEnabled4k']['oid']

    TRUNKPORTSTATE = VTPNODES['vlanTrunkPortDynamicState']['oid']
    TRUNKSTATE_ON = 1
    TRUNKSTATE_OFF = 2
    TRUNKSTATE_AUTO = 4

    TRUNKPORTENCAPSULATION = VTPNODES['vlanTrunkPortEncapsulationType']['oid']
    ENCAPSULATION_DOT1Q = 4
    ENCAPSULATION_NEGOTIATE = 5

    def __init__(self, netbox, **kwargs):
        super(Cisco, self).__init__(netbox, **kwargs)
        self.vlan_oid = '1.3.6.1.4.1.9.9.68.1.2.2.1.2'
        self.write_mem_oid = '1.3.6.1.4.1.9.2.1.54.0'
        self.voice_vlan_oid = '1.3.6.1.4.1.9.9.68.1.5.1.1.1'

    def get_vlan(self, interface):
        return self._query_netbox(self.vlan_oid, interface.ifindex)

    def set_vlan(self, interface, vlan):
        """Set a new vlan for a specified interface,- and
        remove the previous vlan."""
        if_index = interface.ifindex
        try:
            vlan = int(vlan)
        except ValueError:
            raise TypeError('Not a valid vlan %s' % vlan)
        # Fetch current vlan
        fromvlan = self.get_vlan(interface)
        # fromvlan and vlan is the same, there's nothing to do
        if fromvlan == vlan:
            return None
        # Add port to vlan. This makes the port active on both old and new vlan
        status = None
        try:
            _logger.debug("setting vlan: if_index: %s i %s", if_index, vlan)
            status = self._set_netbox_value(self.vlan_oid, if_index, "i", vlan)
        except SnmpError as ex:
            # Ignore this exception,- some boxes want signed integer and
            # we do not know this beforehand.
            # If unsigned fail,- try with signed integer.
            _logger.debug("set_vlan with integer failed: Exception = %s", ex)
            _logger.debug("setting vlan: if_index: %s u %s", if_index, vlan)
            status = self._set_netbox_value(self.vlan_oid, if_index, "u", vlan)
        return status

    def set_native_vlan(self, interface, vlan):
        """Set native vlan on a trunk interface"""
        if_index = interface.ifindex
        try:
            self._set_netbox_value(self.TRUNKPORTNATIVEVLAN, if_index, 'i',
                                   vlan)
        except SnmpError:
            try:
                self._set_netbox_value(self.TRUNKPORTNATIVEVLAN, if_index,
                                       'u', vlan)
            except SnmpError:
                _logger.error('Setting native vlan on %s ifindex %s failed',
                              self.netbox, if_index)

    def get_cisco_voice_vlans(self):
        """Returns a dict of ifIndex:vmVoiceVlanId entries"""
        return {int(x): y for x, y in self._jog(self.voice_vlan_oid)}

    def set_cisco_voice_vlan(self, interface, voice_vlan):
        """Set a voice vlan using Cisco specific oid"""
        status = None
        try:
            voice_vlan = int(voice_vlan)
            status = self._set_netbox_value(
                self.voice_vlan_oid, interface.ifindex, 'i', voice_vlan)
        except SnmpError as error:
            _logger.error('Error setting voice vlan: %s', error)
        except ValueError as error:
            _logger.error('%s is not a valid voice vlan', voice_vlan)

        return status

    def disable_cisco_voice_vlan(self, interface):
        """Disable the Cisco Voice vlan on this interface"""
        status = None
        try:
            status = self._set_netbox_value(
                self.voice_vlan_oid, interface.ifindex, 'i', 4096)
        except SnmpError as error:
            _logger.error('Error disabling voice vlan: %s', error)

        return status

    def write_mem(self):
        """Use OLD-CISCO-SYS-MIB (v1) writeMem to write tomemory.
        Write configuration into non-volatile memory / erase config
        memory if 0."""
        handle = self._get_read_write_handle()
        return handle.set(self.write_mem_oid, 'i', 1)

    def get_available_vlans(self):
        """Fetch all vlans. Filter on operational and of type ethernet."""
        vlan_states = [self._extract_index_from_oid(oid) for oid, status in
                       self._bulkwalk(self.VTPVLANSTATE) if status == 1]
        vlan_types = [self._extract_index_from_oid(oid) for oid, vlantype in
                      self._bulkwalk(self.VTPVLANTYPE) if vlantype == 1]

        return list(set(vlan_states) & set(vlan_types))

    def get_native_and_trunked_vlans(self, interface):
        ifindex = interface.ifindex
        native_vlan = self._query_netbox(self.TRUNKPORTNATIVEVLAN, ifindex)

        blocks = [
            self._query_netbox(oid, ifindex) or ''
            for oid in (self.TRUNKPORTVLANSENABLED,
                        self.TRUNKPORTVLANSENABLED2K,
                        self.TRUNKPORTVLANSENABLED3K,
                        self.TRUNKPORTVLANSENABLED4K)]
        bitstring = "".join(value.ljust(CHARS_IN_1024_BITS, '\x00')
                            for value in blocks)

        bitvector = BitVector(bitstring)
        return native_vlan, bitvector.get_set_bits()

    def set_access(self, interface, access_vlan):
        """Set interface trunking to off and set encapsulation to negotiate"""
        _logger.debug("set_access: %s %s", interface, access_vlan)
        if self._is_trunk(interface):
            self._set_access_mode(interface)
        self.set_trunk_vlans(interface, [])
        self.set_native_vlan(interface, access_vlan)
        self.set_vlan(interface, access_vlan)
        interface.trunk = False # Make sure database is updated
        interface.vlan = access_vlan
        interface.save()

    def _set_access_mode(self, interface):
        _logger.debug("set_access_mode: %s", interface)
        self._set_netbox_value(self.TRUNKPORTSTATE, interface.ifindex, 'i',
                               self.TRUNKSTATE_OFF)
        interface.trunk = False
        interface.save()

    def set_trunk(self, interface, native_vlan, trunk_vlans):
        """Check for trunk, set native vlan, set trunk vlans"""
        _logger.debug("set_trunk: %s (%s, %s)",
                      interface, native_vlan, trunk_vlans)
        if not self._is_trunk(interface):
            self._set_trunk_mode(interface)

        self.set_trunk_vlans(interface, trunk_vlans)
        self.set_native_vlan(interface, native_vlan)
        self._save_trunk_interface(interface, native_vlan, trunk_vlans)

    def _set_trunk_mode(self, interface):
        _logger.debug("_set_trunk_mode %s", interface)
        ifindex = interface.ifindex
        self._set_netbox_value(self.TRUNKPORTSTATE, ifindex, 'i',
                               self.TRUNKSTATE_ON)
        # Set encapsulation to dot1Q TODO: Support other encapsulations
        self._set_netbox_value(self.TRUNKPORTENCAPSULATION, ifindex, 'i',
                               self.ENCAPSULATION_DOT1Q)
        interface.trunk = True
        interface.save()

    def set_trunk_vlans(self, interface, vlans):
        """Set trunk vlans

        Initialize a BitVector with all 4096 vlans set to 0. Then fill in all
        vlans. As Cisco has 4 different oids to set all vlans on the trunk,
        we divide this bitvector into one bitvector for each oid, and set
        each of those.

        """
        ifindex = interface.ifindex
        bitvector = BitVector(512 * '\000')  # initialize all-zero bitstring
        for vlan in vlans:
            bitvector[int(vlan)] = 1

        chunks = self._chunkify(bitvector, 4)

        for oid in [self.TRUNKPORTVLANSENABLED,
                    self.TRUNKPORTVLANSENABLED2K,
                    self.TRUNKPORTVLANSENABLED3K,
                    self.TRUNKPORTVLANSENABLED4K]:
            bitvector_chunk = next(chunks)
            try:
                self._set_netbox_value(oid, ifindex, 's',
                                       bitvector_chunk.to_bytes())
            except SnmpError as error:
                _logger.error('Error setting trunk vlans on %s ifindex %s: %s',
                              self.netbox, ifindex, error)
                break

    def _is_trunk(self, interface):
        state = int(self._query_netbox(self.TRUNKPORTSTATE, interface.ifindex))
        return state in [1, 5]


class HP(SNMPHandler):
    """A specialized class for handling ports in HP switches."""

    # From HP-DOT1X-EXTENSIONS-MIB
    # hpicfDot1xPaePortAuth return INTEGER { true(1), false(2) }
    dot1xPortAuth = '1.3.6.1.4.1.11.2.14.11.5.1.25.1.1.1.1.1'

    def __init__(self, netbox, **kwargs):
        super(HP, self).__init__(netbox, **kwargs)

    def is_dot1x_enabled(self, interface):
        """Returns True or False based on state of dot1x"""
        return int(self._query_netbox(
            self.dot1xPortAuth, interface.ifindex)) == 1

    def get_dot1x_enabled_interfaces(self):
        """Fetches a dict mapping ifindex to enabled state

        :returns: dict[ifindex, is_enabled]
        :rtype: dict[int, bool]
        """
        return {self._get_last_number(oid): state == 1
                for oid, state in self._bulkwalk(self.dot1xPortAuth)}


class H3C(SNMPHandler):
    """HP Comware Platform Software handler"""

    hh3cCfgOperateType = '1.3.6.1.4.1.25506.2.4.1.2.4.1.2'
    hh3cCfgOperateRowStatus = '1.3.6.1.4.1.25506.2.4.1.2.4.1.9'

    def __init__(self, netbox, **kwargs):
        super(H3C, self).__init__(netbox, **kwargs)

    def write_mem(self):
        """Use hh3c-config-man-mib to save running config to startup"""

        running_to_startup = 1
        create_and_go = 4

        # Find the next available row for configuring and store it as a suffix
        active_rows = [self._extract_index_from_oid(o[0])
                       for o in self._bulkwalk(self.hh3cCfgOperateRowStatus)]
        try:
            suffix = str(max(active_rows) + 1)
        except ValueError:
            suffix = '1'

        operation_type_oid = '.'.join([self.hh3cCfgOperateType, suffix])
        operation_status_oid = '.'.join([self.hh3cCfgOperateRowStatus, suffix])

        handle = self._get_read_write_handle()
        handle.multi_set([
            Snmp.PDUVarbind(operation_type_oid, 'i', running_to_startup),
            Snmp.PDUVarbind(operation_status_oid, 'i', create_and_go)
        ])


class Dell(SNMPHandler):
    """Dell INC handler

    Uses DNOS-SWITCHING-MIB
    """

    from nav.smidumps.dnos_switching_mib import MIB as mib

    PORT_MODE_ACCESS = 1
    PORT_MODE_TRUNK = 2
    PORT_MODE_GENERAL = 3

    PORT_MODE_OID = mib['nodes']['agentPortSwitchportMode']['oid']
    NATIVE_VLAN_ID = mib['nodes']['agentPortNativeVlanID']['oid']
    # Overriding members
    VlAN_OID = mib['nodes']['agentPortAccessVlanID']['oid']
    VLAN_EGRESS_PORTS = mib['nodes']['agentVlanSwitchportTrunkStaticEgressPorts']['oid']

    def __init__(self, netbox, **kwargs):
        super(Dell, self).__init__(netbox, **kwargs)

    def set_vlan(self, interface, vlan):
        baseport = interface.baseport
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

        self._set_netbox_value(self.VlAN_OID, baseport, "i", vlan)

    def set_access(self, interface, access_vlan):
        self._set_swport_mode(interface, self.PORT_MODE_ACCESS)
        self.set_vlan(interface, access_vlan)
        interface.vlan = access_vlan
        interface.trunk = False
        interface.save()

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

    def get_native_vlan(self, interface):
        baseport = interface.baseport
        return self._query_netbox(self.NATIVE_VLAN_ID, baseport)

    def set_native_vlan(self, interface, vlan):
        """Set native vlan on a trunk interface"""
        baseport = interface.baseport
        self._set_netbox_value(self.NATIVE_VLAN_ID, baseport, "i", vlan)


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

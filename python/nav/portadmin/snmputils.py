#
# Copyright 2010 (C) Norwegian University of Science and Technology
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
"""This is a utility library made especially for PortAdmin."""
import time
import logging

from nav.Snmp import Snmp
from nav.Snmp.errors import (SnmpError, UnsupportedSnmpVersionError,
                             NoSuchObjectError)
from nav.bitvector import BitVector


_logger = logging.getLogger("nav.portadmin.snmputils")


class FantasyVlan(object):
    """A container object for storing vlans for a netbox

    This object is needed because we mix "real" vlans that NAV know about
    and "fake" vlan that NAV does not know about but exists on the switch.
    They need to be compared and sorted, and this class does that.

    """

    def __init__(self, vlan, netident=None):
        self.vlan = vlan
        self.net_ident = netident

    def __unicode__(self):
        if self.net_ident:
            return "%s (%s)" % (self.vlan, self.net_ident)
        else:
            return str(self.vlan)

    def __hash__(self):
        return hash(self.vlan)

    def __cmp__(self, other):
        return cmp(self.vlan, other.vlan)

    def __eq__(self, other):
        return self.vlan == other.vlan


class SNMPHandler(object):
    """A basic class for SNMP-read and -write to switches."""
    IF_ALIAS_OID = '1.3.6.1.2.1.31.1.1.1.18'  # From IF-MIB
    VlAN_OID = '1.3.6.1.2.1.17.7.1.4.5.1.1'  # From Q-BRIDGE-MIB
    # List of all available vlans on this netbox as by the command "show vlans"
    AVAILABLE_VLANS_OID = '1.3.6.1.2.1.17.7.1.4.3.1.5'
    # oid for reading vlans om a stndard netbox (not cisco)
    DOT1Q_VLAN_STATIC_ROW_STATUS = '1.3.6.1.2.1.17.7.1.4.3.1.5'
    # List of all ports on a vlan as a hexstring (including native vlan)
    DOT1Q_VLAN_STATIC_EGRESS_PORTS = '1.3.6.1.2.1.17.7.1.4.3.1.2'
    IF_ADMIN_STATUS = '1.3.6.1.2.1.2.2.1.7'
    IF_OPER_STATUS = '1.3.6.1.2.1.2.2.1.8'

    netbox = None

    def __init__(self, netbox):
        self.netbox = netbox
        self.read_only_handle = None
        self.read_write_handle = None

    def __unicode__(self):
        return self.netbox.type.vendor.id

    def _bulkwalk(self, oid):
        """Walk all branches for the given oid."""
        handle = self._get_read_only_handle()
        result = []
        try:
            result = handle.bulkwalk(oid)
        except UnsupportedSnmpVersionError, unsup_ex:
            _logger.info("_bulkwalk: UnsupportedSnmpVersionError = %s" %
                         str(unsup_ex))
            try:
                result = handle.walk(oid)
            except SnmpError, ex:
                _logger.error("_bulkwalk: Exception = %s" % str(ex))
        return result

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
            self.read_only_handle = Snmp(self.netbox.ip, self.netbox.read_only,
                                         self.netbox.snmp_version)
        return self.read_only_handle

    def _query_netbox(self, oid, if_index):
        """Query the given interface."""
        handle = self._get_read_only_handle()
        result = None
        try:
            result = handle.get(self._get_query(oid, if_index))
        except NoSuchObjectError, no_such_ex:
            _logger.debug("_query_netbox: NoSuchObjectError = %s" %
                          str(no_such_ex))
        return result

    def _get_read_write_handle(self):
        """Get a read and write SNMP-handle."""
        if self.read_write_handle is None:
            self.read_write_handle = Snmp(self.netbox.ip,
                                          self.netbox.read_write,
                                          self.netbox.snmp_version)
        return self.read_write_handle

    def _set_netbox_value(self, oid, if_index, value_type, value):
        """Set a value for the given interface."""
        handle = self._get_read_write_handle()
        return handle.set(self._get_query(oid, if_index), value_type, value)

    def get_if_alias(self, if_index):
        """ Get alias on a specific interface """
        return self._query_netbox(self.IF_ALIAS_OID, if_index)

    def get_all_if_alias(self):
        """Get all aliases for all interfaces."""
        return self._bulkwalk(self.IF_ALIAS_OID)

    def set_if_alias(self, if_index, if_alias):
        """Set alias on a specific interface."""
        if isinstance(if_alias, unicode):
            if_alias = if_alias.encode('utf8')
        return self._set_netbox_value(self.IF_ALIAS_OID, if_index, "s",
                                      if_alias)

    def get_vlan(self, if_index):
        """Get vlan on a specific interface."""
        return self._query_netbox(self.VlAN_OID, if_index)

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
        return str(bit)

    def set_vlan(self, if_index, vlan):
        """Set a new vlan on the given interface and remove
        the previous vlan"""
        if isinstance(vlan, str) or isinstance(vlan, unicode):
            if vlan.isdigit():
                vlan = int(vlan)
        if not isinstance(vlan, int):
            raise TypeError('Illegal value for vlan: %s' % vlan)
        # Fetch current vlan
        fromvlan = self.get_vlan(if_index)
        # fromvlan and vlan is the same, there's nothing to do
        if fromvlan == vlan:
            return None
        # Add port to vlan. This makes the port active on both old and new vlan
        self._set_netbox_value(self.VlAN_OID, if_index, "u", vlan)
        # Remove port from list of ports on old vlan
        hexstring = self._query_netbox(self.DOT1Q_VLAN_STATIC_EGRESS_PORTS,
                                       fromvlan)
        modified_hexport = self._compute_octet_string(hexstring, if_index,
                                                      'disable')
        return self._set_netbox_value(self.DOT1Q_VLAN_STATIC_EGRESS_PORTS,
                                      fromvlan, 's', modified_hexport)

    def set_if_up(self, if_index):
        """Set interface.to up"""
        return self._set_netbox_value(self.IF_ADMIN_STATUS, if_index, "i", 1)

    def set_if_down(self, if_index):
        """Set interface.to down"""
        return self._set_netbox_value(self.IF_ADMIN_STATUS, if_index, "i", 2)

    def restart_if(self, if_index, wait=5):
        """ Take interface down and up.
            wait = number of seconds to wait between down and up."""
        wait = int(wait)
        self.set_if_down(if_index)
        time.sleep(wait)
        self.set_if_up(if_index)

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
        """Find all available vlans on this netbox"""
        available_vlans = []
        for swport in self.netbox.get_swports():
            available_vlans.extend(self._find_vlans_for_interface(swport))
        return list(set(available_vlans))

    def get_available_vlans(self):
        """Get available vlans from the box

        This is similar to the terminal command "show vlans"

        """
        return [self._extract_index_from_oid(oid)
                for oid, status in self._bulkwalk(self.AVAILABLE_VLANS_OID)
                if status == 1]

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
        native_vlan = self.get_vlan(interface.ifindex)

        bitvector_index = interface.ifindex - 1
        vlans = []
        for vlan in self.get_available_vlans():
            if vlan == native_vlan:
                continue
            octet_string = self._query_netbox(
                self.DOT1Q_VLAN_STATIC_EGRESS_PORTS, vlan)
            bitvector = BitVector(octet_string)
            if bitvector[bitvector_index]:
                vlans.append(vlan)
        return native_vlan, vlans

    def set_trunk_vlans(self, ifindex, vlans):
        """Trunk the vlans on interface

        Egress_Ports includes native vlan. Be sure to not alter that.

        Get all available vlans. For each available vlan fetch list of
        interfaces that forward this vlan. Set or remove the interface from
        this list based on if it is in the vlans list.

        """
        native_vlan = self.get_vlan(ifindex)
        bitvector_index = ifindex - 1

        vlans = [int(vlan) for vlan in vlans]

        for available_vlan in self.get_available_vlans():
            if native_vlan == available_vlan:
                continue

            octet_string = self._query_netbox(
                self.DOT1Q_VLAN_STATIC_EGRESS_PORTS, available_vlan)
            bitvector = BitVector(octet_string)
            if available_vlan in vlans:
                bitvector[bitvector_index] = 1
            else:
                bitvector[bitvector_index] = 0

            _logger.info(bitvector.get_set_bits())
            # self._set_netbox_value(self.DOT1Q_VLAN_STATIC_EGRESS_PORTS,
            #                        available_vlan, 's', str(b))

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


class Cisco(SNMPHandler):
    """A specialized class for handling ports in CISCO switches."""

    from nav.smidumps.cisco_vtp_mib import MIB as vtb_mib

    def __init__(self, netbox):
        super(Cisco, self).__init__(netbox)
        self.vlan_oid = '1.3.6.1.4.1.9.9.68.1.2.2.1.2'
        self.write_mem_oid = '1.3.6.1.4.1.9.2.1.54.0'

    def set_vlan(self, if_index, vlan):
        """Set a new vlan for a specified interface,- and
        remove the previous vlan."""
        if isinstance(vlan, str) or isinstance(vlan, unicode):
            if vlan.isdigit():
                vlan = int(vlan)
        if not isinstance(vlan, int):
            raise TypeError('Illegal value for vlan: %s' % vlan)
        # Fetch current vlan
        fromvlan = self.get_vlan(if_index)
        # fromvlan and vlan is the same, there's nothing to do
        if fromvlan == vlan:
            return None
        # Add port to vlan. This makes the port active on both old and new vlan
        status = None
        try:
            status = self._set_netbox_value(self.vlan_oid, if_index, "u", vlan)
        except SnmpError, ex:
            # Ignore this exception,- some boxes want signed integer and
            # we do not know this beforehand.
            # If unsigned fail,- try with signed integer.
            _logger.debug("set_vlan: Exception = %s" % str(ex))
            status = self._set_netbox_value(self.vlan_oid, if_index, "i", vlan)
        return status

    def write_mem(self):
        """Use OLD-CISCO-SYS-MIB (v1) writeMem to write tomemory.
        Write configuration into non-volatile memory / erase config
        memory if 0."""
        handle = self._get_read_write_handle()
        return handle.set(self.write_mem_oid, 'i', 1)

    def get_available_vlans(self):

        vtp_vlan_state = self._get_oid('vtpVlanState')
        return [self._extract_index_from_oid(oid) for oid, status in
                self._bulkwalk(vtp_vlan_state) if status == 1]

    def get_native_and_trunked_vlans(self, interface):
        ifindex = interface.ifindex
        vlan_trunk_port_native_vlan = self._get_oid('vlanTrunkPortNativeVlan')
        native_vlan = self._query_netbox(vlan_trunk_port_native_vlan, ifindex)

        octetstrings = ""
        for oid in [self._get_oid('vlanTrunkPortVlansEnabled'),
                    self._get_oid('vlanTrunkPortVlansEnabled2k'),
                    self._get_oid('vlanTrunkPortVlansEnabled3k'),
                    self._get_oid('vlanTrunkPortVlansEnabled4k')]:
            octetstring = self._query_netbox(oid, ifindex)
            if octetstring:
                octetstrings += octetstring
            else:
                break

        bitvector = BitVector(octetstrings)

        return native_vlan, bitvector.get_set_bits()

    def _get_oid(self, key):
        return self.vtb_mib['nodes'][key]['oid']


class HP(SNMPHandler):
    """A specialized class for handling ports in HP switches."""
    def __init__(self, netbox):
        super(HP, self).__init__(netbox)

VENDOR_CISCO = 9
VENDOR_HP = 11


class SNMPFactory(object):
    """Factory class for returning SNMP-handles depending
    on a netbox' vendor identification."""
    @classmethod
    def get_instance(cls, netbox):
        """Get and SNMP-handle depending on vendor type"""
        vendor_id = netbox.type.get_enterprise_id()
        if (vendor_id == VENDOR_CISCO):
            return Cisco(netbox)
        if (vendor_id == VENDOR_HP):
            return HP(netbox)
        return SNMPHandler(netbox)

    def __init__(self):
        pass

#
# Copyright (C) 2011-2015, 2020, 2021 Uninett AS
# Copyright (C) 2022 Sikt
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
from functools import wraps
from operator import attrgetter
import logging
from typing import Any, Sequence

from nav.Snmp.profile import get_snmp_session_for_profile
from nav.Snmp import safestring, OID
from nav.Snmp.errors import (
    UnsupportedSnmpVersionError,
    SnmpError,
    NoSuchObjectError,
    TimeOutException,
)
from nav.bitvector import BitVector
from nav.models import manage

from nav.models.manage import Vlan, SwPortAllowedVlan, Interface
from nav.portadmin.handlers import (
    ManagementError,
    ManagementHandler,
    DeviceNotConfigurableError,
    NoResponseError,
    ProtocolError,
)
from nav.portadmin.vlan import FantasyVlan
from nav.smidumps import get_mib


_logger = logging.getLogger(__name__)


def translate_protocol_errors(func):
    """Decorator that translates SNMPErrors into PortAdmin ProtocolErrors.

    The PortAdmin API will handle ProtocolErrors gracefully, but other exceptions
    will bleed through and be handled by Django's 500 handler.
    """

    @wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SnmpError as error:
            logmsg = "An SnmpError was raised:"
            if args and isinstance(args[0], SNMPHandler):
                sysname = args[0].netbox.sysname
                logmsg = f"{sysname}: {logmsg}"
            _logger.exception(logmsg)
            raise ProtocolError(error)

    return _wrapper


class NoReadWriteManagementProfileError(ManagementError):
    """No read-write management profile set on switch"""

    pass


class NoReadOnlyManagementProfileError(ManagementError):
    """No read-only management profile set on switch"""

    pass


class InvalidManagementProfileError(ManagementError):
    """Some attribute of management profile is incorrectly set"""

    pass


class SNMPHandler(ManagementHandler):
    """Implements PortAdmin management functions for SNMP-enabled switches"""

    QBRIDGENODES = get_mib('Q-BRIDGE-MIB')['nodes']

    SYSOBJECTID = '.1.3.6.1.2.1.1.2.0'
    SYSLOCATION = '1.3.6.1.2.1.1.6.0'
    IF_ALIAS_OID = '1.3.6.1.2.1.31.1.1.1.18'  # From IF-MIB
    IF_NAME_OID = '1.3.6.1.2.1.31.1.1.1.1'
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
    CURRENT_VLAN_EGRESS_PORTS = (
        QBRIDGENODES['dot1qVlanCurrentEgressPorts']['oid'] + '.0'
    )

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

    def _bulkwalk(self, oid: str):
        """Performs a GETBULK walk operation on `oid`, downgrading to a regular
        GETNEXT-based walk if the active SNMP version doesn't support the GETBULK
        operation.

        """
        handle = self._get_read_only_handle()
        result = []
        try:
            result = handle.bulkwalk(oid)
        except UnsupportedSnmpVersionError as unsup_ex:
            _logger.info("_bulkwalk: UnsupportedSnmpVersionError = %s", unsup_ex)
            try:
                result = handle.walk(oid)
            except SnmpError as ex:
                _logger.error("_bulkwalk: Exception = %s", ex)
        except TimeOutException as error:
            raise NoResponseError("Timed out") from error
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
            profile = self.netbox.get_preferred_snmp_management_profile()

            if not profile:
                raise NoReadOnlyManagementProfileError

            self.read_only_handle = get_snmp_session_for_profile(profile)(
                host=self.netbox.ip,
                retries=self.retries,
                timeout=self.timeout,
            )
        return self.read_only_handle

    def _query_netbox(self, oid, if_index):
        """Query the given interface."""
        handle = self._get_read_only_handle()
        result = None
        try:
            result = handle.get(self._get_query(oid, if_index))
        except NoSuchObjectError as no_such_ex:
            _logger.debug("_query_netbox: NoSuchObjectError = %s", no_such_ex)
        except TimeoutError as error:
            raise NoResponseError("Timed out") from error
        except SnmpError as error:
            raise ProtocolError("SNMP error") from error
        return result

    def _get_read_write_handle(self):
        """Get a read and write SNMP-handle.

        :rtype: nav.Snmp.Snmp
        """
        if self.read_write_handle is None:
            profile = self.netbox.get_preferred_snmp_management_profile(
                require_write=True
            )
            self.read_write_handle = get_snmp_session_for_profile(profile)(
                host=self.netbox.ip,
                retries=self.retries,
                timeout=self.timeout,
            )
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
            yield BitVector.from_hex(hexes[i : i + chunksize])

    def test_read(self):
        """Test if SNMP read works"""
        handle = self._get_read_only_handle()
        try:
            handle.get(self.SYSOBJECTID)
            return True
        except SnmpError:
            return False

    def test_write(self):
        """Test if SNMP write works"""
        handle = self._get_read_write_handle()
        try:
            value = handle.get(self.SYSLOCATION)
            handle.set(self.SYSLOCATION, 's', value)
            return True
        except SnmpError:
            return False

    @translate_protocol_errors
    def get_interfaces(
        self, interfaces: Sequence[manage.Interface] = None
    ) -> list[dict[str, Any]]:
        names = self._get_interface_names()
        aliases = self._get_all_ifaliases()
        oper = dict(self._get_all_interfaces_oper_status())
        admin = dict(self._get_all_interfaces_admin_status())
        vlans = self._get_all_interfaces_vlan()

        result = [
            {
                "snmp-index": index,
                "name": names.get(index),
                "description": aliases.get(index),
                "oper": oper.get(index),
                "admin": admin.get(index),
                "vlan": vlans.get(index),
            }
            for index in names
        ]
        return result

    def _get_interface_names(self) -> dict[int, str]:
        """Returns a mapping of interface indexes to ifName values"""
        return {
            OID(index)[-1]: safestring(value)
            for index, value in self._bulkwalk(self.IF_NAME_OID)
        }

    def _get_all_ifaliases(self):
        """Get all aliases for all interfaces.

        :returns: A dict describing {ifIndex: ifAlias}
        """
        return {
            OID(oid)[-1]: safestring(value)
            for oid, value in self._bulkwalk(self.IF_ALIAS_OID)
        }

    @translate_protocol_errors
    def set_interface_description(self, interface, description):
        if isinstance(description, str):
            description = description.encode("utf8")
        return self._set_netbox_value(
            self.IF_ALIAS_OID, interface.ifindex, "s", description
        )

    @translate_protocol_errors
    def get_interface_native_vlan(self, interface):
        return self._query_netbox(self.VlAN_OID, interface.baseport)

    def _get_all_interfaces_vlan(self):
        """Retrieves the untagged VLAN value for every interface.

        :returns: A dict describing {ifIndex: VLAN_TAG}
        """
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

    @translate_protocol_errors
    def set_vlan(self, interface, vlan):
        base_port = interface.baseport
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
        # Add port to vlan. This makes the port active on both old and new vlan
        _logger.debug('Enabling port %s on vlan %s', base_port, vlan)
        self._set_netbox_value(self.VlAN_OID, base_port, "u", vlan)
        # Remove port from list of ports on old vlan
        hexstring = self._query_netbox(self.VLAN_EGRESS_PORTS, fromvlan)
        modified_hexport = self._compute_octet_string(hexstring, base_port, 'disable')
        _logger.debug('Disabling port %s on old vlan %s', base_port, fromvlan)
        return self._set_netbox_value(
            self.VLAN_EGRESS_PORTS, fromvlan, 's', modified_hexport
        )

    @translate_protocol_errors
    def set_native_vlan(self, interface, vlan):
        self.set_vlan(interface, vlan)

    @translate_protocol_errors
    def set_interface_up(self, interface):
        return self._set_netbox_value(
            self.IF_ADMIN_STATUS, interface.ifindex, "i", self.IF_ADMIN_STATUS_UP
        )

    @translate_protocol_errors
    def set_interface_down(self, interface):
        return self._set_netbox_value(
            self.IF_ADMIN_STATUS, interface.ifindex, "i", self.IF_ADMIN_STATUS_DOWN
        )

    def commit_configuration(self):
        pass

    @translate_protocol_errors
    def get_interface_admin_status(self, interface):
        return self._query_netbox(self.IF_ADMIN_STATUS, interface.ifindex)

    def _get_if_stats(self, stats):
        """Make a list with tuples.  Each tuple contain
        interface-index and corresponding status-value"""
        available_stats = []
        for if_index, stat in stats:
            if_index = OID(if_index)[-1]
            if isinstance(if_index, int):
                available_stats.append((if_index, stat))
        return available_stats

    def _get_all_interfaces_admin_status(self):
        """Walk all ports and get their administration status."""
        if_admin_stats = self._bulkwalk(self.IF_ADMIN_STATUS)
        return self._get_if_stats(if_admin_stats)

    def _get_all_interfaces_oper_status(self):
        """Walk all ports and get their operational status."""
        if_oper_stats = self._bulkwalk(self.IF_OPER_STATUS)
        return self._get_if_stats(if_oper_stats)

    @translate_protocol_errors
    def get_netbox_vlans(self):
        numerical_vlans = self.get_netbox_vlan_tags()
        vlan_objects = Vlan.objects.filter(
            swport_vlans__interface__netbox=self.netbox
        ).distinct()
        vlans = []
        for numerical_vlan in numerical_vlans:
            try:
                vlan_object = vlan_objects.get(vlan=numerical_vlan)
            except (Vlan.DoesNotExist, Vlan.MultipleObjectsReturned):
                fantasy_vlan = FantasyVlan(numerical_vlan)
            else:
                fantasy_vlan = FantasyVlan(
                    numerical_vlan,
                    netident=vlan_object.net_ident,
                    descr=vlan_object.description,
                )
            vlans.append(fantasy_vlan)

        return sorted(list(set(vlans)), key=attrgetter('vlan'))

    @translate_protocol_errors
    def get_netbox_vlan_tags(self):
        if self.available_vlans is None:
            self.available_vlans = [
                OID(oid)[-1]
                for oid, status in self._bulkwalk(self.VLAN_ROW_STATUS)
                if status == 1
            ]
        return self.available_vlans

    @translate_protocol_errors
    def get_native_and_trunked_vlans(self, interface):
        native_vlan = self.get_interface_native_vlan(interface)

        bitvector_index = interface.baseport - 1
        vlans = []
        for vlan in self.get_netbox_vlan_tags():
            if vlan == native_vlan:
                continue
            octet_string = (
                self._query_netbox(self.CURRENT_VLAN_EGRESS_PORTS, vlan) or b''
            )
            bitvector = BitVector(octet_string)

            try:
                if bitvector[bitvector_index]:
                    vlans.append(vlan)
            except IndexError:
                _logger.error('Baseport index was out of bounds for StaticEgressPorts')

        return native_vlan, vlans

    def _get_egress_interfaces_as_bitvector(self, vlan):
        octet_string = self._query_netbox(self.CURRENT_VLAN_EGRESS_PORTS, vlan)
        return BitVector(octet_string)

    @translate_protocol_errors
    def set_trunk_vlans(self, interface: Interface, vlans: Sequence[int]):
        """Trunk vlans on this interface.

        :param interface: The interface to set to trunk mode.
        :param vlans: The list of VLAN tags to allow on this trunk.
        """
        # This procedure is somewhat complex using the Q-BRIDGE-MIB. For each
        # configured VLAN there is a list of ports (encoded as an octet string where
        # each bit represents a port) with an active egress on this VLAN, so making
        # this configuration change on a single port means updating the egress port
        # list on every VLAN to remove from the port, and for every VLAN to add.
        #
        # Note that the egress port list contains both tagged and untagged/native vlans.
        #
        base_port = interface.baseport
        native_vlan = self.get_interface_native_vlan(interface)
        bitvector_index = base_port - 1

        _logger.debug(
            'base_port: %s, native_vlan: %s, trunk_vlans: %s',
            base_port,
            native_vlan,
            vlans,
        )

        vlans = [int(vlan) for vlan in vlans]

        for available_vlan in self.get_netbox_vlan_tags():
            if native_vlan == available_vlan:
                _logger.debug(
                    'native vlan (%s) == available vlan (%s) - skip',
                    native_vlan,
                    available_vlan,
                )
                continue

            bitvector = self._get_egress_interfaces_as_bitvector(available_vlan)

            original_value = bitvector[bitvector_index]
            if available_vlan in vlans:
                bitvector[bitvector_index] = 1
            else:
                bitvector[bitvector_index] = 0

            if bitvector[bitvector_index] != original_value:
                _logger.debug(
                    'vlan %(vlan)s: state for port %(port)s changed',
                    {'port': base_port, 'vlan': available_vlan},
                )
                self._set_egress_interfaces(available_vlan, bitvector)

    def _set_egress_interfaces(self, vlan, bitvector):
        try:
            _logger.debug(
                'Setting egress ports for vlan %s, set bits: %s',
                vlan,
                bitvector.get_set_bits(),
            )
            self._set_netbox_value(
                self.VLAN_EGRESS_PORTS, vlan, 's', bitvector.to_bytes()
            )
        except SnmpError as error:
            _logger.error("Error setting egress ports: %s", error)
            raise error

    @translate_protocol_errors
    def set_access(self, interface, access_vlan):
        _logger.debug(
            'Setting access mode vlan %s on interface %s', access_vlan, interface
        )
        self.set_vlan(interface, access_vlan)
        self.set_trunk_vlans(interface, [])
        interface.vlan = access_vlan
        interface.trunk = False
        interface.save()

    @translate_protocol_errors
    def set_trunk(self, interface, native_vlan, trunk_vlans):
        self.set_vlan(interface, native_vlan)
        self.set_trunk_vlans(interface, trunk_vlans)
        self._save_trunk_interface(interface, native_vlan, trunk_vlans)

    @translate_protocol_errors
    def _save_trunk_interface(self, interface, native_vlan, trunk_vlans):
        interface.vlan = native_vlan
        interface.trunk = True
        self._set_interface_hex(interface, trunk_vlans)
        interface.save()

    @staticmethod
    def _set_interface_hex(interface, trunk_vlans):
        try:
            allowedvlan = interface.swport_allowed_vlan
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
        try:
            return int(handle.get(self.dot1xPaeSystemAuthControl)) == 1
        except TimeOutException as error:
            raise NoResponseError("Timed out") from error
        except SnmpError as error:
            raise ProtocolError("SNMP error") from error

    def raise_if_not_configurable(self):
        if not self.netbox.get_preferred_snmp_management_profile(require_write=True):
            raise DeviceNotConfigurableError(
                "No writeable SNMP management profile set for this device, "
                "changes cannot be saved"
            )

    # These are not relevant for this generic subclass
    get_cisco_voice_vlans = None
    set_cisco_voice_vlan = None
    enable_cisco_cdp = None
    disable_cisco_voice_vlan = None
    disable_cisco_cdp = None

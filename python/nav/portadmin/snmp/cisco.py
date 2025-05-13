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
"""Cisco specific PortAdmin SNMP handling"""

import logging
from typing import Optional, Sequence

from nav.Snmp.errors import SnmpError
from nav.bitvector import BitVector
from nav.oids import OID
from nav.portadmin.snmp.base import SNMPHandler, translate_protocol_errors
from nav.smidumps import get_mib
from nav.enterprise.ids import VENDOR_ID_CISCOSYSTEMS
from nav.portadmin.handlers import (
    PoeState,
    POEStateNotSupportedError,
    POENotSupportedError,
)
from nav.models import manage


_logger = logging.getLogger(__name__)


class Cisco(SNMPHandler):
    """A specialized class for handling ports in CISCO switches."""

    # Cisco sysObjectIDs under this tree are not normal Cisco products and should
    # probably not be handled by this handler
    OTHER_ENTERPRISES = OID('.1.3.6.1.4.1.9.6')

    VENDOR = VENDOR_ID_CISCOSYSTEMS

    VTPNODES = get_mib('CISCO-VTP-MIB')['nodes']
    PAENODES = get_mib('CISCO-PAE-MIB')['nodes']
    POENODES = get_mib('CISCO-POWER-ETHERNET-EXT-MIB')['nodes']

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

    dot1xPortAuth = PAENODES['cpaePortCapabilitiesEnabled']['oid']
    DOT1X_AUTHENTICATOR = 0b10000000
    DOT1X_SUPPLICANT = 0b01000000

    POEENABLE = POENODES['cpeExtPsePortEnable']['oid']
    POE_AUTO = PoeState(state=1, name="AUTO")
    POE_STATIC = PoeState(state=2, name="STATIC")
    POE_LIMIT = PoeState(state=3, name="LIMIT")
    POE_DISABLE = PoeState(state=4, name="DISABLE")

    POE_OPTIONS = [
        POE_AUTO,
        POE_STATIC,
        POE_LIMIT,
        POE_DISABLE,
    ]

    def __init__(self, netbox, **kwargs):
        super(Cisco, self).__init__(netbox, **kwargs)
        self.vlan_oid = '1.3.6.1.4.1.9.9.68.1.2.2.1.2'
        self.write_mem_oid = '1.3.6.1.4.1.9.2.1.54.0'
        self.voice_vlan_oid = '1.3.6.1.4.1.9.9.68.1.5.1.1.1'
        self.cdp_oid = '1.3.6.1.4.1.9.9.23.1.1.1.1.2'

    @classmethod
    def can_handle(cls, netbox: manage.Netbox) -> bool:
        """Returns True if this handler can handle this netbox"""
        if netbox.type and cls.OTHER_ENTERPRISES.is_a_prefix_of(
            netbox.type.sysobjectid
        ):
            return False
        return super().can_handle(netbox)

    @translate_protocol_errors
    def get_interface_native_vlan(self, interface):
        return self._query_netbox(self.vlan_oid, interface.ifindex)

    @translate_protocol_errors
    def set_vlan(self, interface, vlan):
        """Set a new vlan for a specified interface,- and
        remove the previous vlan."""
        if_index = interface.ifindex
        try:
            vlan = int(vlan)
        except ValueError:
            raise TypeError('Not a valid vlan %s' % vlan)
        # Fetch current vlan
        fromvlan = self.get_interface_native_vlan(interface)
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

    @translate_protocol_errors
    def set_native_vlan(self, interface, vlan):
        """Set native vlan on a trunk interface"""
        if_index = interface.ifindex
        try:
            self._set_netbox_value(self.TRUNKPORTNATIVEVLAN, if_index, 'i', vlan)
        except SnmpError:
            try:
                self._set_netbox_value(self.TRUNKPORTNATIVEVLAN, if_index, 'u', vlan)
            except SnmpError:
                _logger.error(
                    'Setting native vlan on %s ifindex %s failed', self.netbox, if_index
                )
                raise

    @translate_protocol_errors
    def get_cisco_voice_vlans(self):
        """Returns a dict of ifIndex:vmVoiceVlanId entries"""
        return {int(x): y for x, y in self._jog(self.voice_vlan_oid)}

    @translate_protocol_errors
    def set_cisco_voice_vlan(self, interface, voice_vlan):
        """Set a voice vlan using Cisco specific oid"""
        status = None
        try:
            voice_vlan = int(voice_vlan)
            status = self._set_netbox_value(
                self.voice_vlan_oid, interface.ifindex, 'i', voice_vlan
            )
        except SnmpError as error:
            _logger.error('Error setting voice vlan: %s', error)
        except ValueError:
            _logger.error('%s is not a valid voice vlan', voice_vlan)
            raise

        return status

    @translate_protocol_errors
    def enable_cisco_cdp(self, interface):
        """Enable CDP using Cisco specific oid"""
        try:
            return self._set_netbox_value(self.cdp_oid, interface.ifindex, 'i', 1)
        except ValueError:
            _logger.error('%s is not a valid option for cdp', 1)
            raise

    @translate_protocol_errors
    def disable_cisco_voice_vlan(self, interface):
        """Disable the Cisco Voice vlan on this interface"""
        return self._set_netbox_value(self.voice_vlan_oid, interface.ifindex, 'i', 4096)

    @translate_protocol_errors
    def disable_cisco_cdp(self, interface):
        """Disable CDP using Cisco specific oid"""
        try:
            return self._set_netbox_value(self.cdp_oid, interface.ifindex, 'i', 2)
        except ValueError:
            _logger.error('%s is not a valid option for cdp', 2)
            raise

    @translate_protocol_errors
    def commit_configuration(self):
        """Use OLD-CISCO-SYS-MIB (v1) writeMem to write tomemory.
        Write configuration into non-volatile memory / erase config
        memory if 0."""
        handle = self._get_read_write_handle()
        return handle.set(self.write_mem_oid, 'i', 1)

    @translate_protocol_errors
    def get_netbox_vlan_tags(self):
        """Fetch all vlans. Filter on operational and of type ethernet."""
        vlan_states = [
            OID(oid)[-1]
            for oid, status in self._bulkwalk(self.VTPVLANSTATE)
            if status == 1
        ]
        vlan_types = [
            OID(oid)[-1]
            for oid, vlantype in self._bulkwalk(self.VTPVLANTYPE)
            if vlantype == 1
        ]

        return list(set(vlan_states) & set(vlan_types))

    @translate_protocol_errors
    def get_native_and_trunked_vlans(self, interface):
        ifindex = interface.ifindex
        native_vlan = self._query_netbox(self.TRUNKPORTNATIVEVLAN, ifindex)

        blocks = [
            self._query_netbox(oid, ifindex) or b''
            for oid in (
                self.TRUNKPORTVLANSENABLED,
                self.TRUNKPORTVLANSENABLED2K,
                self.TRUNKPORTVLANSENABLED3K,
                self.TRUNKPORTVLANSENABLED4K,
            )
        ]
        bitstring = b"".join(
            value.ljust(CHARS_IN_1024_BITS, b'\x00') for value in blocks
        )

        bitvector = BitVector(bitstring)
        return native_vlan, bitvector.get_set_bits()

    @translate_protocol_errors
    def set_access(self, interface, access_vlan):
        """Set interface trunking to off and set encapsulation to negotiate"""
        _logger.debug("set_access: %s %s", interface, access_vlan)
        if self._is_trunk(interface):
            self._set_access_mode(interface)
        self.set_trunk_vlans(interface, [])
        self.set_native_vlan(interface, access_vlan)
        self.set_vlan(interface, access_vlan)
        interface.trunk = False  # Make sure database is updated
        interface.vlan = access_vlan
        interface.save()

    def _set_access_mode(self, interface):
        _logger.debug("set_access_mode: %s", interface)
        self._set_netbox_value(
            self.TRUNKPORTSTATE, interface.ifindex, 'i', self.TRUNKSTATE_OFF
        )
        interface.trunk = False
        interface.save()

    @translate_protocol_errors
    def set_trunk(self, interface, native_vlan, trunk_vlans):
        """Check for trunk, set native vlan, set trunk vlans"""
        _logger.debug("set_trunk: %s (%s, %s)", interface, native_vlan, trunk_vlans)
        if not self._is_trunk(interface):
            self._set_trunk_mode(interface)

        self.set_trunk_vlans(interface, trunk_vlans)
        self.set_native_vlan(interface, native_vlan)
        self._save_trunk_interface(interface, native_vlan, trunk_vlans)

    def _set_trunk_mode(self, interface):
        _logger.debug("_set_trunk_mode %s", interface)
        ifindex = interface.ifindex
        self._set_netbox_value(self.TRUNKPORTSTATE, ifindex, 'i', self.TRUNKSTATE_ON)
        # Set encapsulation to dot1Q TODO: Support other encapsulations
        self._set_netbox_value(
            self.TRUNKPORTENCAPSULATION, ifindex, 'i', self.ENCAPSULATION_DOT1Q
        )
        interface.trunk = True
        interface.save()

    @translate_protocol_errors
    def set_trunk_vlans(self, interface, vlans):
        """Set trunk vlans

        Initialize a BitVector with all 4096 vlans set to 0. Then fill in all
        vlans. As Cisco has 4 different oids to set all vlans on the trunk,
        we divide this bitvector into one bitvector for each oid, and set
        each of those.

        """
        ifindex = interface.ifindex
        bitvector = BitVector(512 * b'\x00')  # initialize all-zero bitstring
        for vlan in vlans:
            bitvector[int(vlan)] = 1

        chunks = self._chunkify(bitvector, 4)

        for oid in [
            self.TRUNKPORTVLANSENABLED,
            self.TRUNKPORTVLANSENABLED2K,
            self.TRUNKPORTVLANSENABLED3K,
            self.TRUNKPORTVLANSENABLED4K,
        ]:
            bitvector_chunk = next(chunks)
            try:
                self._set_netbox_value(oid, ifindex, 's', bitvector_chunk.to_bytes())
            except SnmpError as error:
                _logger.error(
                    'Error setting trunk vlans on %s ifindex %s: %s',
                    self.netbox,
                    ifindex,
                    error,
                )
                raise

    def _is_trunk(self, interface):
        state = int(self._query_netbox(self.TRUNKPORTSTATE, interface.ifindex))
        return state in [1, 5]

    @translate_protocol_errors
    def is_dot1x_enabled(self, interface):
        """Returns True or False based on state of dot1x"""
        return (
            self._query_netbox(self.dot1xPortAuth, interface.ifindex)[0]
            & self.DOT1X_AUTHENTICATOR
        )

    @translate_protocol_errors
    def get_dot1x_enabled_interfaces(self):
        _logger.error("Querying for dot1x enabled interfaces on Cisco")
        names = self._get_interface_names()
        return {
            names.get(OID(oid)[-1]): state[0] & self.DOT1X_AUTHENTICATOR
            for oid, state in self._bulkwalk(self.dot1xPortAuth)
        }

    def get_poe_state_options(self) -> Sequence[PoeState]:
        """Returns the available options for enabling/disabling PoE on this netbox"""
        return self.POE_OPTIONS

    @translate_protocol_errors
    def set_poe_state(self, interface: manage.Interface, state: PoeState):
        """Set state for enabling/disabling PoE on this interface.
        Available options should be retrieved using `get_poe_state_options`
        """
        unit_number, interface_number = self._get_poe_indexes_for_interface(interface)
        oid_with_unit_number = self.POEENABLE + OID((unit_number,))
        try:
            self._set_netbox_value(
                oid_with_unit_number, interface_number, 'i', state.state
            )
        except SnmpError as error:
            _logger.error('Error setting poe state: %s', error)
            raise
        except ValueError:
            _logger.error('%s is not a valid option for poe state', state)
            raise

    def _get_poe_indexes_for_interface(
        self, interface: manage.Interface
    ) -> tuple[int, int]:
        """Returns the unit number and interface number for the given interface"""
        try:
            poeport = manage.POEPort.objects.get(interface=interface)
        except manage.POEPort.DoesNotExist:
            raise POENotSupportedError(
                "This interface does not have PoE indexes defined"
            )
        unit_number = poeport.poegroup.index
        interface_number = poeport.index
        return unit_number, interface_number

    def get_poe_states(
        self, interfaces: Optional[Sequence[manage.Interface]] = None
    ) -> dict[str, Optional[PoeState]]:
        """Retrieves current PoE state for interfaces on this device.

        :param interfaces: Optional sequence of interfaces to filter for, as fetching
                           data for all interfaces may be a waste of time if only a
                           single interface is needed. If this parameter is omitted,
                           the default behavior is to filter on all Interface objects
                           registered for this device.
        :returns: A dict mapping interfaces to their discovered PoE state.
                  The key matches the `ifname` attribute for the related
                  Interface object.
                  The value will be None if the interface does not support PoE.
        """
        if not interfaces:
            interfaces = self.netbox.interfaces
        states_dict = {}
        for interface in interfaces:
            try:
                state = self._get_poe_state_for_single_interface(interface)
            except POENotSupportedError:
                state = None
            states_dict[interface.ifname] = state
        return states_dict

    @translate_protocol_errors
    def _get_poe_state_for_single_interface(
        self, interface: manage.Interface
    ) -> PoeState:
        """Retrieves current PoE state for given the given interface"""
        unit_number, interface_number = self._get_poe_indexes_for_interface(interface)
        oid_with_unit_number = self.POEENABLE + OID((unit_number,))
        state_value = self._query_netbox(oid_with_unit_number, interface_number)
        if state_value is None:
            raise POENotSupportedError("This interface does not support PoE")
        for state in self.get_poe_state_options():
            if state.state == state_value:
                return state
        raise POEStateNotSupportedError(f"Unknown PoE state {state_value}")


CHARS_IN_1024_BITS = 128

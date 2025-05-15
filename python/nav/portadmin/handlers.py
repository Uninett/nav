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
"""Interface definition for PortAdmin management handlers"""

import time
from typing import Any, Optional, Sequence, Union
import logging
from dataclasses import dataclass

from nav.models import manage
from nav.portadmin.vlan import FantasyVlan


_logger = logging.getLogger(__name__)


@dataclass
class PoeState:
    """Class for defining PoE states.
    `state` is the value used on the device itself.
    `name` is a human readable name for the state
    """

    state: Union[str, int]
    name: str


class ManagementHandler:
    """Defines a common interface for all types of PortAdmin management handlers.

    This defines the set of methods that a handler class may be expected by PortAdmin
    to provide, regardless of the underlying management protocol implemented by such
    a class.
    """

    VENDOR = None

    def __init__(self, netbox: manage.Netbox, **kwargs):
        self.netbox = netbox

    @classmethod
    def can_handle(cls, netbox: manage.Netbox) -> bool:
        """Returns True if this handler can handle the given netbox"""
        return netbox.type and netbox.type.get_enterprise_id() == cls.VENDOR

    def set_interface_description(self, interface: manage.Interface, description: str):
        """Configures a single interface's description, AKA the ifalias value"""
        raise NotImplementedError

    def get_interface_native_vlan(self, interface: manage.Interface) -> int:
        """Retrieves the native/untagged VLAN configured on interface"""
        raise NotImplementedError

    def get_interfaces(
        self, interfaces: Sequence[manage.Interface] = None
    ) -> list[dict[str, Any]]:
        """Retrieves running configuration switch ports on the device.

        :param interfaces: Optional list of interfaces to filter for, as fetching
                           data for all interfaces may be a waste of time if only a
                           single interface is needed. The implementing
                           handler/protocol may not support this filter, so do not rely
                           on it.
        :returns: A list of dicts with members `name`, `description`, `oper`, `admin`
                  and `vlan` (the latter being the access/untagged/native vlan ID.
        """
        raise NotImplementedError

    def set_vlan(self, interface, vlan):
        """Set a new vlan on the given interface and remove the previous vlan"""
        raise NotImplementedError

    def set_native_vlan(self, interface: manage.Interface, vlan: int):
        """Set native vlan on a trunk interface"""
        raise NotImplementedError

    def set_interface_up(self, interface: manage.Interface):
        """Enables a previously shutdown interface"""
        raise NotImplementedError

    def set_interface_down(self, interface: manage.Interface):
        """Shuts down/disables an enabled interface"""
        raise NotImplementedError

    def cycle_interfaces(
        self,
        interfaces: Sequence[manage.Interface],
        wait: float = 5.0,
        commit: bool = False,
    ):
        """Link cycles a set of interfaces, with an optional delay in between.

        Mostly used for configuration changes where any client connected to an
        interface needs to be notified about a network change. Typically,
        if an interface is suddenly placed on a new VLAN, cycling the link status of
        the interface will prompt any connected machine to ask for a new DHCP lease,
        which may be necessary now that the machine is potentially on a different IP
        subnet.

        :param interfaces: The list of interfaces to cycle.
        :param wait: number of seconds to wait between down and up operations.
        :param commit: If True, issues a config commit when the interface have been
                       disabled, and issues a new commit when they have been enabled
                       again.
        """
        if not interfaces:
            return

        netbox = set(ifc.netbox for ifc in interfaces)
        assert len(netbox) == 1, "Interfaces belong to multiple netboxes"
        netbox = list(netbox)[0]
        assert netbox == self.netbox, "Interfaces belong to wrong netbox"

        to_cycle = self._filter_oper_up_interfaces(interfaces)
        if not to_cycle:
            _logger.debug("No interfaces to cycle on %s", netbox.sysname)
            return

        _logger.debug("Taking interfaces administratively down")
        for ifc in to_cycle:
            self.set_interface_down(ifc)
            _logger.debug(ifc.ifname)
        if commit:
            self.commit_configuration()

        if wait:
            time.sleep(wait)

        _logger.debug("Taking interfaces administratively up again")
        for ifc in to_cycle:
            self.set_interface_up(ifc)
            _logger.debug(ifc.ifname)
        if commit:
            self.commit_configuration()

    def _filter_oper_up_interfaces(
        self, interfaces: Sequence[manage.Interface]
    ) -> list[manage.Interface]:
        """Filters a list of Interface objects, returning only those that are
        currently operationally up.

        """
        oper_up = set(
            ifc["name"]
            for ifc in self.get_interfaces(interfaces)
            if ifc["oper"] == manage.Interface.OPER_UP
        )
        to_cycle = [ifc for ifc in interfaces if ifc.ifname in oper_up]
        if len(to_cycle) < len(interfaces):
            _logger.debug(
                "Link cycling on %s: Asked to cycle %r, but only %r is oper up",
                self.netbox.sysname,
                [ifc.ifname for ifc in interfaces],
                [ifc.ifname for ifc in to_cycle],
            )
        return to_cycle

    def commit_configuration(self):
        """Commit running configuration or pending configuration changes to the
        device's startup configuration.

        This operation has different implications depending on the underlying
        platform and management protocol, and may in some instances be a no-op.

        This would map more or less one-to-one when using NETCONF and related protocols,
        whereas when using SNMP on Cisco, this may consist of a "write mem" operation.
        """
        raise NotImplementedError

    def get_interface_admin_status(self, interface: manage.Interface) -> int:
        """Query administrative status of an individual interface.

        :returns: A integer to be interpreted as an RFC 2863 ifAdminStatus value, also
                  defined in `manage.Interface.ADMIN_STATUS_CHOICES`:
                  > up(1),       -- ready to pass packets
                  > down(2),
                  > testing(3)   -- in some test mode
        """
        raise NotImplementedError

    def get_netbox_vlans(self) -> list[FantasyVlan]:
        """Returns a list of FantasyVlan objects representing the enabled VLANs on
        this netbox.

        The FantasyVlan objects represent NAV VLAN objects where a VLAN tag can be
        correlated with a NAV VLAN entry, but can also be used to represent VLAN tags
        that are unknown to NAV.
        """
        raise NotImplementedError

    def get_netbox_vlan_tags(self) -> list[int]:
        """Returns a list of enabled VLANs on this netbox.

        :returns: A list of VLAN tags (integers)
        """
        raise NotImplementedError

    def set_interface_voice_vlan(self, interface: manage.Interface, voice_vlan: int):
        """Activates the voice vlan on this interface.

        The default implementation is to employ PortAdmin's generic trunk-based voice
        VLAN concept. This entails setting the interface to trunk mode, keeping the
        untagged VLAN as its native VLAN and trunking/tagging the voice VLAN.

        A vendor-specific implementation in an inheriting class may opt to use a more
        appropriate vendor-specific implementation (one example is Cisco voice VLAN).
        """
        self.set_trunk(interface, interface.vlan, [voice_vlan])

    def get_cisco_voice_vlans(self):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    def set_cisco_voice_vlan(self, interface, voice_vlan):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    def enable_cisco_cdp(self, interface):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    def disable_cisco_voice_vlan(self, interface):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    def disable_cisco_cdp(self, interface):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    def get_native_and_trunked_vlans(self, interface) -> tuple[int, list[int]]:
        """Get the trunked vlans on this interface

        :returns: (native_vlan_tag, list_of_trunked_vlan_tags)
        """
        raise NotImplementedError

    def set_access(self, interface: manage.Interface, access_vlan: int):
        """Puts a port in access mode and sets its access/native/untagged VLAN.

        An implementation must also update the Interface object in the NAVdb.
        """
        raise NotImplementedError

    def set_trunk(
        self, interface: manage.Interface, native_vlan: int, trunk_vlans: Sequence[int]
    ):
        """Puts a port in trunk mode, setting its native/untagged VLAN and tagged
        trunk VLANs as well.

        An implementation must also update the Interface object in the NAVdb.

        :param interface: The interface to set to trunk mode.
        :param native_vlan: The native VLAN for untagged packets on this interface.
        :param trunk_vlans: A list of VLAN tags to allow on this trunk.
        """
        raise NotImplementedError

    def is_dot1x_enabled(self, interface: manage.Interface) -> bool:
        """Returns True if 802.1X authentication is is enabled on interface"""
        raise NotImplementedError

    def get_dot1x_enabled_interfaces(self) -> dict[str, bool]:
        """Fetches the 802.1X enabled state of every interface.

        :returns: A dict mapping each interface name to a "802.1X enabled" value
        """
        raise NotImplementedError

    def is_port_access_control_enabled(self) -> bool:
        """Returns True if port access control is enabled on this netbox"""
        raise NotImplementedError

    def raise_if_not_configurable(self):
        """Raises an exception if this netbox cannot be configured through PortAdmin.

        The exception message will contain a human-readable explanation as to why not.
        """
        raise NotImplementedError

    def is_configurable(self) -> bool:
        """Returns True if this netbox is configurable using this handler"""
        try:
            self.raise_if_not_configurable()
        except Exception:  # noqa: BLE001
            return False
        return True

    def get_poe_state_options(self) -> Sequence[PoeState]:
        """Returns the available options for enabling/disabling PoE on this netbox"""
        raise NotImplementedError

    def set_poe_state(self, interface: manage.Interface, state: PoeState):
        """Set state for enabling/disabling PoE on this interface.
        Available options should be retrieved using `get_poe_state_options`
        """
        raise NotImplementedError

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
        raise NotImplementedError


class ManagementError(Exception):
    """Base exception class for device management errors"""


class DeviceNotConfigurableError(ManagementError):
    """Raised when a device is not configurable by PortAdmin for some reason"""


class NoResponseError(ManagementError):
    """Raised whenever there is no response when talking to the remote device"""


class AuthenticationError(ManagementError):
    """Raised where the remote device indicated the wrong credentials were used"""


class ProtocolError(ManagementError):
    """Raised when some non-categorized error in the underlying protocol occurred
    during communication
    """


class POENotSupportedError(ManagementError):
    """Raised when an interface that does not support PoE is used in a context
    where PoE support is expected
    """


class POEStateNotSupportedError(ManagementError):
    """Raised when a PoE state is detected in a context where it is not supported"""


class XMLParseError(ManagementError):
    """Raised when failing to parse XML"""

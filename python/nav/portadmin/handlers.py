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
from typing import List, Tuple, Dict, Any, Sequence

from nav.models import manage
from nav.portadmin.vlan import FantasyVlan


class ManagementHandler:
    """Defines a common interface for all types of PortAdmin management handlers.

    This defines the set of methods that a handler class may be expected by PortAdmin
    to provide, regardless of the underlying management protocol implemented by such
    a class.
    """
    def __init__(self, netbox: manage.Netbox, **kwargs):
        self.netbox = netbox

    def set_interface_description(self, interface: manage.Interface, description: str):
        """Configures a single interface's description, AKA the ifalias value"""
        raise NotImplementedError

    def get_interface_native_vlan(self, interface: manage.Interface) -> int:
        """Retrieves the native/untagged VLAN configured on interface"""
        raise NotImplementedError

    def get_interfaces(
        self, interfaces: Sequence[manage.Interface] = None
    ) -> List[Dict[str, Any]]:
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

    def cycle_interface(self, interface: manage.Interface, wait: float = 5.0):
        """Take interface down and up again, with an optional delay in between.

        Mostly used for configuration changes where any client connected to the
        interface needs to be notified about the change. Typically, if an interface
        is suddenly placed on a new VLAN, cycling the link status of the interface
        will prompt any connected machine to ask for a new DHCP lease, which may be
        necessary now that the machine is potentially on a different IP subnet.

        :param interface: The interface to cycle.
        :param wait: number of seconds to wait between down and up operations.
        """
        raise NotImplementedError

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

    def get_netbox_vlans(self) -> List[FantasyVlan]:
        """Returns a list of FantasyVlan objects representing the enabled VLANs on
        this netbox.

        The FantasyVlan objects represent NAV VLAN objects where a VLAN tag can be
        correlated with a NAV VLAN entry, but can also be used to represent VLAN tags
        that are unknown to NAV.
        """
        raise NotImplementedError

    def get_netbox_vlan_tags(self) -> List[int]:
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

    def get_native_and_trunked_vlans(self, interface) -> Tuple[int, List[int]]:
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

    def get_dot1x_enabled_interfaces(self) -> Dict[str, bool]:
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
        except Exception:
            return False
        return True


class ManagementError(Exception):
    """Base exception class for device management errors"""

    pass


class DeviceNotConfigurableError(ManagementError):
    """Raised when a device is not configurable by PortAdmin for some reason"""

    pass


class NoResponseError(ManagementError):
    """Raised whenever there is no response when talking to the remote device"""

    pass


class AuthenticationError(ManagementError):
    """Raised where the remote device indicated the wrong credentials were used"""

    pass


class ProtocolError(ManagementError):
    """Raised when some non-categorized error in the underlying protocol occurred
    during communication
    """

    pass

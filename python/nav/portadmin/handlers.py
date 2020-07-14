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
from typing import List, Tuple, Dict, Any

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

    def get_interface_description(self, interface: manage.Interface):
        """Get alias on a specific interface"""
        raise NotImplementedError

    def set_interface_description(self, interface: manage.Interface, description: str):
        """Configures a single interface's description, AKA the ifalias value"""
        raise NotImplementedError

    def get_interface_native_vlan(self, interface: manage.Interface):
        """Get vlan on a specific interface."""
        raise NotImplementedError

    def get_interfaces(self) -> List[Dict[str, Any]]:
        """Retrieves running configuration of all switch ports on the device.

        :returns: A list of dicts with members `name`, `description`, `oper`, `admin`
                  and `vlan` (the latter being the access/untagged/native vlan ID.
        """
        raise NotImplementedError

    def set_vlan(self, interface, vlan):
        """Set a new vlan on the given interface and remove the previous vlan"""
        raise NotImplementedError

    def set_native_vlan(self, interface, vlan):
        """Set native vlan on a trunk interface"""
        raise NotImplementedError

    def set_if_up(self, if_index):
        """Set interface.to up"""
        raise NotImplementedError

    def set_if_down(self, if_index):
        """Set interface.to down"""
        raise NotImplementedError

    def restart_if(self, if_index, wait=5):
        """Take interface down and up.

        :param wait: number of seconds to wait between down and up.
        """
        raise NotImplementedError

    def write_mem(self):
        """Do a write memory on netbox if available"""
        raise NotImplementedError

    def get_if_admin_status(self, if_index):
        """Query administrative status for a given interface."""
        raise NotImplementedError

    def get_if_oper_status(self, if_index):
        """Query operational status of a given interface."""
        raise NotImplementedError

    def get_netbox_vlans(self) -> List[FantasyVlan]:
        """Returns a list of enabled VLANs on this netbox.

        The list will consist of FantasyVlan objects, as not all the VLAN tags
        discovered on the netbox will necessarily correspond to a known Vlan object
        from the NAV database.
        """
        raise NotImplementedError

    def get_available_vlans(self):
        """Get available vlans from the box

        This is similar to the terminal command "show vlans"
        """
        raise NotImplementedError

    def set_voice_vlan(self, interface, voice_vlan):
        """Activate voice vlan on this interface

        Use set_trunk to make sure the interface is put in trunk mode
        """
        raise NotImplementedError

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

        For each available vlan, fetch list of interfaces that forward this
        vlan. If the interface index is in this list, add the vlan to the
        return list.

        :returns: (native_vlan_tag, list_of_trunked_vlan_tags)
        """
        raise NotImplementedError

    def get_native_vlan(self, interface):
        raise NotImplementedError

    def set_trunk_vlans(self, interface, vlans):
        """Trunk the vlans on interface

        Egress_Ports includes native vlan. Be sure to not alter that.

        Get all available vlans. For each available vlan fetch list of
        interfaces that forward this vlan. Set or remove the interface from
        this list based on if it is in the vlans list.

        """
        raise NotImplementedError

    def set_access(self, interface, access_vlan):
        """Set this port in access mode and set access vlan

        Means - remove all vlans except access vlan from this interface
        """
        raise NotImplementedError

    def set_trunk(self, interface, native_vlan, trunk_vlans):
        """Set this port in trunk mode and set native vlan"""
        raise NotImplementedError

    def is_dot1x_enabled(self, interface):
        """Returns a boolean indicating whether 802.1X is enabled on the given
        interface.
        """
        raise NotImplementedError

    def get_dot1x_enabled_interfaces(self) -> Dict[int, bool]:
        """Fetches a dict mapping ifindex to enabled state

        :returns: dict[ifindex, is_enabled]
        """
        raise NotImplementedError

    def is_port_access_control_enabled(self):
        """Returns state of port access control"""
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

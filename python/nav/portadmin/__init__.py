#
# Copyright (C) 2017, 2019 UNINETT AS
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
"""Shared code for portadmin"""


class BaseHandler(object):

    netbox = None

    def __init__(self, netbox):
        self.netbox = netbox

    def test_read(self):
        """Test if read works"""
        return False

    def test_write(self):
        """Test if write works"""
        return False

    def get_if_alias(self, if_index):
        """ Get alias on a specific interface """
        raise NotImplementedError

    def get_all_if_alias(self):
        """Get all aliases for all interfaces."""
        raise NotImplementedError

    def set_if_alias(self, interface, if_alias):
        """Set alias on a specific interface."""
        raise NotImplementedError

    def get_vlan(self, interface):
        """Get vlan on a specific interface."""
        raise NotImplementedError

    def get_all_vlans(self):
        """Get all vlans on the switch"""
        raise NotImplementedError

    def set_vlan(self, interface, vlan):
        """Set a new vlan on the given interface and remove
        the previous vlan"""
        raise NotImplementedError

    def set_native_vlan(self, interface, vlan):
        """Set native vlan on a trunk interface"""
        raise NotImplementedError

    def set_if_up(self, interface):
        """Set interface.to up"""
        raise NotImplementedError

    def set_if_down(self, interface):
        """Set interface.to down"""
        raise NotImplementedError

    def restart_if(self, interface, wait=5):
        """ Take interface down and up.
            wait = number of seconds to wait between down and up."""
        raise NotImplementedError

    def write_mem(self):
        """ Do a write memory on netbox if available"""
        raise NotImplementedError

    def get_if_admin_status(self, if_index):
        """Query administration status for a given interface."""
        raise NotImplementedError

    def get_if_oper_status(self, if_index):
        """Query operational status of a given interface."""
        raise NotImplementedError

    def get_netbox_admin_status(self):
        """Walk all ports and get their administration status."""
        raise NotImplementedError

    def get_netbox_oper_status(self):
        """Walk all ports and get their operational status."""
        raise NotImplementedError

    def get_netbox_vlans(self):
        """Create Fantasyvlans for all vlans on this netbox"""
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

    def disable_cisco_voice_vlan(self, interface):
        """Should not be implemented on anything else than Cisco"""
        raise NotImplementedError

    def get_native_and_trunked_vlans(self, interface):
        """Get the trunked vlans on this interface

        For each available vlan, fetch list of interfaces that forward this
        vlan. If the interface index is in this list, add the vlan to the
        return list.

        :returns native vlan + list of trunked vlan

        """
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

    def is_dot1x_enabled(self, interfaces):
        """Explicitly returns None as we do not know"""
        raise NotImplementedError

    def get_dot1x_enabled_interfaces(self):
        """"""
        raise NotImplementedError

    def is_port_access_control_enabled(self):
        """Returns state of port access control"""
        raise NotImplementedError

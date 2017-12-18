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
import configparser
from operator import attrgetter
from os.path import join

from django.utils.encoding import python_2_unicode_compatible

from nav.config import find_configfile
from nav.models.manage import Vlan

CONFIGFILE = find_configfile(join("portadmin", "portadmin.conf")) or ''


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

    def __cmp__(self, other):
        return cmp(self.vlan, other.vlan)


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

    def get_interface_livedata(self, interfaces):
        """ Update *interfaces* with livedata """
        raise NotImplementedError

    def set_if_alias(self, interface, if_alias):
        """Set alias on a specific interface."""
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

    def get_if_admin_status(self, interface):
        """Query administration status for a given interface."""
        raise NotImplementedError

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

    def set_access(self, interface, access_vlan):
        """Set this port in access mode and set access vlan

        Means - remove all vlans except access vlan from this interface
        """
        raise NotImplementedError

    def set_trunk(self, interface, native_vlan, trunk_vlans):
        """Set this port in trunk mode and set native vlan"""
        raise NotImplementedError

    def get_dot1x_enabled_interfaces(self):
        """"""
        raise NotImplementedError

    def is_port_access_control_enabled(self):
        """Returns state of port access control"""
        raise False


def get_handler(netbox, **kwargs):
    from .snmputils import SNMPFactory

    if netbox.readwrite_connection_profile.is_snmp:
        return SNMPFactory(netbox, **kwargs)
    return None


def read_config():
    """Read the config"""
    config = configparser.ConfigParser()
    config.read(CONFIGFILE)

    return config

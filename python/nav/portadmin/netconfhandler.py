#
# Copyright (C) 2011-2015, 2019 UNINETT AS
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
"""Netconf handler class for PortAdmin."""

from copy import deepcopy
import logging
import time

from lxml import etree
from ncclient import manager
from . import BaseHandler

logger = logging.getLogger('nav.portadmin.netconf')


def host_key_callback(host, fingerprint):
    return True


class NetconfHandler(BaseHandler):

    netbox = None

    def __init__(self, netbox):
        self.netbox = netbox
        self.interface_data = None
        self.config_data = None

    def _connection(self):
        profile = self.netbox.readwrite_connection_profile
        return manager.connect(
            host=self.netbox.ip,
            port=profile.port,
            username=profile.username,
            password=profile.password,
            unknown_host_cb=host_key_callback,
            device_params={'name': 'junos'},
        )

    def test_read(self):
        """Test if read works"""
        with self._connection() as conn:
            try:
                conn.get_config(source='running')
                return True
            except:
                logger.exception("Failure making netconf connection")
        return False

    def test_write(self):
        """Test if write works"""
        return False

    def _interface_data(self):
        if self.interface_data is None:
            with self._connection() as conn:
                data = conn.get_interface_information()
                iface_data = data.xpath('/rpc-reply/interface-information')[0]
                self.interface_data = iface_data
        return self.interface_data

    def _config_data(self):
        if self.config_data is None:
            with self._connection() as conn:
                data = conn.get_config(source='running')
                config_data = data.xpath('/rpc-reply/data/configuration')[0]
                self.config_data = config_data
        return self.config_data

    def get_interface_livedata(self, interfaces):
        self._update_ifaliases(interfaces)
        self._update_vlans(interfaces)
        self._update_statuses(interfaces)

    def _get_interface(self, interface):
        interfaces_config = self._config_data().xpath('./interfaces')[0]
        basename, unit = interface.ifname.split('.')
        interface_config = interfaces_config.xpath(
            './interface[normalize-space(name)="{}"]'.format(basename))
        if len(interface_config) < 1:
            return None, None
        interface_config = interface_config[0]
        unit = interface_config.xpath('unit[name="{}"]'.format(unit))
        if len(unit) < 1:
            return None, None
        return interface_config, unit[0]

    def _update_ifaliases(self, interfaces):
        for interface in interfaces:
            if "." not in interface.ifname:
                continue
            _, unit = self._get_interface(interface)
            for alias in unit.xpath('alias'):
                interface.ifalias = alias.text

    def _update_vlans(self, interfaces):
        vlans = {name: vlan_id for vlan_id, name in self._get_vlans().items()}
        for interface in interfaces:
            _, unit = self._get_interface(interface)
            for vlan in unit.xpath('family/ethernet-switching/vlan[port-mode="access"]'):
                for member in vlan.xpath('members'):
                    interface.vlan = vlans.get(int(member.text), interface.vlan)

    def _update_statuses(self, interfaces):
        for interface in interfaces:
            if "." not in interface.ifname:
                continue
            basename, unit = interface.ifname.split('.')
            iface_data = self._interface_data().xpath('./physical-interface[normalize-space(name)="{basename}"]'.format(basename=basename))
            if len(iface_data) < 1:
                continue
            iface_data = iface_data[0]
            interface.ifoperstatus = iface_data.xpath('./oper-status/text()')[0].strip() == 'up'
            interface.ifadminstatus = interface.ADM_UP if iface_data.xpath('./admin-status/text()')[0].strip() == 'up' else interface.ADM_DOWN

    def set_if_alias(self, interface, if_alias):
        """Set alias on a specific interface."""
        interface_config, unit = self._get_interface(interface)
        aliases = unit.xpath('alias')
        if len(aliases) > 0:
            alias = aliases[0]
        else:
            alias = etree.Element('alias')
            unit.append(alias)
        alias.text = if_alias

    def set_vlan(self, interface, vlan, voice_activated=False):
        """Set a new vlan on the given interface and remove
        the previous vlan"""
        interface_config, unit = self._get_interface(interface)
        vlans = self._get_vlans()
        previous_vlan_nane = vlans[interface.vlan]
        if_vlan_config = unit.xpath('family/ethernet-switching/vlan')
        if len(if_vlan_config) < 1:
            raise RuntimeError("Missing expected interface configuration")
        if_vlan_config = if_vlan_config[0]
        for prev in if_vlan_config.xpath('members[text()="{name}"]'.format(name=previous_vlan_nane)):
            prev.getparent().remove(prev)
        m = etree.Element('members')
        m.text = vlans[vlan]
        if_vlan_config.append(m)

    def set_if_up(self, interface):
        """Set interface.to up"""
        interface_config, _ = self._get_interface(interface)
        for disable in interface_config.xpath('disable'):
            disable.getparent().remove(disable)

    def set_if_down(self, interface):
        """Set interface.to down"""
        self.set_if_up(interface)
        interface_config, _ = self._get_interface(interface)
        disable = etree.Element('disable')
        interface_config.append(disable)

    def restart_if(self, interface, wait=5):
        """ Take interface down and up.
            wait = number of seconds to wait between down and up."""
        self.set_if_down(interface)
        self.commit()
        time.sleep(wait)
        self.set_if_up(interface)
        self.commit()

    def commit(self):
        """Enable all pending changes"""
        logger.warning("Saving updated config")
        save = etree.Element("config")
        save.append(deepcopy(self._config_data()))
        logger.debug(etree.tostring(save, pretty_print=True))
        with self._connection() as m:
            try:
                m.edit_config(config=save, default_operation="replace")
                m.commit()
            except Exception as exception:
                logger.exception("Error saving configuration")
                raise exception

    def write_mem(self):
        """ Do a write memory on netbox if available. Not implemented yet"""
        return
        # Probably something like this depending on device support:
        # with self._connection() as m:
        #     m.copy_config('running', 'startup')

    def get_if_admin_status(self, interface):
        """Query administration status for a given interface."""
        self._update_statuses([interface])
        return interface.ifadminstatus

    def _get_vlans(self):
        vlans = {}
        for vlan in self._config_data().xpath('vlans/vlan'):
            (vlan_id,) = vlan.xpath('vlan-id/text()')
            (name,) = vlan.xpath('name/text()')
            vlans[int(vlan_id)] = str(name)
        return vlans

    def get_available_vlans(self):
        """Get available vlans from the box

        This is similar to the terminal command "show vlans"

        """
        return list(self._get_vlans().keys())

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
        return False

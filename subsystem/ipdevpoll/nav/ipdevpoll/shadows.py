# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Shadow model classes.

This module defines Shadow classes for use in ipdevpoll's storage system.  A
Shadow object will mimic a Django model object, but will not be a "live
object", in the sense that access to member attributes will not result in
database I/O.

"""

from nav.models import manage, oid
from storage import Shadow

# Shadow classes.  Not all of these will be used to store data, but
# may be used to retrieve and cache existing database records.

class Netbox(Shadow):
    __shadowclass__ = manage.Netbox
    __lookups__ = ['sysname', 'ip']

class NetboxType(Shadow):
    __shadowclass__ = manage.NetboxType

class Vendor(Shadow):
    __shadowclass__ = manage.Vendor

class Module(Shadow):
    __shadowclass__ = manage.Module
    __lookups__ = [('netbox', 'name')]

class Device(Shadow):
    __shadowclass__ = manage.Device
    __lookups__ = ['serial']

class Interface(Shadow):
    __shadowclass__ = manage.Interface
    __lookups__ = [('netbox', 'ifname'), ('netbox', 'ifindex')]

class Location(Shadow):
    __shadowclass__ = manage.Location

class Room(Shadow):
    __shadowclass__ = manage.Room

class Category(Shadow):
    __shadowclass__ = manage.Category

class Organization(Shadow):
    __shadowclass__ = manage.Organization

class Vlan(Shadow):
    __shadowclass__ = manage.Vlan
    __lookups__ = ['vlan']

    def _get_my_prefixes(self, containers):
        """Get a list of Prefix shadow objects that point to this Vlan."""
        if Prefix in containers:
            all_prefixes = containers[Prefix].values()
            my_prefixes = [prefix for prefix in all_prefixes
                           if prefix.vlan is self]
            return my_prefixes
        else:
            return []

    def _get_vlan_id_from_my_prefixes(self, containers):
        """Find and return an existing primary key value from any
        shadow prefix object pointing to this Vlan.

        """
        my_prefixes = self._get_my_prefixes(containers)
        for prefix in my_prefixes:
            live_prefix = prefix.get_existing_model()
            if live_prefix and live_prefix.vlan_id:
                # We just care about the first associated prefix we found
                return live_prefix.vlan_id

    def get_existing_model(self, containers):
        """Overriden to provide special handling of looking up
        existing models via known prefixes.

        """
        # Magic lookup only if a simple lookup isn't available
        # Find and set the primary key of this object, if available
        if not (self.vlan or self.id):
            vlan_id = self._get_vlan_id_from_my_prefixes(containers)
            if vlan_id:
                self.id = vlan_id

        # We now return to our regular program :P
        return super(Vlan, self).get_existing_model(containers)


class Prefix(Shadow):
    __shadowclass__ = manage.Prefix
    __lookups__ = [('net_address', 'vlan'), 'net_address']

class GwPortPrefix(Shadow):
    __shadowclass__ = manage.GwPortPrefix
    __lookups__ = ['gw_ip']

class NetType(Shadow):
    __shadowclass__ = manage.NetType

class SwPortVlan(Shadow):
    __shadowclass__ = manage.SwPortVlan

class Arp(Shadow):
    __shadowclass__ = manage.Arp
    __lookups__ = [('netbox', 'ip', 'mac', 'end_time')]

class Cam(Shadow):
    __shadowclass__ = manage.Cam
    __lookups__ = [('netbox', 'ifindex', 'mac', 'miss_count')]

class Prefix(Shadow):
    __shadowclass__ = manage.Prefix
    __lookups__ = ['net_address']

class SwPortAllowedVlan(Shadow):
    __shadowclass__ = manage.SwPortAllowedVlan
    __lookups__ = ['interface']

class SnmpOid(Shadow):
    __shadowclass__ = oid.SnmpOid
    __lookups__ = ['oidkey']

class NetboxSnmpOid(Shadow):
    __shadowclass__ = oid.NetboxSnmpOid



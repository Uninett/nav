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

from nav.models import manage
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

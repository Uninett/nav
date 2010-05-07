# -*- coding: utf-8 -*-
#
# Copyright (C) 2009, 2010 UNINETT AS
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
import datetime
import IPy

from nav.models import manage, oid
from storage import Shadow
import descrparsers
import utils

# Shadow classes.  Not all of these will be used to store data, but
# may be used to retrieve and cache existing database records.

class Netbox(Shadow):
    __shadowclass__ = manage.Netbox
    __lookups__ = ['sysname', 'ip']

    def prepare(self, containers):
        """Attempts to solve serial number conflicts before savetime.

        Specifically, if another Netbox in the database is registered with the
        same serial number as this one, we empty this one's serial number to
        avoid db integrity conflicts.

        """
        if self.device and self.device.serial:
            try:
                other = manage.Netbox.objects.get(
                    device__serial=self.device.serial)
            except manage.Netbox.DoesNotExist:
                pass
            else:
                if other.id != self.id:
                    self._logger.warning(
                        "Serial number conflict, attempting peaceful "
                        "resolution (%s): "
                        "%s [%s] (id: %s) <-> %s [%s] (id: %s)",
                        self.device.serial, 
                        self.sysname, self.ip, self.id,
                        other.sysname, other.ip, other.id)
                    self.device.serial = None

class NetboxType(Shadow):
    __shadowclass__ = manage.NetboxType

class Vendor(Shadow):
    __shadowclass__ = manage.Vendor

class Module(Shadow):
    __shadowclass__ = manage.Module
    __lookups__ = [('netbox', 'name'), 'device']

    def _fix_binary_garbage(self):
        """Fixes string attributes that appear as binary garbage."""

        if utils.is_invalid_utf8(self.model):
            self._logger.warn("Invalid value for model: %r", self.model)
            self.model = repr(self.model)
        
    def prepare(self, containers):
        self._fix_binary_garbage()

class Device(Shadow):
    __shadowclass__ = manage.Device
    __lookups__ = ['serial']

    def _fix_binary_garbage(self):
        """Fixes version strings that appear as binary garbage."""

        for attr in ('hardware_version',
                     'software_version',
                     'firmware_version',
                     'serial'):
            value = getattr(self, attr)
            if utils.is_invalid_utf8(value):
                self._logger.warn("Invalid value for %s: %r",
                                  attr, value)
                setattr(self, attr, repr(value))
        
    def prepare(self, containers):
        self._fix_binary_garbage()

class Interface(Shadow):
    __shadowclass__ = manage.Interface
    __lookups__ = [('netbox', 'ifname'), ('netbox', 'ifindex')]

    @classmethod
    def _find_missing_interfaces(cls, containers):
        """Check if any previously known interfaces are missing from the
        collected set

        This method will compare the set of new Interface containers with the
        Interface objects stored in the database.  A new container will be
        created for any known interface missing from the containers set, and
        its gone_since timestamp will be set.

        NOTE: The comparisons are only made using ifindex values.  If
        a netbox has re-assigned ifindices to its interfaces since the
        last collection, this may cause trouble.

        TODO: Make a deletion algorithm.  Missing interfaces that do
        not correspond to a module known to be down should be deleted.
        If all interfaces belonging to a specific module is down, we
        may have detected that the module is down as well.

        """
        netbox = containers.get(None, Netbox)
        found_interfaces = containers[cls].values()
        timestamp = datetime.datetime.now()
        # pick only interfaces that aren't gone already
        known_interfaces = manage.Interface.objects.filter(
            netbox=netbox.id, gone_since__isnull=True)

        known_ifindices = set(i.ifindex for i in known_interfaces)
        found_ifindices = set(i.ifindex for i in found_interfaces)
        missing_ifindices = known_ifindices.difference(found_ifindices)

        if missing_ifindices:
            cls._logger.info("Marking %s interfaces as gone.  Ifindex: %r",
                             netbox.sysname, missing_ifindices)

        for ifindex in missing_ifindices:
            interface = containers.factory(ifindex, Interface)
            interface.ifindex = ifindex
            interface.gone_since = timestamp
            interface.netbox = netbox


        # This should be the end of the deferred chain
        return True


    @classmethod
    def prepare_for_save(cls, containers):
        cls._find_missing_interfaces(containers)
        super(Interface, cls).prepare_for_save(containers)

class Location(Shadow):
    __shadowclass__ = manage.Location

class Room(Shadow):
    __shadowclass__ = manage.Room

class Category(Shadow):
    __shadowclass__ = manage.Category

class Organization(Shadow):
    __shadowclass__ = manage.Organization

class Usage(Shadow):
    __shadowclass__ = manage.Usage

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

    def _find_numberless_vlan_id(self, containers):
        """Finds and sets pre-existing Vlan primary key value for VLANs that
        have no VLAN number.

        Without this, a new Vlan entry would be added for unnumbered VLANs on
        every collection run.

        """
        # Magic lookup only if a simple lookup isn't available
        # Find and set the primary key of this object, if available
        if not (self.vlan or self.id):
            vlan_id = self._get_vlan_id_from_my_prefixes(containers)
            if vlan_id:
                self.id = vlan_id

    def _guesstimate_net_type(self, containers):
        """Guesstimates a net type for this VLAN, based on its prefixes.

        Various algorithms may be used (and the database may be queried).

        Returns:

          A NetType storage container, suitable for assignment to
          Vlan.net_type.

        """
        prefix_containers = self._get_my_prefixes(containers)
        # ATM we only look at the first prefix we can find.
        if prefix_containers:
            prefix = IPy.IP(prefix_containers[0].net_address)
        else:
            return None

        net_type = 'vlan'
        # Get the number of router ports attached to this prefix
        port_count = manage.GwPortPrefix.objects.filter(
            prefix__net_address=str(prefix)).count()

        if prefix.version() == 6 and prefix.prefixlen() == 128:
            net_type = 'loopback'
        elif prefix.version() == 4:
            if prefix.prefixlen() == 32:
                net_type = 'loopback'
            elif prefix.prefixlen() == 30:
                net_type = port_count == 1 and 'elink' or 'link'
        if port_count > 2:
            net_type = 'core'
        elif port_count == 2:
            net_type = 'link'

        return NetType.get(net_type)

    def prepare(self, containers):
        """Prepares this VLAN object for saving.

        The data stored in a VLAN object consists much of what can be found
        from other objects, such as interfaces and prefixes, so the logic in
        here can becore rather involved.

        """
        self._find_numberless_vlan_id(containers)
        if not self.net_type or self.net_type.id == 'unknown':
            net_type = self._guesstimate_net_type(containers)
            if net_type:
                self.net_type = net_type

class Prefix(Shadow):
    __shadowclass__ = manage.Prefix
    __lookups__ = [('net_address', 'vlan'), 'net_address']

class GwPortPrefix(Shadow):
    __shadowclass__ = manage.GwPortPrefix
    __lookups__ = ['gw_ip']

    def _parse_description(self, containers):
        """Parses router port descriptions to find a suitable Organization,
        netident, usageid and description for this vlan.

        """
        if (not self.interface or \
            not self.interface.netbox or \
            not self.interface.ifalias or \
            not self.prefix or \
            not self.prefix.vlan
            ): 
            return

        sysname = self.interface.netbox.sysname
        ifalias = self.interface.ifalias
        vlan = self.prefix.vlan
        for parse in (descrparsers.parse_ntnu_convention,
                      descrparsers.parse_uninett_convention):
            data = parse(sysname, ifalias)
            if data:
                break
        if not data:
            self._logger.info("ifalias did not match any known router port "
                              "description conventions: %s", ifalias)
            vlan.netident = ifalias
            return

        if data.get('net_type', None):
            vlan.net_type = NetType.get(data['net_type'])
        if data.get('netident', None):
            vlan.net_ident = data['netident']
        if data.get('usage', None):
            vlan.usage = containers.factory(data['usage'], Usage)
            vlan.usage.id = data['usage']
        if data.get('comment', None):
            vlan.description = data['comment']
        if data.get('org', None):
            vlan.organization = containers.factory(data['org'], Organization)
            vlan.organization.id = data['org']

    def prepare(self, containers):
        self._parse_description(containers)

class NetType(Shadow):
    __shadowclass__ = manage.NetType

    @classmethod
    def get(cls, net_type_id):
        """Creates a NetType container for the given net_type id."""
        n = cls()
        n.id = net_type_id
        return n

 
class SwPortVlan(Shadow):
    __shadowclass__ = manage.SwPortVlan

class Arp(Shadow):
    __shadowclass__ = manage.Arp
    __lookups__ = [('netbox', 'ip', 'mac', 'end_time')]

class Cam(Shadow):
    __shadowclass__ = manage.Cam
    __lookups__ = [('netbox', 'ifindex', 'mac', 'miss_count')]

class SwPortAllowedVlan(Shadow):
    __shadowclass__ = manage.SwPortAllowedVlan
    __lookups__ = ['interface']

class SnmpOid(Shadow):
    __shadowclass__ = oid.SnmpOid
    __lookups__ = ['oidkey']

class NetboxSnmpOid(Shadow):
    __shadowclass__ = oid.NetboxSnmpOid



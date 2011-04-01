# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 UNINETT AS
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

from django.db.models import Q

from nav.models import manage, oid
from storage import Shadow
import descrparsers
import utils
from nav.ipdevpoll import db

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

    @classmethod
    @db.commit_on_success
    def cleanup_replaced_netbox(cls, netbox_id, new_type):
        """Removes basic inventory knowledge for a netbox.

        When a netbox has changed type (sysObjectID), this can be called to set
        its new type, delete its modules and interfaces, and reset its
        up_to_date status.

        Arguments:

            netbox_id -- Netbox primary key integer.
            new_type -- A NetboxType shadow container representing the new
                        type.

        """
        type_ = new_type.convert_to_model()
        if type_:
            type_.save()

        netbox = manage.Netbox.objects.get(id=netbox_id)
        cls._logger.warn("Removing stored inventory info for %s",
                         netbox.sysname)
        netbox.type = type_
        netbox.up_to_date = False

        new_device = manage.Device()
        new_device.save()
        netbox.device = new_device

        netbox.save()

        netbox.module_set.all().delete()
        netbox.interface_set.all().delete()


class NetboxType(Shadow):
    __shadowclass__ = manage.NetboxType
    __lookups__ = ['sysobjectid']

class NetboxInfo(Shadow):
    __shadowclass__ = manage.NetboxInfo
    __lookups__ = [('netbox', 'key', 'variable')]

class Vendor(Shadow):
    __shadowclass__ = manage.Vendor

class Module(Shadow):
    __shadowclass__ = manage.Module
    __lookups__ = [('netbox', 'device'), ('netbox', 'name')]

    def prepare(self, containers):
        self._fix_binary_garbage()
        self._fix_missing_name()
        self._resolve_duplicate_serials()
        self._resolve_duplicate_names()

    def _fix_binary_garbage(self):
        """Fixes string attributes that appear as binary garbage."""

        if utils.is_invalid_utf8(self.model):
            self._logger.warn("Invalid value for model: %r", self.model)
            self.model = repr(self.model)

    def _fix_missing_name(self):
        if not self.name and self.device and self.device.serial:
            self.name = "S/N %s" % self.device.serial

    def _resolve_duplicate_serials(self):
        """Attempts to solve serial number conflicts before savetime.

        Specifically, if another Module in the database is registered with the
        same serial number as this one, we attach an empty device to the other
        module.

        """
        if not self.device or not self.device.serial:
            return

        myself = self.get_existing_model()
        try:
            other = manage.Module.objects.get(
                device__serial=self.device.serial)
        except manage.Module.DoesNotExist:
            return

        if other != myself:
            myself = myself or self
            self._logger.warning(
                "Serial number conflict, attempting peaceful resolution (%s): "
                "I am %r (%s) at %s (id: %s) <-> "
                "other is %r (%s) at %s (id: %s)",
                self.device.serial,
                self.name, self.description, myself.netbox.sysname, myself.id,
                other.name, other.description, other.netbox.sysname, other.id)
            new_device = manage.Device()
            new_device.save()
            other.device = new_device
            other.save()

    def _resolve_duplicate_names(self):
        """Attempts to solve module naming conflicts inside the same chassis.

        If two modules physically switch slots in a chassis, they will be
        recognized by their serial numbers, but their names will likely be
        swapped.

        Module names must be unique within a chassis, so if another module on
        this netbox has the same name as us, we need to do something about the
        other module's name before our own to avoid a database integrity
        error.

        """
        other = self._find_name_duplicates()
        if other:
            self._logger.warning(
                "modules appear to have been swapped inside same chassis (%s): "
                "%s (%s) <-> %s (%s)",
                other.netbox.sysname,
                self.name, self.device.serial,
                other.name, other.device.serial)

            other.name = u"%s (%s)" % (other.name, other.device.serial)
            other.save()


    def _find_name_duplicates(self):
        myself_in_db = self.get_existing_model()

        same_name_modules = manage.Module.objects.filter(
            netbox__id = self.netbox.id,
            name = self.name)

        if myself_in_db:
            same_name_modules = same_name_modules.exclude(
                id = myself_in_db.id)

        other = same_name_modules.select_related('device', 'netbox')

        return other[0] if other else None

    @classmethod
    def _make_modulestate_event(cls, django_module):
        from nav.models.event import EventQueue as Event
        e = Event()
        # FIXME: ipdevpoll is not a registered subsystem in the database yet
        e.source_id = 'getDeviceData'
        e.target_id = 'eventEngine'
        e.device = django_module.device
        e.netbox = django_module.netbox
        e.event_type_id = 'moduleState'
        return e

    @classmethod
    def _dispatch_down_event(cls, django_module):
        e = cls._make_modulestate_event(django_module)
        e.state = e.STATE_START
        e.save()

    @classmethod
    def _dispatch_up_event(cls, django_module):
        e = cls._make_modulestate_event(django_module)
        e.state = e.STATE_END
        e.save()

    @classmethod
    def _handle_missing_modules(cls, containers):
        """Handles modules that have gone missing from a device."""
        netbox = containers.get(None, Netbox)
        all_modules = manage.Module.objects.filter(netbox__id = netbox.id)
        modules_up = all_modules.filter(up=manage.Module.UP_UP)
        modules_down = all_modules.filter(up=manage.Module.UP_DOWN)

        collected_modules = containers[Module].values()
        collected_module_pks = [m.id for m in collected_modules if m.id]

        missing_modules = modules_up.exclude(id__in=collected_module_pks)
        reappeared_modules = modules_down.filter(id__in=collected_module_pks)

        if missing_modules:
            shortlist = ", ".join(m.name for m in missing_modules)
            cls._logger.info("%d modules went missing on %s (%s)",
                             netbox.sysname, len(missing_modules), shortlist)
            for module in missing_modules:
                cls._dispatch_down_event(module)

        if reappeared_modules:
            shortlist = ", ".join(m.name for m in reappeared_modules)
            cls._logger.info("%d modules reappeared on %s (%s)",
                             netbox.sysname, len(reappeared_modules),
                             shortlist)
            for module in reappeared_modules:
                cls._dispatch_up_event(module)


    @classmethod
    def cleanup_after_save(cls, containers):
        cls._handle_missing_modules(containers)
        return super(Module, cls).cleanup_after_save(containers)


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
        self.clear_cached_objects()
        
    def prepare(self, containers):
        self._fix_binary_garbage()

class Interface(Shadow):
    __shadowclass__ = manage.Interface

    @classmethod
    def cleanup_after_save(cls, containers):
        """Cleans up Interface data."""
        cls._mark_missing_interfaces(containers)
        cls._delete_missing_interfaces(containers)
        super(Interface, cls).cleanup_after_save(containers)

    @classmethod
    def _mark_missing_interfaces(cls, containers):
        """Marks interfaces in db as gone if they haven't been collected in
        this round.

        This is designed to run in the cleanup_after_save phase, as it needs
        primary keys of the containers to have been found.

        """
        netbox = containers.get(None, Netbox)
        found_interfaces = containers[cls].values()
        timestamp = datetime.datetime.now()

        # start by finding the existing interface's primary keys
        pks = [i.id for i in found_interfaces if i.id]

        # the rest of the interfaces that haven't already been marked as gone,
        # should be marked as such
        missing_interfaces = manage.Interface.objects.filter(
            netbox=netbox.id, gone_since__isnull=True
            ).exclude(pk__in=pks)

        count = missing_interfaces.count()
        if count > 0:
            cls._logger.debug("_mark_missing_interfaces(%s): "
                              "marking %d interfaces as gone",
                              netbox.sysname, count)
        missing_interfaces.update(gone_since=timestamp)

    @classmethod
    def _delete_missing_interfaces(cls, containers):
        """Deletes missing interfaces from the database."""
        netbox = containers.get(None, Netbox)
        ifcs = manage.Interface.objects.filter(netbox__id=netbox.id)
        missing_ifcs = ifcs.exclude(gone_since__isnull=True)

        deleteable = set(cls._get_indexless_ifcs_pk(missing_ifcs))
        deleteable.update(cls._get_dead_ifcs_pk(ifcs))

        if deleteable:
            cls._logger.info("(%s) Deleting %d missing interfaces",
                             netbox.sysname, len(deleteable))
            manage.Interface.objects.filter(pk__in=deleteable).delete()

    @staticmethod
    def _get_indexless_ifcs_pk(interfaces):
        indexless = interfaces.filter(ifindex__isnull=True).values('pk')
        return [row['pk'] for row in indexless]

    @staticmethod
    def _get_dead_ifcs_pk(interfaces,
                          grace_period = datetime.timedelta(days=1)):
        """Returns a list of primary keys of dead interfaces.

        An interface is considered dead if has a gone_since timestamp older
        than the grace period and is either not associated with a module or
        associated with a module known to still be up.

        """
        deadline = datetime.datetime.now() - grace_period
        ancient_ifcs = interfaces.filter(gone_since__lt = deadline)
        down_modules = manage.Module.objects.exclude(up='y')
        dead_ifcs = ancient_ifcs.exclude(module__in = down_modules)
        return [row['pk'] for row in dead_ifcs.values('pk')]

    def lookup_matching_objects(self, containers):
        """Finds existing db objects that match this container.

        ifName is a more important identifier than ifindex, as ifindexes may
        change at any time.  A database migrated from NAV 3.5 may also have a
        lot of weird or duplicate data, due to sloppiness on getDeviceData's
        part.

        """
        query = manage.Interface.objects.filter(netbox__id=self.netbox.id)
        result = []
        if self.ifname:
            result = query.filter(ifname=self.ifname)
        if not result and self.ifdescr:
            # this is only likely on a db recently migrated from NAV 3.5
            result = query.filter(ifname=self.ifdescr,
                                  ifdescr=self.ifdescr)
        if len(result) > 1:
            # Multiple ports with same name? damn...
            # also filter for ifindex, maybe we get lucky
            result = result.filter(ifindex=self.ifindex)

        # If none of this voodoo helped, try matching ifindex only
        if not result:
            result = query.filter(ifindex=self.ifindex)

        return result

    def get_existing_model(self, containers):
        """Implements custom logic for finding known interfaces."""
        result = self.lookup_matching_objects(containers)
        if not result:
            return None
        elif len(result) > 1:
            self._logger.debug(
                "get_existing_model: multiple matching objects returned. "
                "query is: %r", result.query.as_sql())
            raise manage.Interface.MultipleObjectsReturned(
                "get_existing_model: "
                "Found multiple matching objects for %r" % self)
        else:
            self.id = result[0].id
            return result[0]

    @classmethod
    def prepare_for_save(cls, containers):
        super(Interface, cls).prepare_for_save(containers)
        cls._resolve_changed_ifindexes(containers)

    @classmethod
    def _resolve_changed_ifindexes(cls, containers):
        """Resolves conflicts that arise from changed ifindexes.

        The db model will not allow duplicate ifindex, so any ifindex
        that appears to have changed on the device must be nulled out
        in the database before we start updating Interfaces.

        """
        netbox = containers.get(None, Netbox)
        found_existing_map = (
            (interface, interface.get_existing_model(containers))
            for interface in containers[Interface].values())

        changed_ifindexes = [(new.ifindex, old.ifindex)
                             for new, old in found_existing_map
                             if old and new.ifindex != old.ifindex]
        if not changed_ifindexes:
            return

        cls._logger.info("%s changed ifindex mappings (new/old): %r",
                         netbox.sysname, changed_ifindexes)

        my_interfaces = manage.Interface.objects.filter(netbox__id=netbox.id)
        changed_interfaces = my_interfaces.filter(
            ifindex__in=[new for new, old in changed_ifindexes])
        changed_interfaces.update(ifindex=None)

    def prepare(self, containers):
        self.set_netbox_if_unset(containers)
        self.set_ifindex_if_unset(containers)

    def set_netbox_if_unset(self, containers):
        """Sets this Interface's netbox reference if unset by plugins."""
        if self.netbox is None:
            self.netbox = containers.get(None, Netbox)

    def set_ifindex_if_unset(self, containers):
        """Sets this Interface's ifindex value if unset by plugins."""
        if self.ifindex is None:
            interfaces = dict((v, k) for k, v in containers[Interface].items())
            if self in interfaces:
                self.ifindex = interfaces[self]


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

    def _get_my_prefixes(self, containers):
        """Get a list of Prefix shadow objects that point to this Vlan."""
        if Prefix in containers:
            all_prefixes = containers[Prefix].values()
            my_prefixes = [prefix for prefix in all_prefixes
                           if prefix.vlan is self]
            return my_prefixes
        else:
            return []

    def _get_vlan_from_my_prefixes(self, containers):
        """Find and return an existing vlan any shadow prefix object pointing
        to this Vlan.

        """
        my_prefixes = self._get_my_prefixes(containers)
        for prefix in my_prefixes:
            live_prefix = prefix.get_existing_model()
            if live_prefix and live_prefix.vlan_id:
                # We just care about the first associated prefix we found
                self._logger.debug(
                    "_get_vlan_from_my_prefixes: selected prefix "
                    "%s for possible vlan match for %r (%s), "
                    "pre-existing is %r",
                    live_prefix.net_address, self, id(self),
                    live_prefix.vlan)
                return live_prefix.vlan

    def get_existing_model(self, containers):
        """Finds pre-existing Vlan object using custom logic.

        This is complicated because of the relationship between Prefix and
        Vlan, and the fact that multiple vlans with the same vlan number may
        exist, and even Vlan entries without a number.

        If we have a known netident and find an existing record with the same
        vlan value (either a number or NULL) and netident, they are considered
        the same.

        Otherwise, we consider the prefixes that are associated with this vlan.
        If these prefixes already exist in the database, they are likely
        connected to the existing vlan object that we should update.

        If all else fails, a new record is created.

        """
        # Only lookup if primary key isn't already set.
        if self.id:
            return super(Vlan, self).get_existing_model(containers)

        if self.net_ident:
            vlans = manage.Vlan.objects.filter(vlan=self.vlan,
                                               net_ident=self.net_ident)
            if vlans:
                self._logger.debug(
                    "get_existing_model: %d matches found for "
                    "vlan+net_ident: %r",
                    len(vlans), self)
                return vlans[0]

        vlan = self._get_vlan_from_my_prefixes(containers)
        if vlan:
            # Only claim to be the same Vlan object if the vlan number is the
            # same, or the pre-existing object has no Vlan number.
            if vlan.vlan is None or vlan.vlan == self.vlan:
                return vlan

    def _log_if_multiple_prefixes(self, prefix_containers):
        if len(prefix_containers) > 1:
            self._logger.debug("multiple prefixes for %r: %r",
                self, [p.net_address for p in prefix_containers])


    def _guesstimate_net_type(self, containers):
        """Guesstimates a net type for this VLAN, based on its prefixes.

        Various algorithms may be used (and the database may be queried).

        Returns:

          A NetType storage container, suitable for assignment to
          Vlan.net_type.

        """
        prefix_containers = self._get_my_prefixes(containers)
        self._log_if_multiple_prefixes(prefix_containers)
        # ATM we only look at the first prefix we can find.
        if prefix_containers:
            prefix = IPy.IP(prefix_containers[0].net_address)
        else:
            return NetType.get('unknown')

        netbox = containers.get(None, Netbox)
        net_type = 'lan'
        router_count = self._get_router_count_for_prefix(prefix, netbox.id)

        if prefix.version() == 6 and prefix.prefixlen() == 128:
            net_type = 'loopback'
        elif prefix.version() == 4:
            if prefix.prefixlen() == 32:
                net_type = 'loopback'
            elif prefix.prefixlen() == 30:
                net_type = router_count == 1 and 'elink' or 'link'
        if router_count > 2:
            net_type = 'core'
        elif router_count == 2:
            net_type = 'link'

        return NetType.get(net_type)

    @staticmethod
    def _get_router_count_for_prefix(net_address, include_netboxid=None):
        """Returns the number of routers attached to a prefix.

        :param net_address: a prefix network address
        :param include_netboxid: count the netbox with this id as a router for
                                 the prefix, no matter what the db might say
                                 about it.
        :returns: an integer count of routers for `net_address`

        """
        address_filter = Q(interface__gwportprefix__prefix__net_address=
                           str(net_address))
        if include_netboxid:
            address_filter = address_filter | Q(id=include_netboxid)

        router_count = manage.Netbox.objects.filter(
            address_filter,
            category__id__in=('GW', 'GSW')
            )
        return router_count.distinct().count()

    def prepare(self, containers):
        """Prepares this VLAN object for saving.

        The data stored in a VLAN object consists much of what can be found
        from other objects, such as interfaces and prefixes, so the logic in
        here can becore rather involved.

        """
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

    @classmethod
    def cleanup_after_save(cls, containers):
        cls._delete_missing_addresses(containers)

    @classmethod
    @db.autocommit
    def _delete_missing_addresses(cls, containers):
        missing_addresses = cls._get_missing_addresses(containers)
        gwips = [row['gw_ip'] for row in missing_addresses.values('gw_ip')]
        if len(gwips) < 1:
            return

        netbox = containers.get(None, Netbox).get_existing_model()
        cls._logger.info("deleting %d missing addresses from %s: %s",
                         len(gwips), netbox.sysname, ", ".join(gwips))

        missing_addresses.delete()

    @classmethod
    @db.autocommit
    def _get_missing_addresses(cls, containers):
        found_addresses = [g.gw_ip
                           for g in containers[cls].values()]
        netbox = containers.get(None, Netbox).get_existing_model()
        missing_addresses = manage.GwPortPrefix.objects.filter(
            interface__netbox=netbox).exclude(
            gw_ip__in=found_addresses)
        return missing_addresses

    def _parse_description(self, containers):
        """Parses router port descriptions to find a suitable Organization,
        netident, usageid and description for this vlan.

        """
        if not self._are_description_variables_present():
            return

        data = self._parse_description_with_all_parsers()
        if not data:
            self._logger.info("ifalias did not match any known router port "
                              "description conventions: %s",
                              self.interface.ifalias)
            self.prefix.vlan.netident = self.interface.ifalias
            return

        self._update_with_parsed_description_data(data, containers)

    def _are_description_variables_present(self):
        return self.interface and \
            self.interface.netbox and \
            self.interface.ifalias and \
            self.prefix and \
            self.prefix.vlan

    def _parse_description_with_all_parsers(self):
        for parse in (descrparsers.parse_ntnu_convention,
                      descrparsers.parse_uninett_convention):
            data = parse(self.interface.netbox.sysname, self.interface.ifalias)
            if data:
                return data

    def _update_with_parsed_description_data(self, data, containers):
        vlan = self.prefix.vlan
        if data.get('net_type', None):
            vlan.net_type = NetType.get(data['net_type'].lower())
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

    def save(self, containers):
        if not self.id:
            return super(Arp, self).save(containers)

        attrs = dict((attr, getattr(self, attr))
                     for attr in self.get_touched()
                     if attr != 'id')
        if attrs:
            me = manage.Arp.objects.filter(id=self.id)
            me.update(**attrs)

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



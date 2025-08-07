#
# Copyright (C) 2009-2012, 2016 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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

from collections import defaultdict
import IPy

from django.db.models import Q

from nav.models import manage
from nav.event2 import EventFactory

from nav.ipdevpoll.storage import MetaShadow, Shadow, shadowify
from nav.ipdevpoll import descrparsers
from nav.ipdevpoll import utils
from nav.oids import get_enterprise_id

from .netbox import Netbox
from .interface import Interface, InterfaceStack, InterfaceAggregate
from .swportblocked import SwPortBlocked
from .cam import Cam
from .adjacency import AdjacencyCandidate, UnrecognizedNeighbor
from .entity import NetboxEntity
from .prefix import Prefix
from .gwpeers import GatewayPeerSession

__all__ = [
    "NetboxType",
    "NetboxInfo",
    "Vendor",
    "Module",
    "Device",
    "Location",
    "Room",
    "Category",
    "Organization",
    "Usage",
    "Vlan",
    "GwPortPrefix",
    "NetType",
    "SwPortVlan",
    "Arp",
    "SwPortAllowedVlan",
    "Sensor",
    "PowerSupplyOrFan",
    "POEPort",
    "POEGroup",
    "Interface",
    "InterfaceStack",
    "InterfaceAggregate",
    "SwPortBlocked",
    "Cam",
    "AdjacencyCandidate",
    "UnrecognizedNeighbor",
    "NetboxEntity",
    "GatewayPeerSession",
]

# Shadow classes.  Not all of these will be used to store data, but
# may be used to retrieve and cache existing database records.


ALERT_TYPE_MAPPING = {
    "hardware_version": "deviceHwUpgrade",
    "software_version": "deviceSwUpgrade",
    "firmware_version": "deviceFwUpgrade",
}
device_event = EventFactory('ipdevpoll', 'eventEngine', 'deviceState')


class NetboxType(Shadow):
    __shadowclass__ = manage.NetboxType
    __lookups__ = ['sysobjectid']

    def get_enterprise_id(self):
        """Returns the type's enterprise ID as an integer.

        The type's sysobjectid should always start with
        SNMPv2-SMI::enterprises (1.3.6.1.4.1).  The next OID element will be
        an enterprise ID, while the remaining elements will describe the type
        specific to the vendor.

        :returns: A long integer if the type has a valid enterprise id, None
                  otherwise.

        """
        try:
            return get_enterprise_id(self.sysobjectid)
        except ValueError:
            return None


class NetboxInfo(Shadow):
    __shadowclass__ = manage.NetboxInfo
    __lookups__ = [('netbox', 'key', 'variable')]

    @classmethod
    def get_dependencies(cls):
        """Fakes a dependency to all Shadow subclasses.

        We do this to ensure NetboxInfo is always the last table to be updated
        by a job.

        Often, this table is used to store timestamps of successful jobs, but
        with no other real dependencies than Netbox it would be saved before
        most of the other container objects are saved. Since not all the data
        is stored in a single transaction, storing timestamps in NetboxInfo
        may indicate a success where there was in reality a failure due to a
        database problem that occurred after NetboxInfo was updated.

        """

        return MetaShadow.shadowed_classes.values()


class Vendor(Shadow):
    __shadowclass__ = manage.Vendor


class Module(Shadow):
    __shadowclass__ = manage.Module
    __lookups__ = [('netbox', 'device'), ('netbox', 'name')]
    event = EventFactory('ipdevpoll', 'eventEngine', 'moduleState')

    def __init__(self, *args, **kwargs):
        super(Module, self).__init__(*args, **kwargs)
        self.is_new = None

    @classmethod
    def prepare_for_save(cls, containers):
        cls._resolve_actual_duplicate_names(containers)
        return super(Module, cls).prepare_for_save(containers)

    @classmethod
    def _resolve_actual_duplicate_names(cls, containers):
        """Attempts to resolve an issue where multiple collected modules are
        reported as having the same name, by adding the module's serial number
        to its name before it's stored into the db.

        This may happen in some devices, but is not supported by NAV's data
        model.

        """
        if cls not in containers:
            return

        by_name = defaultdict(list)
        for module in containers[cls].values():
            by_name[module.name].append(module)
        duped = [name for name in by_name if len(by_name[name]) > 1]
        for name in duped:
            cls._logger.warning(
                "Device reports %d modules by the name %r", len(by_name[name]), name
            )
            for module in by_name[name]:
                serial = module.device.serial if module.device else None
                if serial:
                    module.name = '{} ({})'.format(name, serial)

    def prepare(self, containers):
        self._fix_binary_garbage()
        self._fix_missing_name()
        self._resolve_duplicate_names()
        self.is_new = not self.get_existing_model()

    def _fix_binary_garbage(self):
        """Fixes string attributes that appear as binary garbage."""

        if utils.is_invalid_database_string(self.model):
            self._logger.warning("Invalid value for model: %r", self.model)
            self.model = repr(self.model)

    def _fix_missing_name(self):
        if not self.name and self.device and self.device.serial:
            self.name = "S/N %s" % self.device.serial

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
                self.name,
                self.device.serial,
                other.name,
                other.device.serial,
            )

            other.name = "%s (%s)" % (other.name, other.device.serial)
            other.save()

    def _find_name_duplicates(self):
        myself_in_db = self.get_existing_model()

        same_name_modules = manage.Module.objects.filter(
            netbox__id=self.netbox.id, name=self.name
        )

        if myself_in_db:
            same_name_modules = same_name_modules.exclude(id=myself_in_db.id)

        other = same_name_modules.select_related('device', 'netbox')

        return other[0] if other else None

    @classmethod
    def _handle_missing_modules(cls, containers):
        """Handles modules that have gone missing from a device."""
        netbox = containers.get(None, Netbox)
        all_modules = manage.Module.objects.filter(netbox__id=netbox.id)
        modules_up = all_modules.filter(up=manage.Module.UP_UP)
        modules_down = all_modules.filter(up=manage.Module.UP_DOWN)

        collected_modules = containers[Module].values()
        collected_module_pks = [m.id for m in collected_modules if m.id]

        missing_modules = modules_up.exclude(id__in=collected_module_pks)
        reappeared_modules = modules_down.filter(id__in=collected_module_pks)

        if missing_modules:
            shortlist = ", ".join(m.name for m in missing_modules)
            cls._logger.info(
                "%d modules went missing on %s (%s)",
                netbox.sysname,
                len(missing_modules),
                shortlist,
            )
            for module in missing_modules:
                cls.event.start(module.device, module.netbox, module.id).save()

        if reappeared_modules:
            shortlist = ", ".join(m.name for m in reappeared_modules)
            cls._logger.info(
                "%d modules reappeared on %s (%s)",
                netbox.sysname,
                len(reappeared_modules),
                shortlist,
            )
            for module in reappeared_modules:
                cls.event.end(module.device, module.netbox, module.id).save()

    def cleanup(self, containers):
        self._handle_new_module()

    def _handle_new_module(self):
        if not self.is_new:
            return
        module = self.get_existing_model()
        # If a module is also registered as a chassis, then avoid duplicate
        # events and let NetboxEntity handle it. This should not really happen,
        # but its possible if the standard MIBs detects something as a module
        # and proprietary MIBs detect the same thing as a chassis.
        if not module.get_entity().is_chassis() and module.device.serial:
            device_event.notify(
                device=module.device,
                netbox=module.netbox,
                alert_type='deviceNewModule',
            ).save()

    @classmethod
    def cleanup_after_save(cls, containers):
        cls._handle_missing_modules(containers)
        super(Module, cls).cleanup_after_save(containers)


class Device(Shadow):
    __shadowclass__ = manage.Device
    __lookups__ = ['serial']
    event = EventFactory('ipdevpoll', 'eventEngine', 'deviceNotice')

    def __init__(self, *args, **kwargs):
        super(Device, self).__init__(*args, **kwargs)
        self.changed_versions = {}

    def prepare(self, containers):
        self._fix_binary_garbage()
        self._detect_version_changes()

    def _fix_binary_garbage(self):
        """Fixes version strings that appear as binary garbage."""

        for attr in (
            'hardware_version',
            'software_version',
            'firmware_version',
            'serial',
        ):
            value = getattr(self, attr)
            if utils.is_invalid_database_string(value):
                self._logger.warning("Invalid value for %s: %r", attr, value)
                setattr(self, attr, repr(value))
        self.clear_cached_objects()

    def _detect_version_changes(self):
        """
        Detects if the software, hardware or firmware version changed for each device.

        Saves this information in changed_versions in the Device instance.
        """
        old_device = self.get_existing_model()
        if old_device:
            changed_versions = set(self.get_diff_attrs(old_device)).intersection(
                (
                    'hardware_version',
                    'software_version',
                    'firmware_version',
                )
            )
            for version in changed_versions:
                self.changed_versions[version] = (
                    getattr(old_device, version),
                    getattr(self, version),
                )

    def cleanup(self, containers):
        if self.changed_versions:
            self._post_events_version_changes(containers)

    def _post_events_version_changes(self, containers):
        """Posts events for software, hardware or firmware changes."""
        device = self.get_existing_model()
        for alert_type, (old_version, new_version) in self.changed_versions.items():
            self.event.notify(
                device=device,
                netbox=containers.get(None, Netbox).get_existing_model(),
                alert_type=ALERT_TYPE_MAPPING[alert_type],
                varmap={
                    "old_version": old_version if old_version else "N/A",
                    "new_version": new_version if new_version else "N/A",
                },
            ).save()


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

    def prepare(self, containers):
        """Prepares this VLAN object for saving.

        The data stored in a VLAN object consists much of what can be found
        from other objects, such as interfaces and prefixes, so the logic in
        here can become rather involved.

        """
        if not self.net_type or self.net_type.id == 'unknown':
            net_type = self._guesstimate_net_type(containers)
            if net_type:
                self.net_type = net_type

    def save(self, containers):
        if self._revert_vlan_on_type_change_to_scope(
            containers
        ) or self._is_type_changed_to_static(containers):
            return

        self._ignore_unknown_organizations()
        self._ignore_unknown_usages()

        super(Vlan, self).save(containers)

    def get_existing_model(self, containers=None):
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
            if self.netbox:
                netboxid = self.netbox.id
            else:
                netboxid = None
            vlans = manage.Vlan.objects.filter(
                vlan=self.vlan, net_ident=self.net_ident, netbox__id=netboxid
            )
            if vlans:
                self._logger.debug(
                    "get_existing_model: %d matches found for vlan+net_ident: %r",
                    len(vlans),
                    self,
                )
                return vlans[0]

        vlan = self._get_vlan_from_my_prefixes(containers)
        if vlan:
            # Only reuse the existing Vlan object if lacks essential identifiers
            if vlan.vlan is None or (vlan.vlan == self.vlan and not self.net_ident):
                return vlan

    def _has_no_prefixes(self, containers):
        prefixes = self._get_my_prefixes(containers)
        if not prefixes:
            self._logger.debug("no associated prefixes, not saving: %r", self)
            return True

    def _revert_vlan_on_type_change_to_scope(self, containers):
        mdl = self.get_existing_model(containers)
        if mdl and mdl.net_type_id == 'scope':
            prefixes = self._get_my_prefixes(containers)
            self._logger.warning(
                "some interface claims to be on a scope "
                "prefix, not changing vlan details. attached "
                "prefixes: %r",
                [pfx.net_address for pfx in prefixes],
            )
            for pfx in prefixes:
                pfx.vlan = mdl
            return True

    def _is_type_changed_to_static(self, containers):
        mdl = self.get_existing_model(containers)
        if mdl and mdl.net_type_id != 'static' and self.net_type.id == 'static':
            self._logger.info(
                "will not change vlan %r type from %s to static",
                self.net_ident,
                mdl.net_type_id,
            )
            return True

    def _ignore_unknown_organizations(self):
        if self.organization and not self.organization.get_existing_model():
            self._logger.warning(
                "ignoring unknown organization id %r", self.organization.id
            )
            self.organization = None

    def _ignore_unknown_usages(self):
        if self.usage and not self.usage.get_existing_model():
            self._logger.warning("ignoring unknown usage id %r", self.usage.id)
            self.usage = None

    def _get_my_prefixes(self, containers):
        """Get a list of Prefix shadow objects that point to this Vlan."""
        if Prefix in containers:
            all_prefixes = containers[Prefix].values()
            my_prefixes = [prefix for prefix in all_prefixes if prefix.vlan is self]
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
                    live_prefix.net_address,
                    self,
                    id(self),
                    live_prefix.vlan,
                )
                return live_prefix.vlan

    def _log_if_multiple_prefixes(self, prefix_containers):
        if len(prefix_containers) > 1:
            self._logger.debug(
                "multiple prefixes for %r: %r",
                self,
                [p.net_address for p in prefix_containers],
            )

    def _guesstimate_net_type(self, containers):
        """Guesstimates a net type for this VLAN, based on its prefixes.

        Various algorithms may be used (and the database may be queried).

        Returns:

          A NetType storage container, suitable for assignment to
          Vlan.net_type.

        """
        prefix_containers = self._get_my_prefixes(containers)
        self._log_if_multiple_prefixes(prefix_containers)

        if prefix_containers:
            # prioritize ipv4 prefixes, as the netmasks are more revealing
            prefix_containers.sort(key=lambda p: IPy.IP(p.net_address).version())
            prefix = IPy.IP(prefix_containers[0].net_address)
        else:
            return NetType.get('unknown')

        netbox = containers.get(None, Netbox)
        net_type = 'lan'
        router_count = self._get_router_count_for_prefix(prefix, netbox.id)
        has_virtual_addrs = self._get_virtual_address_count(prefix) > 0

        if prefix.version() == 6 and prefix.prefixlen() == 128:
            net_type = 'loopback'
        elif prefix.version() == 4:
            if prefix.prefixlen() == 32:
                net_type = 'loopback'
            elif prefix.prefixlen() in (30, 31):
                net_type = 'elink' if router_count == 1 else 'link'
        if not has_virtual_addrs:
            if router_count > 2:
                net_type = 'core'
            elif router_count == 2:
                net_type = 'link'

        self._logger.debug(
            "_guesstimate_net_type: %r -> %r (router_count=%r has_virtual_addrs=%r)",
            prefix,
            net_type,
            router_count,
            has_virtual_addrs,
        )
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
        address_filter = Q(
            interfaces__gwport_prefixes__prefix__net_address=str(net_address)
        )
        if include_netboxid:
            address_filter = address_filter | Q(id=include_netboxid)

        router_count = manage.Netbox.objects.filter(
            address_filter, category__id__in=('GW', 'GSW')
        )
        return router_count.distinct().count()

    @staticmethod
    def _get_virtual_address_count(net_address):
        """Returns the number of virtual router port addresses attached to a prefix.
        If there are any virtual addresses, this indicates the network has some sort of
        redundancy, either HSRP or VRRP.

        :param net_address: a prefix network address
        :returns: an integer count of virtual gwportprefixes

        """
        virtual_addresses = manage.GwPortPrefix.objects.filter(
            prefix__net_address=str(net_address),
            virtual=True,
        )
        return virtual_addresses.distinct().count()


class GwPortPrefix(Shadow):
    __shadowclass__ = manage.GwPortPrefix
    __lookups__ = ['gw_ip']

    @classmethod
    def cleanup_after_save(cls, containers):
        cls._delete_missing_addresses(containers)

    @classmethod
    def _delete_missing_addresses(cls, containers):
        missing_addresses = cls._get_missing_addresses(containers)
        gwips = [row['gw_ip'] for row in missing_addresses.values('gw_ip')]
        if not gwips:
            return

        netbox = containers.get(None, Netbox).get_existing_model()
        cls._logger.info(
            "deleting %d missing addresses from %s: %s",
            len(gwips),
            netbox.sysname,
            ", ".join(gwips),
        )

        missing_addresses.delete()

    @classmethod
    def _get_missing_addresses(cls, containers):
        found_addresses = [g.gw_ip for g in containers[cls].values()]
        netbox = containers.get(None, Netbox).get_existing_model()
        missing_addresses = manage.GwPortPrefix.objects.filter(
            interface__netbox=netbox
        ).exclude(gw_ip__in=found_addresses)
        return missing_addresses

    def _parse_description(self, containers):
        """Parses router port descriptions to find a suitable Organization,
        netident, usageid and description for this vlan.

        """
        if not self._are_description_variables_present():
            return

        data = self._parse_description_with_all_parsers()
        if not data:
            self._logger.debug(
                "ifalias did not match any known router port "
                "description conventions: %s",
                self.interface.ifalias,
            )
            self.prefix.vlan.netident = self.interface.ifalias
            return

        self._update_with_parsed_description_data(data, containers)

    def _are_description_variables_present(self):
        return (
            self.interface
            and self.interface.netbox
            and self.interface.ifalias
            and self.prefix
            and self.prefix.vlan
        )

    def _parse_description_with_all_parsers(self):
        for parse in (
            descrparsers.parse_ntnu_convention,
            descrparsers.parse_uninett_convention,
        ):
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
        if data.get('vlan'):
            vlan.vlan = data['vlan']
            self._logger.info(
                "forcing vlan tag of %s to %s by description convention",
                self.prefix.net_address,
                vlan.vlan,
            )

    def prepare(self, containers):
        self._parse_description(containers)


class NetType(Shadow):
    __shadowclass__ = manage.NetType

    @classmethod
    def get(cls, net_type_id):
        """Creates a NetType container for the given net_type id."""
        ntype = cls()
        ntype.id = net_type_id
        return ntype


class SwPortVlan(Shadow):
    __shadowclass__ = manage.SwPortVlan


class Arp(Shadow):
    __shadowclass__ = manage.Arp

    def save(self, containers):
        if not self.id:
            return super(Arp, self).save(containers)

        attrs = dict(
            (attr, getattr(self, attr)) for attr in self.get_touched() if attr != 'id'
        )
        if attrs:
            myself = manage.Arp.objects.filter(id=self.id)
            myself.update(**attrs)


class SwPortAllowedVlan(Shadow):
    __shadowclass__ = manage.SwPortAllowedVlan
    __lookups__ = ['interface']


class Sensor(Shadow):
    __shadowclass__ = manage.Sensor
    __lookups__ = [('netbox', 'internal_name', 'mib')]

    @classmethod
    def cleanup_after_save(cls, containers):
        cls._delete_missing_sensors(containers)

    @classmethod
    def _delete_missing_sensors(cls, containers):
        missing_sensors = cls._get_missing_sensors(containers)
        sensor_names = [
            row['internal_name'] for row in missing_sensors.values('internal_name')
        ]
        if not missing_sensors:
            return
        netbox = containers.get(None, Netbox)
        cls._logger.debug(
            'Deleting %d missing sensors from %s: %s',
            len(sensor_names),
            netbox.sysname,
            ", ".join(sensor_names),
        )
        missing_sensors.delete()

    @classmethod
    def _get_missing_sensors(cls, containers):
        found_sensor_pks = [sensor.id for sensor in containers[cls].values()]
        netbox = containers.get(None, Netbox)
        missing_sensors = manage.Sensor.objects.filter(netbox=netbox.id).exclude(
            pk__in=found_sensor_pks
        )
        return missing_sensors

    def prepare(self, containers):
        if self.interface:
            if self.name:
                self.name = self.name.format(ifc=self.interface.ifname)
            if self.human_readable:
                self.human_readable = self.human_readable.format(
                    ifc=self.interface.ifdescr
                )
            if self.internal_name:
                self.internal_name = self.internal_name.format(
                    ifc=self.interface.ifname
                )


class PowerSupplyOrFan(Shadow):
    __shadowclass__ = manage.PowerSupplyOrFan
    __lookups__ = [('netbox', 'name')]

    def __init__(self, *args, **kwargs):
        super(PowerSupplyOrFan, self).__init__(*args, **kwargs)
        self.is_new = None

    def prepare(self, containers):
        self.is_new = not self.get_existing_model()
        # Set a default value of UNKNOWN if this is a new object
        if self.is_new and self.up is None:
            self.up = manage.PowerSupplyOrFan.STATE_UNKNOWN

    def cleanup(self, containers):
        self._handle_new_psu_or_fan()

    def _handle_new_psu_or_fan(self):
        if not self.is_new:
            return
        psufan = self.get_existing_model()
        # Device not existing seems to be an issue exclusive to PowerSupplyOrFan objects
        try:
            if psufan.device.serial:
                device_event.notify(
                    device=psufan.device,
                    netbox=psufan.netbox,
                    alert_type="deviceNewPsu" if psufan.is_psu() else "deviceNewFan",
                ).save()
        except manage.Device.DoesNotExist:
            return

    @classmethod
    def cleanup_after_save(cls, containers):
        cls._delete_missing_psus_and_fans(containers)
        super(PowerSupplyOrFan, cls).cleanup_after_save(containers)

    @classmethod
    def _delete_missing_psus_and_fans(cls, containers):
        missing_psus_and_fans = cls._get_missing_psus_and_fans(containers)
        psu_and_fan_names = [
            row['name'] for row in missing_psus_and_fans.values('name')
        ]
        if not missing_psus_and_fans:
            return
        netbox = containers.get(None, Netbox)
        cls._logger.debug(
            'Deleting %d missing psus and fans from %s: %s',
            len(psu_and_fan_names),
            netbox.sysname,
            ", ".join(psu_and_fan_names),
        )
        cls._alert_missing_devices_are_deleted(missing_psus_and_fans)
        missing_psus_and_fans.delete()

    @classmethod
    def _get_missing_psus_and_fans(cls, containers):
        found_psus_and_fans_pks = [psu_fan.id for psu_fan in containers[cls].values()]
        netbox = containers.get(None, Netbox)
        missing_psus_and_fans = manage.PowerSupplyOrFan.objects.filter(
            netbox=netbox.id
        ).exclude(pk__in=found_psus_and_fans_pks)
        return missing_psus_and_fans

    @classmethod
    def _alert_missing_devices_are_deleted(cls, deleted_psus_and_fans):
        for psufan in deleted_psus_and_fans:
            try:
                if psufan.device.serial:
                    device_event.notify(
                        device=psufan.device,
                        netbox=psufan.netbox,
                        alert_type=(
                            "deviceDeletedPsu"
                            if psufan.is_psu()
                            else "deviceDeletedFan"
                        ),
                    ).save()
            except manage.Device.DoesNotExist:
                pass


class POEPort(Shadow):
    __shadowclass__ = manage.POEPort
    __lookups__ = [('netbox', 'poegroup', 'index')]

    @classmethod
    def cleanup_after_save(cls, containers):
        found = [port.id for port in containers[cls].values()]
        netbox = containers.get(None, Netbox)
        manage.POEPort.objects.filter(netbox=netbox.id).exclude(pk__in=found).delete()


class POEGroup(Shadow):
    __shadowclass__ = manage.POEGroup
    __lookups__ = [('netbox', 'index')]
    phy_index = None

    @classmethod
    def cleanup_after_save(cls, containers):
        found = [grp.id for grp in containers[cls].values()]
        netbox = containers.get(None, Netbox)
        manage.POEGroup.objects.filter(netbox=netbox.id).exclude(pk__in=found).delete()

    def prepare(self, containers):
        if self.phy_index and not self.module:
            entity = manage.NetboxEntity.objects.filter(
                netbox=self.netbox.id, index=self.phy_index
            ).first()
            if entity and entity.device:
                self.module = entity.device.modules.first()
        vendor = self.netbox.type.vendor.id if self.netbox.type else ''
        if vendor == 'hp' and not self.module:
            module = manage.Module.objects.filter(
                netbox=self.netbox.id,
                name=chr(ord('A') + self.index - 1),
            ).first()
            if module:
                self.module = shadowify(module)

#
# Copyright (C) 2010, 2011, 2013-2015 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Import seed data in bulk."""

import json

from django.core.exceptions import ValidationError

from nav.models.fields import PointField
from nav.models.manage import Netbox, Room, Organization
from nav.models.manage import Category, NetboxInfo, NetboxGroup
from nav.models.manage import NetboxCategory, Interface
from nav.models.manage import Location, Usage, NetboxType, Vendor
from nav.models.manage import Prefix, Vlan, NetType
from nav.models.manage import ManagementProfile, NetboxProfile
from nav.models.cabling import Cabling, Patch
from nav.models.service import Service, ServiceProperty
from nav.util import is_valid_ip
from nav.web.servicecheckers import get_description

from nav.bulkparse import BulkParseError


class BulkImporter:
    """Abstract bulk import iterator"""

    def __init__(self, parser):
        self.parser = parser

    def __iter__(self):
        return self

    def __next__(self):
        """Parses and returns next line"""
        try:
            row = next(self.parser)
            row = self._decode_as_utf8(row)
            objects = self._create_objects_from_row(row)
        except BulkParseError as error:
            objects = error
        return self.parser.line_num, objects

    @staticmethod
    def _decode_as_utf8(row):
        """Decodes all unicode values in row as utf-8 strings"""
        for key, value in row.items():
            if isinstance(value, bytes):
                row[key] = value.decode('utf-8')
        return row

    def _create_objects_from_row(self, row):
        """Hook to create Django ORM objects from a row.

        Must be overridden in descendant classes.

        """
        raise NotImplementedError


class NetboxImporter(BulkImporter):
    """Creates objects from the netbox bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(Netbox, ip=row['ip'])
        raise_if_exists(Netbox, sysname=row['ip'])

        netbox = self._get_netbox_from_row(row)
        objects = [netbox]

        netbox.data = self._parse_data(row['data'])

        netboxinfo = self._get_netboxinfo_from_function(netbox, row['function'])
        if netboxinfo:
            objects.append(netboxinfo)

        netboxgroups = self._get_groups_from_group(netbox, row.get('netboxgroup', []))
        if netboxgroups:
            objects.extend(netboxgroups)

        profiles = self._get_management_profiles(
            netbox, row.get('management_profiles', '')
        )
        if profiles:
            objects.extend(profiles)

        return objects

    @staticmethod
    def _get_netbox_from_row(row):
        netbox = Netbox(ip=row['ip'])
        netbox.room = get_object_or_fail(Room, id=row['roomid'])
        netbox.organization = get_object_or_fail(Organization, id=row['orgid'])
        netbox.category = get_object_or_fail(Category, id=row['catid'])
        netbox.sysname = netbox.ip

        master = row.get('master')
        if master:
            if is_valid_ip(master, strict=True):
                netbox.master = get_object_or_fail(Netbox, ip=master)
            else:
                netbox.master = get_object_or_fail(Netbox, sysname__startswith=master)

        return netbox

    @staticmethod
    def _get_management_profiles(netbox, profile_names):
        if not profile_names:
            return

        profiles = profile_names.split('|')
        profiles = [
            get_object_or_fail(ManagementProfile, name=name)
            for name in profiles
            if name.strip()
        ]
        return [NetboxProfile(netbox=netbox, profile=profile) for profile in profiles]

    @staticmethod
    def _get_netboxinfo_from_function(netbox, function):
        if function:
            return NetboxInfo(
                netbox=netbox, key=None, variable='function', value=function
            )

    @staticmethod
    def _get_groups_from_group(netbox, netboxgroup):
        if not netboxgroup:
            return

        netboxgroups = []
        for netboxgroupid in [s for s in netboxgroup if s]:
            netboxgroup = get_object_or_fail(NetboxGroup, id=netboxgroupid)
            netboxgroups.append(NetboxCategory(netbox=netbox, category=netboxgroup))
        return netboxgroups

    @staticmethod
    def _parse_data(datastring):
        if datastring:
            items = (item.split('=', 1) for item in datastring.split('|'))
        else:
            items = []
        return dict(items) if items else dict()


class ServiceImporter(BulkImporter):
    """Creates objects from the service bulk format"""

    def _create_objects_from_row(self, row):
        objects = []
        netbox = get_object_or_fail(Netbox, sysname=row['host'])
        service = Service(netbox=netbox, handler=row['service'])
        objects.append(service)

        handler_descr = self._get_handler_descr(row['service'])
        service_args = dict([arg.split('=', 1) for arg in row.get('arg', [])])
        self._validate_handler_args(handler_descr, service_args)
        service_properties = self._get_service_properties(service, service_args)

        if service_properties:
            objects.extend(service_properties)

        return objects

    @staticmethod
    def _get_handler_descr(handler):
        descr = get_description(handler)
        if not descr:
            raise BulkImportError("Service handler %s does not exist" % handler)
        return descr

    @staticmethod
    def _get_service_properties(service, args):
        service_properties = []
        for prop, val in args.items():
            serviceprop = ServiceProperty(service=service, property=prop, value=val)
            service_properties.append(serviceprop)
        return service_properties

    @staticmethod
    def _validate_handler_args(handler_descr, service_args):
        arg_keys = handler_descr.get('args', [])
        optarg_keys = handler_descr.get('optargs', [])

        for key in arg_keys:
            if key not in service_args:
                raise BulkImportError("Missing required property: %s" % key)

        for key in service_args:
            if key not in arg_keys and key not in optarg_keys:
                raise BulkImportError("Key %s is not valid for handler" % key)


class LocationImporter(BulkImporter):
    """Creates objects from the location bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(Location, id=row['locationid'])
        if row['parent']:
            parent = get_object_or_fail(Location, id=row['parent'])
        else:
            parent = None
        location = Location(
            id=row['locationid'], parent=parent, description=row['descr']
        )
        return [location]


class RoomImporter(BulkImporter):
    """Creates objects from the room bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(Room, id=row['roomid'])
        location = get_object_or_fail(Location, id=row['locationid'])
        attributes = dict([attr.split('=', 1) for attr in row.get('attr', [])])
        room = Room(
            id=row['roomid'],
            location=location,
            description=row['descr'],
            data=attributes,
        )
        try:
            room.position = PointField().to_python(row['position'])
        except (ValidationError, ValueError):
            raise InvalidValue(row['position'])
        return [room]


class ManagementProfileImporter(BulkImporter):
    """Creates objects from the management profile bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(ManagementProfile, name=row['name'])
        result = ManagementProfile(name=row['name'])

        proto_lookup = {
            name: value for value, name in ManagementProfile.PROTOCOL_CHOICES
        }

        result.protocol = proto_lookup.get(row['protocol'])
        result.configuration = json.loads(row['configuration'])
        return [result]


class OrgImporter(BulkImporter):
    """Creates objects from the organization bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(Organization, id=row['orgid'])
        if row['parent']:
            parent = get_object_or_fail(Organization, id=row['parent'])
        else:
            parent = None
        attributes = dict([attr.split('=', 1) for attr in row.get('attr', [])])
        org = Organization(
            id=row['orgid'],
            parent=parent,
            description=row['description'],
            data=attributes,
        )
        return [org]


class PrefixImporter(BulkImporter):
    """Creates objects from the prefix bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(Prefix, net_address=row['netaddr'])
        net_type = get_object_or_fail(NetType, id=row['nettype'])

        org = None
        if row['orgid']:
            org = get_object_or_fail(Organization, id=row['orgid'])

        usage = None
        if row['usage']:
            usage = get_object_or_fail(Usage, id=row['usage'])

        vlan_number = None
        if row['vlan']:
            vlan_number = int(row['vlan'])

        vlan, _ = Vlan.objects.get_or_create(
            vlan=vlan_number,
            net_type=net_type,
            organization=org,
            net_ident=row['netident'],
            usage=usage,
            description=row['description'],
        )
        prefix = Prefix(net_address=row['netaddr'], vlan=vlan)
        return [vlan, prefix]


class UsageImporter(BulkImporter):
    """Creates objects from the usage bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(Usage, id=row['usageid'])
        usage = Usage(id=row['usageid'], description=row['descr'])
        return [usage]


class NetboxTypeImporter(BulkImporter):
    """Creates objects from the type bulk format"""

    def _create_objects_from_row(self, row):
        vendor = get_object_or_fail(Vendor, id=row['vendorid'])
        raise_if_exists(NetboxType, sysobjectid=row['sysobjectid'])
        raise_if_exists(NetboxType, vendor=vendor, name=row['typename'])

        netbox_type = NetboxType(
            vendor=vendor,
            name=row['typename'],
            sysobjectid=row['sysobjectid'],
            description=row['description'],
        )
        return [netbox_type]


class VendorImporter(BulkImporter):
    """Creates objects from the vendor bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(Vendor, id=row['vendorid'])
        vendor = Vendor(id=row['vendorid'])
        return [vendor]


class NetboxGroupImporter(BulkImporter):
    """Creates objects from the netboxgroup bulk format"""

    def _create_objects_from_row(self, row):
        raise_if_exists(NetboxGroup, id=row['netboxgroupid'])
        netboxgroup = NetboxGroup(
            id=row['netboxgroupid'], description=row['description']
        )
        return [netboxgroup]


class CablingImporter(BulkImporter):
    """Creates objects from the cabling bulk format"""

    def _create_objects_from_row(self, row):
        room = get_object_or_fail(Room, id=row['roomid'])
        raise_if_exists(Cabling, room=room, jack=row['jack'])
        cabling = Cabling(
            room=room,
            jack=row['jack'],
            building=row['building'],
            target_room=row['targetroom'],
            category=row['category'],
            description=row['descr'],
        )
        return [cabling]


class PatchImporter(BulkImporter):
    """Creates objects from the patch bulk format"""

    def _create_objects_from_row(self, row):
        netbox = get_object_or_fail(Netbox, sysname=row['sysname'])
        interface = get_object_or_fail(Interface, netbox=netbox, ifname=row['port'])
        room = get_object_or_fail(Room, id=row['roomid'])
        cabling = get_object_or_fail(Cabling, room=room, jack=row['jack'])

        if not row['split']:
            row['split'] = 'no'
        patch = Patch(interface=interface, cabling=cabling, split=row['split'])
        return [patch]


def get_object_or_fail(cls, **kwargs):
    """Gets the object as specified by the kwargs search arguments, and raises
    bulk errors if not found.

    cls -- Django ORM model to search for.
    kwargs -- search parameters for a cls.objects.get() call.

    """
    try:
        return cls.objects.get(**kwargs)
    except cls.DoesNotExist:
        raise DoesNotExist("%s does not exist: %r" % (cls.__name__, kwargs))
    except cls.MultipleObjectsReturned:
        raise MultipleObjectsReturned(
            "%s returned multiple: %r" % (cls.__name__, kwargs)
        )


def raise_if_exists(cls, **kwargs):
    """Raises AlreadyExists if an ORM object exists.

    cls -- Django ORM model to search for.
    kwargs -- search parameters for a cls.objects.get() call.

    """
    result = cls.objects.filter(**kwargs)
    if result.count() > 0:
        raise AlreadyExists("%s already exists: %r" % (cls.__name__, kwargs))


class BulkImportError(BulkParseError):
    "Import failed."

    pass


class DoesNotExist(BulkImportError):
    "Object does not exist"

    pass


class MultipleObjectsReturned(BulkImportError):
    "Multiple objects returned"

    pass


class AlreadyExists(BulkImportError):
    "Object already exist in database"

    pass


class InvalidValue(BulkImportError):
    """Invalid value"""

    pass


def reset_object_foreignkeys(obj):
    """Re-sets foreign key objects on obj.

    This makes sure that the ID's of foreignkey objects are updated on obj
    before obj.save() is attempted.

    """
    for field in get_foreign_key_fields(obj):
        value = getattr(obj, field.name)
        if value:
            setattr(obj, field.name, value)


def get_foreign_key_fields(obj):
    """Gets foreign key fields from this object"""
    return [field for field in obj._meta.get_fields() if field.many_to_one]

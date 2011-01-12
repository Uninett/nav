#
# Copyright (C) 2010 UNINETT
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
"""Import seed data in bulk."""

from nav.models.manage import Device, Netbox, Room, Organization
from nav.models.manage import Category, NetboxInfo
from nav.models.manage import Subcategory, NetboxCategory
from nav.models.manage import Location

from nav.bulkparse import *

from nav.models.manage import models

class BulkImporter(object):
    def __init__(self, parser):
        self.parser = parser

    def __iter__(self):
        return self

    def next(self):
        try:
            row = self.parser.next()
            objects = self.create_objects_from_row(row)
        except BulkParseError, error:
            objects = error
        return (self.parser.line_num, objects)

    def create_objects_from_row(self, row):
        raise Exception("Not Implemented")

class NetboxImporter(BulkImporter):
    def create_objects_from_row(self, row):
        raise_if_exists(Netbox, ip=row['ip'])
        raise_if_exists(Netbox, sysname=row['ip'])

        device = self.get_device_from_serial(row['serial'])
        netbox = self.get_netbox_from_row(row)
        netbox.device = device
        objects = [device, netbox]

        netboxinfo = self.get_netboxinfo_from_function(
            netbox, row['function'])
        if netboxinfo:
            objects.append(netboxinfo)

        subcats = self.get_subcats_from_subcat(netbox, row.get('subcat', []))
        if subcats:
            objects.extend(subcats)

        return objects

    def get_device_from_serial(self, serial):
        if not serial:
            return Device(serial='')

        try:
            device = Device.objects.get(serial=serial)
        except Device.DoesNotExist, e:
            return Device(serial=serial)
        else:
            return device

    def get_netbox_from_row(self, row):
        netbox = Netbox(ip=row['ip'], read_only=row['ro'],
                        read_write=row['rw'], snmp_version=1)
        netbox.room = get_object_or_fail(Room, id=row['roomid'])
        netbox.organization = get_object_or_fail(Organization, id=row['orgid'])
        netbox.category = get_object_or_fail(Category, id=row['catid'])
        netbox.sysname = netbox.ip
        return netbox

    def get_netboxinfo_from_function(self, netbox, function):
        if function:
            return NetboxInfo(netbox=netbox, key=None, variable='function',
                              value=function)

    def get_subcats_from_subcat(self, netbox, subcat):
        if not subcat:
            return

        subcats = []
        for subcatid in [s for s in subcat if s]:
            subcategory = get_object_or_fail(Subcategory, id=subcatid,
                                             category__id=netbox.category_id)
            subcats.append(NetboxCategory(netbox=netbox, category=subcategory))
        return subcats

class LocationImporter(BulkImporter):
    def create_objects_from_row(self, row):
        raise_if_exists(Location, id=row['locationid'])
        location = Location(id=row['locationid'],
                            description=row['descr'])
        return [location]

def get_object_or_fail(cls, **kwargs):
    try:
        return cls.objects.get(**kwargs)
    except cls.DoesNotExist, e:
        raise DoesNotExist("%s does not exist: %r" %
                           (cls.__name__, kwargs))

def raise_if_exists(cls, **kwargs):
    result = cls.objects.filter(**kwargs)
    if result.count() > 0:
        raise AlreadyExists("%s already exists: %r" %
                            (cls.__name__, kwargs))

class BulkImportError(BulkParseError):
    pass

class DoesNotExist(BulkImportError):
    pass

class AlreadyExists(BulkImportError):
    pass

def reset_object_foreignkeys(obj):
    """Re-sets foreign key objects on obj.

    This makes sure that the ID's of foreignkey objects are updated on obj
    before obj.save() is attempted.

    """
    foreign_fields = [field for field in obj._meta.fields
                      if isinstance(field, models.fields.related.ForeignKey)]
    for field in foreign_fields:
        value = getattr(obj, field.name)
        if value:
            setattr(obj, field.name, value)


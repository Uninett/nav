#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- testargs: -h -*-
#
# Copyright (C) 2010-2011, 2013-2015, 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Dumps core information from NAV to textfiles importable by SeedDB"""

import sys
import argparse
import json


from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.models import manage
import nav.models.service


_stdout = sys.stdout
SEPARATOR = ":"


def main():
    args = parse_args()

    if args.separator:
        global SEPARATOR
        SEPARATOR = args.separator

    if args.all:
        keys = [
            key
            for key, func in vars(Handlers).items()
            if type(func) is staticmethod and not key.startswith('_')
        ]
        for key in keys:
            filename = key + ".txt"
            sys.stdout = _stdout
            print("Dumping " + filename)
            try:
                # We're lazy and are using print all the way
                sys.stdout = open(filename, "w")
            except IOError as error:
                fail(2, "Could not open file %s: %s" % (args.output, error))
            handler = getattr(Handlers, key)
            handler()
        sys.exit(0)

    if args.output:
        try:
            # We're lazy and are using print all the way
            sys.stdout = open(args.output, "w")
        except IOError as error:
            fail(2, "Could not open file %s: %s" % (args.output, error))

    handler = getattr(Handlers(), args.table)

    # And run the handler
    handler()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Dumps NAV database seed data to importable files"
    )
    arg = parser.add_argument
    arg(
        "-s",
        "--separator",
        help="use SEP to separate fields in output, [default :]",
        metavar="SEP",
        default=":",
    )
    tables = sorted(
        table
        for table, func in vars(Handlers).items()
        if type(func) is staticmethod and not table.startswith('_')
    )
    arg(
        "-t",
        "--table",
        help="dump data from TABLE",
        default="",
        choices=tables,
        metavar="TABLE",
    )
    arg("-o", "--output", help="dump data to FILE instead of stdout", metavar="FILE")
    arg(
        "-a",
        "--all",
        dest="all",
        action="store_true",
        help="dump all tables to files named TABLE.txt",
    )

    args = parser.parse_args()
    if not (args.table or args.all):
        parser.error(
            "Please specify which tables to dump, using either --table or --all"
        )
    return args


def warn(msg):
    sys.stderr.write(msg + "\n")


def fail(resultcode, msg):
    warn(msg)
    sys.exit(resultcode)


def header(definition):
    """Output the header definition, possibly with replaced separators"""
    definition = definition.replace(":", SEPARATOR) + '\n'
    sys.stdout.write(definition)


def lineout(line):
    """Output line, remove any : in strings"""
    newline = ('"%s"' % column if SEPARATOR in column else column for column in line)
    line = SEPARATOR.join(newline) + '\n'
    sys.stdout.write(line)


class Handlers(object):
    """Contains methods for printing database info suitable for bulk import"""

    @staticmethod
    def netbox():
        """Outputs a line for each netbox in the database"""
        header(
            "#roomid:ip:orgid:catid:[management_profiles:master:function:"
            "key1=value1|key2=value2:"
            "devicegroup1:devicegroup2..]"
        )
        for box in manage.Netbox.objects.all():
            profiles = '|'.join(box.profiles.values_list('name', flat=True))
            data = '|'.join("%s=%s" % (k, v) for k, v in box.data.items())
            line = [
                box.room_id,
                box.ip,
                box.organization_id,
                box.category_id,
                profiles,
                box.master.sysname if box.master else "",
                box.get_function() or "",
                data,
            ]
            categories = sorted(box.groups.values_list('id', flat=True))
            line.extend(categories)
            lineout(line)

    @staticmethod
    def management_profile():
        """Outputs a line for each management profile in the database"""
        header("#name:protocol:option=value|option=value...")
        for profile in manage.ManagementProfile.objects.all():
            line = [
                profile.name,
                profile.get_protocol_display(),
                json.dumps(profile.configuration).replace('"', '""'),
            ]
            lineout(line)

    @staticmethod
    def org():
        header("#orgid[:parent:description:attribute=value[:attribute=value]]")
        for org in manage.Organization.objects.all():
            if org.parent:
                parent = org.parent.id
            else:
                parent = ""
            line = [org.id, parent, org.description or ""]
            line.extend(['%s=%s' % x for x in org.data.items()])
            lineout(line)

    @staticmethod
    def netboxgroup():
        header("#netboxgroupid:description")
        for netboxgroup in manage.NetboxGroup.objects.all():
            line = [netboxgroup.id, netboxgroup.description]
            lineout(line)

    @staticmethod
    def device_group():
        """Netbox group is a deprecated term, support the new term"""
        Handlers.netboxgroup()

    @staticmethod
    def usage():
        header("#usageid:descr")
        for usage in manage.Usage.objects.all():
            line = [usage.id, usage.description]
            lineout(line)

    @staticmethod
    def location():
        header("#locationid[:parent:descr]")
        for location in manage.Location.objects.all():
            line = [location.id, location.parent_id or '', location.description or '']
            lineout(line)

    @staticmethod
    def room():
        header("# roomid[:locationid:descr:position:attr=value:...]")
        for room in manage.Room.objects.all():
            line = [
                room.id,
                room.location_id if room.location_id else "",
                room.description or "",
            ]
            if room.position:
                line.append("(%s, %s)" % room.position)
            elif room.data:
                line.append('')
            line.extend(['%s=%s' % x for x in room.data.items()])
            lineout(line)

    @staticmethod
    def type():
        header("#vendorid:typename:sysoid[:description:cdp:tftp]")
        for netbox_type in manage.NetboxType.objects.all():
            line = [
                netbox_type.vendor.id,
                netbox_type.name,
                netbox_type.sysobjectid,
                netbox_type.description,
            ]
            lineout(line)

    @staticmethod
    def vendor():
        header("#vendorid")
        for vendor in manage.Vendor.objects.all():
            line = [vendor.id]
            lineout(line)

    @staticmethod
    def prefix():
        global SEPARATOR
        old_sep = SEPARATOR
        if SEPARATOR == ":":
            # IPv6 prefixes are full of colons
            warn("Not smart to use : as separator for prefixes, using ;")
            SEPARATOR = ";"
        header("#prefix/mask;nettype[;orgid;netident;usage;description;vlan]")
        for prefix in manage.Prefix.objects.all():
            vlan = prefix.vlan
            line = [
                prefix.net_address,
                vlan and vlan.net_type and vlan.net_type.id or "",
            ]
            if vlan:
                line.append(vlan.organization and vlan.organization.id or "")
                line.append(vlan.net_ident or "")
                line.append(vlan.usage and vlan.usage.id or "")
                line.append(vlan.description or "")
                line.append(vlan.vlan and str(vlan.vlan) or "")
            lineout(line)
        SEPARATOR = old_sep

    @staticmethod
    def service():
        global SEPARATOR
        old_sep = SEPARATOR
        if SEPARATOR == ":":
            # (since it is used in URLs for HTTP checker and we don't
            # have a defined way to escape it)
            warn("Not smart to use : as separator for services, using ;")
            SEPARATOR = ";"
        header("#ip/sysname:handler[:arg=value[:arg=value]]")
        all_services = nav.models.service.Service.objects.all()
        for service in all_services.prefetch_related('properties'):
            line = [service.netbox.sysname, service.handler]
            properties = [
                "%s=%s" % (p.property, p.value) for p in service.properties.all()
            ]
            line.extend(properties)
            lineout(line)
        SEPARATOR = old_sep


if __name__ == "__main__":
    main()

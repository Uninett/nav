#!/usr/bin/env python3
#
# Copyright (C) 2006, 2010, 2020 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""This script produces PostgreSQL INSERT (or actually, "UPSERT") statements suitable
to synchronize the IP Device type registry of one NAV installation based on the
information contained in another.
"""

import argparse

import nav.db
from nav.bootstrap import bootstrap_django

bootstrap_django("synctypes")
from nav.models.manage import NetboxType


VENDOR_INSERT_SQL_TEMPLATE = """
INSERT INTO vendor
(SELECT {vendorid} AS vendorid
 WHERE NOT EXISTS (
  SELECT vendorid FROM vendor WHERE vendorid ILIKE {vendorid}
 )
);
"""

TYPE_UPSERT_SQL_TEMPLATE = """
INSERT INTO "type" (vendorid, typename, sysobjectid, descr)
VALUES (
  (SELECT vendorid FROM vendor WHERE vendorid ILIKE {vendorid}),
  {typename},
  {sysobjectid},
  {descr}
) ON CONFLICT (sysobjectid) DO UPDATE
  SET
    vendorid=(SELECT vendorid FROM vendor WHERE vendorid ILIKE {vendorid}),
    typename={typename},
    descr={descr};

"""


def main():
    """Main program"""
    parse_args()
    types = NetboxType.objects.all().select_related("vendor")
    used_vendors = {t.vendor.id for t in types}
    if types:
        print("-- This SQL script needs at least PostgreSQL 9.5 to work --")
        print("BEGIN;\n")
        print("-- Vendor definitions --\n")
        for vendor in used_vendors:
            print_vendor(vendor)

        print("-- Netbox type definitions --\n")
        for typ in types:
            print_type(typ)

        print("\nCOMMIT;")


def print_vendor(vendor: str):
    """Prints an SQL statement to ensure a vendor entry is synced.

    Vendor ID's are case sensitive, so the statement will try work case
    insensitively to avoid inserting 'duplicate' records due to casing changes.
    """
    sql = VENDOR_INSERT_SQL_TEMPLATE.format(vendorid=escape(vendor))
    print(sql)


def print_type(typ: NetboxType):
    """Prints an SQL statement to ensure a type entry is synced"""
    sql = TYPE_UPSERT_SQL_TEMPLATE.format(
        vendorid=escape(typ.vendor.id),
        typename=escape(typ.name),
        sysobjectid=escape(typ.sysobjectid),
        descr=escape(typ.description),
    )
    print(sql)


def escape(v):
    """Escape a value before entering it in to the db"""
    return nav.db.escape(str(v)) if v is not None else "NULL"


def parse_args():
    """Parses command line arguments using argparse"""
    parser = argparse.ArgumentParser(
        description="NAV type registry synchronizer",
        epilog="This program dumps this NAV installation's IP device type registry to "
        "STDOUT as a PostgreSQL compatible script. The resulting script can be used to "
        "synchronize the type registry of another NAV installation. The script will "
        "add missing types and update existing type names and descriptions.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()

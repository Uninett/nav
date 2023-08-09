#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- testargs: --arp -*-
#
# Copyright (C) 2017 Uninett AS
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
"""Deletes old data from the NAV database"""
from __future__ import print_function

import sys
import argparse

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

import psycopg2
from django.db.transaction import atomic
from django.contrib.sessions.models import Session
from django.utils import timezone

import nav.db


def main(args):
    """Main execution function."""
    parser = make_argparser()
    args = parser.parse_args()

    if args.interval:
        expiry = "NOW() - interval %s" % nav.db.escape(args.interval)
    elif args.datetime:
        expiry = args.datetime

    connection = nav.db.getConnection('default', 'manage')
    deleters = get_selected_deleters(args, connection)

    deleted = False
    for deleter in deleters:
        try:
            count = deleter.delete(expiry, dry_run=not args.force)
            if not args.quiet:
                print(
                    "Expired records in {table}: {count}".format(
                        table=deleter.table, count=count if count is not None else "N/A"
                    )
                )
            deleted = True

        except psycopg2.Error as error:
            print("The PostgreSQL backend produced an error", file=sys.stderr)
            print(error, file=sys.stderr)
            connection.rollback()
            sys.exit(1)

    if not args.force:
        connection.rollback()
        deleted = False
    else:
        connection.commit()

    if not args.quiet:
        if deleted:
            print("Expired records were deleted.")
        else:
            print("Nothing deleted.")

    connection.close()


#
# helper functions
#


def make_argparser():
    """Makes this program's ArgumentParser"""
    parser = argparse.ArgumentParser(
        description="Deletes old data from the NAV database",
        epilog="Unless options are given, the number of expired records will "
        "be printed. The default expiry limit is 6 months. The -e and -E"
        " options set a common expiry date for all selected tables. If "
        "you want different expiry dates for each table, you need to "
        "run navclean more than once. To actually delete the expired "
        "records, add the -f option.",
    )
    arg = parser.add_argument

    arg("-q", "--quiet", action="store_true", help="be quiet")
    arg("-f", "--force", action="store_true", help="force deletion of expired records")
    arg(
        "-e",
        "--datetime",
        type=postgresql_datetime,
        help="set an explicit expiry date on ISO format",
    )
    arg(
        "-E",
        "--interval",
        type=postgresql_interval,
        default="6 months",
        help="set an expiry interval using PostgreSQL interval syntax, e.g. "
        "'30 days', '4 weeks', '6 months'",
    )

    arg("--arp", action="store_true", help="delete from ARP table")
    arg("--cam", action="store_true", help="delete from CAM table")
    arg("--radiusacct", action="store_true", help="delete from Radius accounting table")
    arg("--radiuslog", action="store_true", help="delete from Radius error log table")
    arg("--netbox", action="store_true", help="delete from NETBOX table")
    arg("--websessions", action="store_true", help="delete expired web sessions")

    return parser


def validate_sql(sql, args):
    """Validates than an SQL statement can run without errors"""
    connection = nav.db.getConnection('default', 'manage')
    cursor = connection.cursor()
    try:
        cursor.execute(sql, args)
    except psycopg2.DataError as error:
        raise ValueError(error)
    finally:
        connection.rollback()
    return True


def postgresql_datetime(value):
    """Validates a user-input value as a PostgreSQL timestamp string"""
    if validate_sql('SELECT TIMESTAMP %s', (value,)):
        return value


def postgresql_interval(value):
    """Validates a user-input value as a PostgreSQL interval string"""
    if validate_sql("SELECT INTERVAL %s", (value,)):
        return value


def get_selected_deleters(args, connection):
    """Returns a list of RecordDeleter instances for each of the tables
    selected in the supplied ArgumentParser.
    """
    return [
        deleter(connection)
        for deleter in RecordDeleter.__subclasses__()
        if getattr(args, deleter.table, False)
    ]


#
# Deleter implementations
#


class RecordDeleter(object):
    """Base class for record deletion"""

    table = None
    selector = ""

    def __init__(self, connection):
        self.connection = connection

    def filter(self, expiry):
        """Returns a selector statement formatted with the supplied expiry"""
        return self.selector.format(expiry=expiry)

    def sql(self, expiry):
        """Returns the full DELETE statement based on the expiry date"""
        where = self.filter(expiry)
        return 'DELETE FROM {table} {filter}'.format(table=self.table, filter=where)

    def delete(self, expiry, dry_run=False):
        """Deletes the records selected by the expiry spec"""
        cursor = self.connection.cursor()
        sql = self.sql(expiry)
        cursor.execute(sql)
        return cursor.rowcount


# pylint: disable=missing-docstring


class ArpDeleter(RecordDeleter):
    table = "arp"
    selector = "WHERE end_time < {expiry}"


class CamDeleter(RecordDeleter):
    table = "cam"
    selector = "WHERE end_time < {expiry}"


class RadiusAcctDeleter(RecordDeleter):
    table = "radiusacct"
    selector = """
        WHERE (acctstoptime < {expiry})
        OR ((acctstarttime + (acctsessiontime * interval '1 sec')) < {expiry})
        OR (acctstarttime < {expiry} 
            AND (acctstarttime + (acctsessiontime * interval '1 sec')) IS NULL)
        """


class RadiusLogDeleter(RecordDeleter):
    table = "radiuslog"
    selector = "WHERE time < {expiry}"


class NetboxDeleter(RecordDeleter):
    table = "netbox"
    selector = "WHERE pg_try_advisory_lock(netboxid) and deleted_at IS NOT NULL"


class SessionDeleter(RecordDeleter):
    """Special case deleter for Django Sessions"""

    table = "websessions"

    @atomic
    def delete(self, expiry, dry_run=False):
        """Deletes all expired django sessions if not a dry_run.

        Expiry spec is ignored, as sessions have a different expiry mechanism.
        """
        expired = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired.count()
        if dry_run:
            return count
        expired.delete()
        return count


if __name__ == '__main__':
    main(sys.argv[1:])

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- testargs: --arp -*-
# -*- testargs: --close-arp -*-
#
# Copyright (C) 2017 Uninett AS
# Copyright (C) 2024 Sikt
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
"""Cleans old data from the NAV database"""

import argparse
import sys

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

import psycopg2
from django.db.transaction import atomic
from django.contrib.sessions.models import Session
from django.utils import timezone

import nav.db


def main():
    """Main execution function."""
    parser = make_argparser()
    args = parser.parse_args()

    if args.interval:
        expiry = "NOW() - interval %s" % nav.db.escape(args.interval)
    elif args.datetime:
        expiry = args.datetime

    connection = nav.db.getConnection('default', 'manage')
    cleaners = get_selected_cleaners(args, connection)

    cleaned = False
    for cleaner in cleaners:
        try:
            count = cleaner.clean(expiry, dry_run=not args.force)
            if not args.quiet:
                print(
                    "Expired {expiry_type} records: {count}".format(
                        expiry_type=cleaner.expiry_type,
                        count=count if count is not None else "N/A",
                    )
                )
            cleaned = True

        except psycopg2.Error as error:
            print("The PostgreSQL backend produced an error", file=sys.stderr)
            print(error, file=sys.stderr)
            connection.rollback()
            sys.exit(1)

    if not args.force:
        connection.rollback()
        cleaned = False
    else:
        connection.commit()

    if not args.quiet:
        if cleaned:
            print("Expired records were updated/deleted.")
        else:
            print("Nothing changed.")

    connection.close()


#
# helper functions
#


def make_argparser():
    """Makes this program's ArgumentParser"""
    parser = argparse.ArgumentParser(
        description="Cleans old data from the NAV database",
        epilog="Cleaning old data means either deleting old records, or updating "
        "expired records.  Use options to select which types of data to clean. "
        "The -e and -E options set an expiry date that applies to all "
        "selected data types.  Every run is a dry-run by default, unless the "
        "-f option is given, in order to avoid accidental data deletion.",
    )
    arg = parser.add_argument

    arg("-q", "--quiet", action="store_true", help="Be quiet")
    arg("-f", "--force", action="store_true", help="Force actual database updates")
    arg(
        "-e",
        "--datetime",
        type=postgresql_datetime,
        help="Set an explicit expiry date on ISO format",
    )
    arg(
        "-E",
        "--interval",
        type=postgresql_interval,
        default="6 months",
        help="Set an expiry interval using PostgreSQL interval syntax, e.g. "
        "'30 days', '4 weeks', '6 months', '30 minutes'",
    )

    arg("--arp", action="store_true", help="Delete old records from ARP table")
    arg(
        "--close-arp",
        action="store_true",
        help="Close expired ARP records. Expired records are those where the netbox "
        "has been down for longer than the set expiry limit",
    )
    arg("--cam", action="store_true", help="Delete old records from CAM table")
    arg(
        "--radiusacct",
        action="store_true",
        help="Delete old records from Radius accounting table",
    )
    arg(
        "--radiuslog",
        action="store_true",
        help="Delete old records from Radius error log table",
    )
    arg(
        "--netbox",
        action="store_true",
        help="Delete netboxes that have been marked for deletion by Seed Database",
    )
    arg("--websessions", action="store_true", help="Delete expired web sessions")

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


def get_selected_cleaners(
    args: argparse.Namespace, connection
) -> list["RecordCleaner"]:
    """Returns a list of RecordCleaner instances for each of the tables
    selected in the supplied ArgumentParser.
    """
    return [
        cleaner(connection)
        for cleaner in RecordCleaner.__subclasses__()
        if getattr(args, cleaner.expiry_type, False)
    ]


#
# Cleaner implementations
#


class RecordCleaner:
    """Base class for record cleaning"""

    expiry_type = None
    selector = ""

    def __init__(self, connection):
        self.connection = connection

    def filter(self, expiry):
        """Returns a selector statement formatted with the supplied expiry"""
        return self.selector.format(expiry=expiry)

    def sql(self, expiry):
        """Returns the full DELETE statement based on the expiry date.  Override this
        method if a different kind of update statement is needed.
        """
        where = self.filter(expiry)
        return 'DELETE FROM {table} {filter}'.format(
            table=self.expiry_type, filter=where
        )

    def clean(self, expiry: str, dry_run: bool = False):
        """Cleans the records selected by the expiry spec"""
        cursor = self.connection.cursor()
        sql = self.sql(expiry)
        cursor.execute(sql)
        return cursor.rowcount


class ArpDeleter(RecordCleaner):
    expiry_type = "arp"
    selector = "WHERE end_time < {expiry}"


class ArpCloser(RecordCleaner):
    """Closes ARP records that have "expired", i.e. they're open, but the netbox they
    were collected from has been down for too long.
    """

    expiry_type = "close_arp"

    def sql(self, expiry):
        """Returns the full UPDATE statement based on the expiry date"""
        return f"""
            WITH unreachable_devices AS (
                SELECT
                    netboxid,
                    start_time AS downsince
                FROM
                    alerthist
                WHERE
                    eventtypeid = 'boxState'
                    AND end_time >= 'infinity'
            )
            UPDATE
                arp
            SET
                end_time = NOW()
            WHERE
                netboxid IN (
                    SELECT
                        netboxid
                    FROM
                        unreachable_devices
                    WHERE
                        downsince < {expiry})
                AND end_time >= 'infinity'
        """


class CamDeleter(RecordCleaner):
    expiry_type = "cam"
    selector = "WHERE end_time < {expiry}"


class RadiusAcctDeleter(RecordCleaner):
    expiry_type = "radiusacct"
    selector = """
        WHERE (acctstoptime < {expiry})
        OR ((acctstarttime + (acctsessiontime * interval '1 sec')) < {expiry})
        OR (acctstarttime < {expiry}
            AND (acctstarttime + (acctsessiontime * interval '1 sec')) IS NULL)
        """


class RadiusLogDeleter(RecordCleaner):
    expiry_type = "radiuslog"
    selector = "WHERE time < {expiry}"


class NetboxDeleter(RecordCleaner):
    expiry_type = "netbox"
    selector = "WHERE pg_try_advisory_lock(netboxid) and deleted_at IS NOT NULL"


class SessionDeleter(RecordCleaner):
    """Special case deleter for Django Sessions"""

    expiry_type = "websessions"

    @atomic
    def clean(self, expiry, dry_run=False):
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
    main()

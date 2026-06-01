#
# Copyright (C) 2014, 2019 Uninett AS
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Controllers for WatchDog requests"""

from django.shortcuts import render
from django.db import connection

from nav.models.fields import INFINITY
from nav.models.manage import Arp, Device, Netbox
from nav.web.utils import create_title
from nav.watchdog.util import get_statuses


def render_index(request):
    """Controller for WatchDog index"""
    navpath = [("Home", "/"), ("WatchDog",)]

    context = {
        "navpath": navpath,
        "title": create_title(navpath),
        "tests": get_statuses(),
    }

    return render(request, "watchdog/base.html", context)


def get_netbox(request):
    """Returns a fragment with the total number of registered IP devices"""
    return render(
        request,
        "watchdog/frag_count.html",
        {"count": Netbox.objects.count()},
    )


def get_serial_numbers(request):
    """Returns a fragment with the number of distinct device serial numbers"""
    return render(
        request,
        "watchdog/frag_count.html",
        {"count": Device.objects.distinct("serial").count()},
    )


def get_arp_count(request):
    """Returns a fragment with an estimated count of ARP records"""
    return _render_count_estimate(request, "arp")


def get_cam_count(request):
    """Returns a fragment with an estimated count of CAM records"""
    return _render_count_estimate(request, "cam")


def get_active_addresses(request):
    """Returns a fragment with counts of currently active IP addresses"""
    active = Arp.objects.filter(end_time=INFINITY)
    return render(
        request,
        "watchdog/frag_active_addresses.html",
        {
            "active": active.count(),
            "ipv4": active.extra(where=["family(ip)=4"]).count(),
            "ipv6": active.extra(where=["family(ip)=6"]).count(),
        },
    )


def get_database_size(request):
    """Returns a fragment with the on-disk size of the NAV PostgreSQL database"""
    cursor = connection.cursor()
    return render(
        request,
        "watchdog/frag_db_size.html",
        {"size": get_postgres_db_size(cursor)},
    )


#
# Helper functions
#


def _render_count_estimate(request, table):
    """Renders an estimate-count fragment for arp/cam-shaped tables"""
    cursor = connection.cursor()
    return render(
        request,
        "watchdog/frag_count_estimate.html",
        {
            "count": get_tuple_count_estimate(cursor, table),
            "oldest": get_oldest_start_time_date(cursor, table),
        },
    )


def get_tuple_count_estimate(cursor, table):
    """Returns PostgreSQL's estimate number of live tuples in table"""
    query = """SELECT n_live_tup
               FROM pg_stat_all_tables
               WHERE relname = %s"""
    cursor.execute(query, (table,))
    row = cursor.fetchone()
    return row[0]


def get_oldest_start_time_date(cursor, table):
    """Returns the date of the oldest closed ARP/CAM record (or from any log table
    using the same start_time/end_time principle as the arp/cam tables

    """
    query = """SELECT start_time::DATE
                FROM
                 (SELECT start_time
                  FROM {table}
                  WHERE end_time < 'infinity'
                  ORDER BY start_time ASC
                  LIMIT 1) AS foo"""
    cursor.execute(query.format(table=table))
    row = cursor.fetchone()
    return row[0] if row else None


def get_postgres_db_size(cursor):
    """Returns the size of the PostgreSQL database as a pretty string"""
    query = """SELECT pg_size_pretty( pg_database_size( current_database() ) )"""
    cursor.execute(query)
    row = cursor.fetchone()
    return row[0] if row else None

#
# Copyright (C) 2014, 2019 Uninett AS
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
"""Controllers for WatchDog requests"""

from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection

from nav.models.fields import INFINITY
from nav.models.manage import Arp, Device
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


def get_active_addresses(_):
    """Get active addresses on the network"""
    active = Arp.objects.filter(end_time=INFINITY)
    num_active = active.count()
    num_active_ipv6 = active.extra(where=["family(ip)=6"]).count()
    num_active_ipv4 = active.extra(where=["family(ip)=4"]).count()
    return JsonResponse(
        {"active": num_active, "ipv6": num_active_ipv6, "ipv4": num_active_ipv4}
    )


def get_cam_and_arp(_request):
    """Get cam and arp numbers"""
    cursor = connection.cursor()
    return JsonResponse(
        {
            "cam": get_cam(cursor),
            "arp": get_arp(cursor),
            "oldest_cam": get_oldest_cam_date(cursor),
            "oldest_arp": get_oldest_arp_date(cursor),
        }
    )


def get_database_size(_request):
    """Gets the size of the PostgreSQL database"""
    cursor = connection.cursor()
    return JsonResponse({"size": get_postgres_db_size(cursor)})


#
# Helper functions
#


def get_cam(cursor):
    """Gets number of cam records"""
    return get_tuple_count_estimate(cursor, "cam")


def get_oldest_cam_date(cursor):
    """Returns the date of the oldest closed CAM record"""
    return get_oldest_start_time_date(cursor, "cam")


def get_arp(cursor):
    """Gets number of arp records"""
    return get_tuple_count_estimate(cursor, "arp")


def get_oldest_arp_date(cursor):
    """Returns the date of the oldest closed ARP record"""
    return get_oldest_start_time_date(cursor, "arp")


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


def get_serial_numbers(_):
    """Get number of distinct serial numbers in NAV"""
    return JsonResponse({"count": Device.objects.distinct("serial").count()})

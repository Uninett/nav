#
# Copyright (C) 2014 Uninett AS
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
    navpath = [('Home', '/'), ('WatchDog', )]

    context = {
        'navpath': navpath,
        'title': create_title(navpath),
        'tests': get_statuses()
    }

    return render(request, 'watchdog/base.html', context)


def get_active_addresses(_):
    """Get active addresses on the network"""
    active = Arp.objects.filter(end_time=INFINITY)
    num_active = active.count()
    num_active_ipv6 = active.extra(where=['family(ip)=6']).count()
    num_active_ipv4 = active.extra(where=['family(ip)=4']).count()
    return JsonResponse({
        'active': num_active,
        'ipv6': num_active_ipv6,
        'ipv4': num_active_ipv4
    })


def get_cam_and_arp(_request):
    """Get cam and arp numbers"""
    cursor = connection.cursor()
    return JsonResponse({
        'cam': get_cam(cursor),
        'arp': get_arp(cursor)
    })


def get_cam(cursor):
    query = """SELECT n_live_tup
               FROM pg_stat_all_tables
               WHERE relname = 'cam'"""
    cursor.execute(query)
    row = cursor.fetchone()
    return row[0]


def get_arp(cursor):
    """Gets number of arp records"""
    query = """SELECT n_live_tup
               FROM pg_stat_all_tables
               WHERE relname = 'arp'"""
    cursor.execute(query)
    row = cursor.fetchone()
    return row[0]


def get_serial_numbers(_):
    """Get number of distinct serial numbers in NAV"""
    return JsonResponse({'count': Device.objects.distinct('serial').count()})

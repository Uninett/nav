#
# Copyright (C) 2007, 2010, 2011 UNINETT AS
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
"""Netmap mod_python handler"""

import nav.db
import psycopg2.extras

#from nav.web.netmap.common import *
from nav.web.netmap.datacollector import getData

from nav.web.templates.GraphML import GraphML
from nav.web.templates.Netmap import Netmap

from django.http import HttpResponse
from nav.django.utils import get_account

def index(req):
    """The main Netmap view, embedding the Java applet"""
    page = Netmap()
    page.sessionID = _get_session_cookie(req)
    base_url = req.build_absolute_uri()
    page.baseURL = base_url[:-1]
    account = get_account(req)
    if account.has_perm(None, None):
        page.is_admin = "True"
    else:
        page.is_admin = "False"

    return HttpResponse(page.respond(),
                        mimetype='text/html')

def output_graph_data(req):
    """Outputs the network graph as GraphML"""
    cursor = _get_db_cursor()
    page = GraphML()
    data = getData(cursor)
    page.netboxes = data[0]
    page.connections = data[1]
    base_url = req.build_absolute_uri()
    page.baseURL = base_url[:base_url.rfind('/')]

    return HttpResponse(page.respond(),
                        mimetype='text/xml')

def save_positions(req):
    """Saves absolute node positions from the map to the database"""
    # Check if user is admin
    account = get_account(req)
    if not account.has_perm(None, None):
        return HttpResponseUnauthorized()

    positions = {}
    for key, value in req.REQUEST.items():
        try:
            sysname, direction = key.split("_")
            position = float(value or 0.0)
        except ValueError:
            continue
        if not sysname or not direction or not position:
            continue
        if sysname not in positions:
            positions[sysname] = [0.0, 0.0]
        if direction == "x":
            positions[sysname][0] = position
        elif direction == "y":
            positions[sysname][1] = position

    cursor = _get_db_cursor()
    for sysname in positions.keys():
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM netmap_position
            WHERE sysname = %s
            """, (sysname,))
        result = cursor.fetchall()
        if result[0][0] > 0:
            cursor.execute(
                """
                UPDATE netmap_position
                SET xpos = %s, ypos = %s
                WHERE sysname = %s
                """, (positions[sysname][0], positions[sysname][1],
                      sysname))
        else:
            cursor.execute(
                """
                INSERT INTO netmap_position(xpos, ypos, sysname)
                VALUES (%s, %s, %s)
                """, (positions[sysname][1], positions[sysname][1],
                      sysname))

    return HttpResponse(mimetype="text/plain")

def category_list(_):
    """Outputs a comma separated list of available netbox categories"""
    cursor = _get_db_cursor()
    cursor.execute("SELECT catid FROM cat ORDER BY catid")
    result = cursor.fetchall()

    return HttpResponse(",".join(r[0] for r in result) + ",",
                        mimetype="text/plain")

def linktype_list(_):
    """Outputs a comma separated list of available link types"""
    cursor = _get_db_cursor()
    cursor.execute("SELECT nettypeid FROM nettype ORDER BY nettypeid")
    result = cursor.fetchall()

    return HttpResponse(",".join(r[0] for r in result) + ",",
                        mimetype="text/plain")


def _get_session_cookie(request):
    return "nav_sessid=%s" % request.COOKIES.get('nav_sessid', None)

def _get_db_cursor():
    connection = nav.db.getConnection('netmapserver', 'manage')
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return cursor


class HttpResponseUnauthorized(HttpResponse):
    """A HttpResponse defaulting to a 401 UNAUTHORIZED status code"""
    def __init__(self):
        super(HttpResponseUnauthorized, self).__init__()
        self.status_code = 401

#
# Copyright (C) 2007, 2010 UNINETT AS
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

import sys
import nav.db
import datetime
import psycopg2.extras

from nav.web.netmap.common import *
from nav.web.netmap.datacollector import *

from mod_python import Cookie
try:
    from mod_python import apache
except ImportError:
    apache = None

from nav.web.templates.GraphML import GraphML
from nav.web.templates.Netmap import Netmap

from nav.models.profiles import Account

def get_account(req):
    """Inspects the mod_python req structure and returns a Django Account
    object for the corresponding user.
    """
    account = Account.objects.get(login=req.session['user']['login'])
    return account

def handler(req):

    path = req.filename[req.filename.rfind('/'):]

    connection = nav.db.getConnection('netmapserver', 'manage')
    db = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)


    try:
        if req.is_https():
            baseURL = "https://" + req.hostname + req.uri
        else:
            baseURL = "http://" + req.hostname + req.uri
    except AttributeError:
        if req.subprocess_env.get('HTTPS', '').lower() in ('on', '1'):
            baseURL = "https://" + req.hostname + req.uri
        else:
            baseURL = "http://" + req.hostname + req.uri

    account = get_account(req)
    if path == '/server':
        page = GraphML()
        data = getData(db)
        page.netboxes = data[0]
        page.connections = data[1]
        page.baseURL = baseURL[:baseURL.rfind('/')]

        req.content_type="text/xml; charset=utf-8"
        req.send_http_header()

        req.write(page.respond().encode('utf-8'))

        return apache.OK

    # Save positions for later usage
    elif path == '/position':
        # Check if user is admin
        if not account.has_perm(None, None):
            return apache.HTTP_UNAUTHORIZED

        from mod_python.util import FieldStorage
        form = FieldStorage(req)
        req.content_type="text/plain"
        req.send_http_header()

        positions = {}
        for key in form.keys():
            try:
                sysname,direction = key.split("_")
                position = float(form.get(key, 0.0))
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

        for sysname in positions.keys():
            db.execute("SELECT COUNT(*) FROM netmap_position WHERE sysname = '%s'" % sysname)
            result = db.fetchall()
            if result[0][0] > 0:
                db.execute("UPDATE netmap_position SET xpos = %s, ypos = %s WHERE sysname = '%s'" % (positions[sysname][0], positions[sysname][1], sysname))
            else:
                db.execute("INSERT INTO netmap_position(xpos, ypos, sysname) VALUES (%s, %s, '%s')" % (positions[sysname][1], positions[sysname][1], sysname))


        return apache.OK



    #Fetch categories
    elif path == '/catids':
        db.execute("SELECT catid FROM cat ORDER BY catid")
        result = db.fetchall()

        req.content_type="text/plain"
        req.send_http_header()
        for cat in result:
            req.write(cat[0] + ",")
        return apache.OK

    elif path == '/linktypes':
        db.execute("SELECT nettypeid FROM nettype ORDER BY nettypeid")
        result = db.fetchall()

        req.content_type="text/plain"
        req.send_http_header()
        for type in result:
            req.write(type[0] + ",")
        return apache.OK

    elif path == '/':
        cookies = Cookie.get_cookies(req)
        if not cookies.get('nav_sessid', None):
            return apache.HTTP_UNAUTHORIZED

        page = Netmap()
        page.sessionID = cookies['nav_sessid']
        page.baseURL = baseURL[:-1]
        if account.has_perm(None, None):
            page.is_admin = "True"
        else:
            page.is_admin = "False"
        req.content_type="text/html"
        req.send_http_header()

        req.write(page.respond())

        return apache.OK

    else:
        return apache.HTTP_NOT_FOUND

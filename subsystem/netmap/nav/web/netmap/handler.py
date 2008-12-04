# -*- coding: UTF-8 -*-
#
# Copyright 2007 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Kristian Klette <klette@samfundet.no>

import sys
import psycopg
import nav.db
import datetime

from nav.web.netmap.common import *
from nav.web.netmap.datacollector import *

from nav import auth

from mod_python import apache, util, Cookie
from mod_python.util import FieldStorage

from nav.web.templates.GraphML import GraphML
from nav.web.templates.Netmap import Netmap

def handler(req):

    path = req.filename[req.filename.rfind('/'):]

    connection = nav.db.getConnection('netmapserver', 'manage')
    db = connection.cursor()


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

    if path == '/server':
        page = GraphML()
        data = getData(db)
        page.netboxes = data[0]
        page.connections = data[1]
        page.baseURL = baseURL[:baseURL.rfind('/')]

        req.content_type="text/xml"
        req.send_http_header()

        req.write(page.respond());

        return apache.OK

    # Save positions for later usage
    elif path == '/position':
        # Check if user is admin
        if not auth.hasPrivilege(req.session['user'], None, None):
            return apache.HTTP_UNAUTHORIZED

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
        if not cookies['nav_sessid']:
            return apache.HTTP_UNAUTHORIZED

        page = Netmap()
        page.sessionID = cookies['nav_sessid']
        page.baseURL = baseURL[:-1]
        if auth.hasPrivilege(req.session['user'], None, None):
            page.is_admin = "True"
        else:
            page.is_admin = "False"
        req.content_type="text/html"
        req.send_http_header()

        req.write(page.respond())

        return apache.OK

    else:
        return apache.HTTP_NOT_FOUND

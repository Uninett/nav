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

from mod_python import apache, util, Cookie

from nav.web.templates.GraphML import GraphML
from nav.web.templates.Netmap import Netmap

def handler(req):

    path = req.filename[req.filename.rfind('/'):]

    connection = nav.db.getConnection('netmapserver', 'manage')
    db = connection.cursor()

    if req.is_https():
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

    #Fetch categories
    elif path == '/catids':
       db.execute("SELECT catid FROM cat ORDER BY catid")
       result = db.fetchall()

       req.content_type="text/plain"
       req.send_http_header()
       for cat in result:
           req.write(cat[0] + ",")
       return apache.OK

    elif path == '/':
        cookies = Cookie.get_cookies(req)
        if not cookies['nav_sessid']:
            return apache.HTTP_UNAUTHORIZED

        page = Netmap()
        page.sessionID = cookies['nav_sessid']
        page.baseURL = baseURL[:-1]
        (cookies['nav_sessid'], cookies['nav_sessid'])
        req.content_type="text/html"
        req.send_http_header()

        req.write(page.respond())

        return apache.OK

    else:
        return apache.HTTP_NOT_FOUND

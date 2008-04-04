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

def handler(req):

    path = req.filename[req.filename.rfind('/'):]

    connection = nav.db.getConnection('netmapserver', 'manage')
    db = connection.cursor()

    if path == '/server':
        page = GraphML()
        data = getData(db)
        page.netboxes = data[0]
        page.connections = data[1]

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

        out = """
<html>
<body>

 <!--[if !IE]>-->
      <object classid="java:no.uninett.netmap.Main" type="application/x-java-applet;version=1.5.0" archive="applet/Netmap_0.2.jar" width="800" height="600">
        <param name="archive" value="applet/Netmap_0.2.jar" />
        <param name="sessionid" value="%s">
        <param name="baseurl" value="https://navdev.uninett.no">
      <!--<![endif]-->
      <object classid="clsid:8AD9C840-044E-11D1-B3E9-00805F499D93" codebase="http://java.sun.com/getjava/index.jsp" width="800" height="600">

        <param name="code" value="no.uninett.netmap.Main">
        <param name="archive" value="applet/Netmap_0.2.jar">
        <param name="sessionid" value="%s">
        <param name="baseurl" value="https://navdev.uninett.no">
        <strong>
        No Java Plug-in found.<br />
          <a href="http://java.sun.com/getjava/index.jsp">Please download and install one.</a>
        </strong>
      </object>
      <!--[if !IE]>-->

      </object>
      <!--<![endif]-->

</body>
            """ % (cookies['nav_sessid'], cookies['nav_sessid'])
        req.content_type="text/html"
        req.send_http_header()

        req.write(out)

        return apache.OK

    else:
        return apache.HTTP_NOT_FOUND

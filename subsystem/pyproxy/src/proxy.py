#!/usr/bin/env python
#
# Copyright 2002-2004 Norwegian University of Science and Technology
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
#
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

import os
import sys
import time
import warnings
import traceback
import httplib
from mod_python import apache


import nav.web
from nav.web.templates.DeviceBrowserTemplate import DeviceBrowserTemplate


SERVERBASE='localhost'
SERVERPORT=8080

def handler(req):
    remotecookie = req.session.get('navadmin-cookie')

    if req.args:
        proxyreq = "%s?%s" % (req.uri, req.args)
    else:
        proxyreq = req.uri
    if req.method == 'POST':
        postdata = req.read()
    else:
        postdata = ''
    response = doRequest(proxyreq, req.method, remotecookie, query=postdata)
    remoteanswer = response.read()
    req.content_type = response.msg.dict['content-type']
    if not req.content_type.startswith('text'):
        req.send_http_header()
        req.write(remoteanswer)
        return apache.OK

    try:
        cookie = response.msg.dict['set-cookie']
        cookie = cookie[:cookie.find(';')]
        req.session['navadmin-cookie'] = cookie
        req.session.save()
    except KeyError:
        pass
    
    req.session.setdefault('uris', [])
    templatePath = [] # add logical paths to thhis
    templatePath.append(("Home", "/"))
    templatePath.append(("Network explorer",
                         "/navAdmin/servlet/navAdmin?section=ni&func=visTopologi"))

    template = DeviceBrowserTemplate()
    template.path = []

    # Our template defines the variable myContent and treeselect.
    # Of course we can add more of them
    template.myContent = remoteanswer
    template.treeselect = None
    template.path = templatePath

    response = template.respond()

    req.send_http_header()
    req.write(response)
    return apache.OK
    

def doRequest(path, method, cookie, query=''):
    request = httplib.HTTPConnection(SERVERBASE, SERVERPORT)
    if method == 'POST':
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
    else:
        headers = {}
    headers['Cookie']=cookie
    request.request(method, path, query, headers)
    response = request.getresponse()
    return response
    
    

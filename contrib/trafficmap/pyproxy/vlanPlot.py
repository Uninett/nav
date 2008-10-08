# -*- coding: ISO8859-1 -*-
#
# Copyright 2004 Norwegian University of Science and Technology
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
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

import sys
from mod_python import apache
from nav.web.templates.MainTemplate import MainTemplate

def handler(req):
    user = None
    if req.session.has_key('user') and req.session['user'].id > 0:
        user = req.session['user'].login

    protocolmap = {80:'http',
                   443:'https',
                   }
    protocol = protocolmap.get(req.connection.local_addr[1], 'http')
    applet = '<APPLET ARCHIVE="applet/vlanPlot.jar" CODE="vlanPlot.class" CODEBASE="." WIDTH=800 HEIGHT=600>\n'
       
    args = {}
    server = req.server.server_hostname
    if req.args:
        items = req.args.split("&")
        for item in items:
            try:
                key, val = item.split('=')
                args[key] = val
            except:
                pass

    params = ""
    params += '<PARAM NAME="vPServerURL" VALUE="%s://%s/vPServer/servlet/vPServer">\n' % (protocol, server)
    params += '<PARAM NAME="lastURL" VALUE="%s://%s/vlanPlot/last.pl">\n' % (protocol, server)
    params += '<PARAM NAME="cricketURL" VALUE="%s://%s/cricket/">\n' % (protocol, server)
    params += '<PARAM NAME="netflowURL" VALUE="%s://%s">\n' % (protocol, server)

    if args.has_key('boksid'):
        params += '<PARAM NAME="gotoBoksid" VALUE="%s"> \n' % args['boksid']
    if args.has_key('vlan'):
        params += '<PARAM NAME="gotoVlan" VALUE="%s"> \n' % args['vlan']

    params += '<PARAM NAME="nav_sessid" VALUE="%s"> \n' %req.session.id
    if user:
        params += '<PARAM NAME="user" VALUE="%s"> \n' % user
    applet += params
    applet +="</APPLET>"
    
    page = MainTemplate()
    page.content = lambda: applet
    page.path = [('Home', '/'), ('vlanPlot','')]
    req.content_type = "text/html; charset=utf-8"
    req.send_http_header()
    req.write(page.respond())
    return apache.OK

    

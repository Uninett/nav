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
# Author: Stian Soiland <stain@itea.ntnu.no>
#

"""Dispatcher - receives all requests below /browse and process them.
Parses the rest of the path to decide what to show.  This allows for
descriptive URLs like "/browse/machine.domain.com" and 
"/browse/machine.domain.com/module15/" etc.
"""

import os
import sys
import time
import profile
import warnings
import traceback
from mod_python import apache
from nav.errors import *

import forgetHTML as html

# Drrrty read av config
import nav.config

import nav.web

from nav.web.templates.DeviceBrowserTemplate import DeviceBrowserTemplate

try:
    script = __file__
except NameError:    
    script = sys.argv[0]

config = nav.config.readConfig('devbrowser.conf')

def handler(req):
    # catch warnings
    warns = []
    def showwarning(message, category, filename, lineno):
        warning = warnings.formatwarning(message, category, filename, lineno)
        warns.append(warning)
    warnings.showwarning = showwarning

    request = classifyUri(req.uri)
    if not request:
        if req.args:
            #  quick patch to except
            (a,b) = req.args.split("=")
            redirect(req, '/browse/%s' % b)
        redirect(req, '/report')    
        return apache.OK
    try:  
        import nav
        handler = __import__('nav.web.devBrowser.' + request['type'],
                             globals(), locals(), ('nav', 'web'))
        handler.process # make sure that there is a process functin
    except ImportError, e:
        req.write("%s\n" % e)
        req.write("%s \n" % sys.path)
        return apache.HTTP_NOT_FOUND
    except AttributeError, e:
        req.write("%s\n" % e)
        return apache.HTTP_NOT_FOUND
    
    req.session.setdefault('uris', [])
    request['query'] = req.args
    request['session'] = req.session
    request['req'] = req # in case som might need it. 
    templatePath = [] # add logical paths to thhis
    request['templatePath'] = templatePath
    templatePath.append(("Home", "/"))
    templatePath.append(("IP Device Center", "/report"))

    # result = handler.process(request)
    req.content_type = "text/html; charset=utf-8"
    try:
        result = handler.process(request)
        # Ensure our session gets saved =)
        req.session.save()
    except RedirectError, error:
        redirect(req, error.args[0])
    except apache.SERVER_RETURN, error:
        # don't catch-all these
        raise error
    except Exception, error:
        result = html.Paragraph("""We're terribly sorry, but something went wrong.. :(""")
        trace = traceback.format_exception(*sys.exc_info())
        message = "".join(trace)
        warns.append(message)
    
    # postpend the warnings
    if warns:    
        # Wrap it so we can add more
        result = html.Division(result)
        for warn in warns:
            warn = warn.replace("<", "&lt;")
            warn = warn.replace(">", "&gt;")
            message = html.Pre(warn, _class="warning")
            result.append(message)
    
    template = DeviceBrowserTemplate()
    template.path = []

    # Our template defines the variable myContent and treeselect.
    # Of course we can add more of them
    template.myContent = result
    template.treeselect = None
    template.path = templatePath
    template.title = templatePath[-1][0]

    response = template.respond()

    req.send_http_header()
    req.write(response)
    return apache.OK

def redirect(req, url):
    req.headers_out.add("Location", url)
    raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY

def classifyUri(uri):
    request = {}
    splitted = uri.split("/")
    # Note! Removes the first two elements! =) (perl style!)    
    if splitted.pop(0) != '' or \
       splitted.pop(0) <> config['basepath']:
        raise BasepathError, config['basepath']

    try:    
        name = splitted.pop(0)  
    except IndexError: 
        # We're requesting the index, return empty {}
        return request
    
    # handle empty string or 'topdir' (called 'index' by # DirectoryIndex)
    if not name or name == 'index':
        return request

    # Clean this up in some way
    if name in 'netbox cat vlan room module port service sla notfound alert org rrd'.split():
        request['type'] = name
    else:
        # Ok, it's a sysname.. split out to a seperate function that
        # checks out ip-addresses and so on
        request['type'] = 'netbox'
        if name.count(":"):
            (name, service) = name.split(":")[:2]
            request['service'] = service
        request['hostname'] = name
        if splitted:
            request['module'] = splitted.pop(0)
            if request['module']:
                request['type'] = 'module'
        if splitted:
            request['port'] = splitted.pop(0)
            if request['port']:
                request['type'] = 'port'
            
    
    request['args'] = splitted # the rest
    
    return request
    


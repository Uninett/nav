
import os
import sys
import time
import profile
import warnings 
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
        req.send_http_header()
        req.write(req.uri)
        req.write("\n")
        req.write("Dette er forsiden.. q-Pakh'")
        return apache.OK
    try:  
        import nav
        handler = __import__('nav.web.devBrowser.' + request['type'],
                             globals(), locals(), ('nav', 'web'))
        handler.process # make sure that there is a process functin

    except ImportError, e:
        req.write(str(e))
        return apache.HTTP_NOT_FOUND
    except AttributeError, e:
        raise repr(handler)
        return apache.HTTP_NOT_FOUND
    
    req.session.setdefault('uris', [])
    request['query'] = req.args
    request['session'] = req.session
        
    # result = handler.process(request)
    req.content_type = "text/html; charset=utf-8"
    try:
        result = handler.process(request)
    except RedirectError, error:
        redirect(req, error.args[0])
    
    # postpend the warnings
    if warns:    
        # Wrap it so we can add more
        result = html.Division(result)
        for warn in warns:
            message = html.Pre(warn, _class="warning")
            result.append(message)
    
    template = DeviceBrowserTemplate()
    # DRRRRRRTYUUUYY
    template.content = lambda: result
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
    
    # handle empty string or my own script (called by apaches 'index' feature)
    if not name or name == os.path.basename(script.replace(".pyc", ".py")):
        return request

    # Clean this up in some way
    if name in 'netbox cat vlan room service sla notfound alert org'.split():
        request['type'] = name
    else:
        # Ok, it's a sysname.. split out to a seperate function that
        # checks out ip-addresses and so on
        request['type'] = 'netbox'
        if name.count(":"):
            (name, service) = name.split(":")[:2]
            request['service'] = service
        request['hostname'] = name
    
    request['args'] = splitted # the rest
    
    return request
    



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

from nav.web.templates.MainTemplate import MainTemplate

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
        handler = __import__(request['type'])
        handler.process # make sure that there is a process functin

    except ImportError, e:
        req.write(str(e))
        return apache.HTTP_NOT_FOUND
    except AttributeError:
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
    
    # postpend the warningsw
    if warns:    
        # Wrap it so we can add more
        result = html.Division(result)
        for warn in warns:
            message = html.Pre(warn, _class="warning")
            result.append(message)
    
    template = MainTemplate()
    template.content = lambda: result
    # DRRRRRRTYUUUYY
    template.additionalCSS = lambda: """
      table.serviceNetboxes {
        border-collapse: collapse;
        padding: 0;
        margin: 0;
      }
      table.serviceNetboxes td {
        padding: 0.2em;
      }
      /* Services down have red light, in shadow yellow */
      table.serviceNetbox td { padding: 0.2em; }
      table.netboxinfo th { text-align: left; }
      /* Arrows for sorting!! 
      th.reverseSort#activeSort:after { content: url("/images/pilopp.png") }
      th.sort#activeSort:after { content: url("/images/pilned.png") }
      */
      th#activeSort { background-color: #ace; }
      table.serviceNetboxes th { text-align: left;  }
      pre.alert {
        position: absolute;
        border: 1px solid black;
        background-color: #ffa;
        visibility: hidden;
        z-index: 2;
        width: auto;
        padding: 0.1em;
      }
      div.alertBox {
        padding-right: 1em;
        float: left;
      }
      pre.warning {
        padding: 1em;
        border: 2px dotted black;
        background-color: #a88;
        color: black;
        margin-left: 10em;
        margin-right: 10em;
        margin-top: 2em;
      }
      
    """
    template.additionalJavaScript = lambda: """
    function show(id) {
        elem = document.getElementById(id);
        elem.style.visibility = 'visible';
    }
    function hide(id) {
        elem = document.getElementById(id);
        elem.style.visibility = 'hidden';
    }
    """
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
    if name in 'device cat vlan room service sla notfound alert org'.split():
        request['type'] = name
    else:
        # Ok, it's a sysname.. split out to a seperate function that
        # checks out ip-addresses and so on
        request['type'] = 'device'
        if name.count(":"):
            (name, service) = name.split(":")[:2]
            request['service'] = service
        request['hostname'] = name
    
    request['args'] = splitted # the rest
    
    return request
    


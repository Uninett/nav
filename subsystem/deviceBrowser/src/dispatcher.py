
import os
import sys
import time

from mod_python import apache

from errors import *

# Drrrty read av config
import nav.config

from nav.web.templates.MainTemplate import MainTemplate

try:
    script = __file__
except NameError:    
    script = sys.argv[0]

config = nav.config.readConfig('devbrowser.conf')

def handler(req):
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
        
    # result = handler.process(request)
    req.content_type = "text/html"
    result = handler.process(request)
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
      table.serviceNetboxes tr.n td.col0:before { content: url("/images/lys/red.png") }
      table.serviceNetboxes tr.s td.col0:before { content: url("/images/lys/yellow.png") }
      table.serviceNetboxes tr.y td.col0 { padding-left: 25px; }
      table.netboxinfo th { text-align: left; }
      /* Arrows for sorting!! */
      th.reverseSort#activeSort:after { content: url("/images/pilopp.png") }
      th.sort#activeSort:after { content: url("/images/pilned.png") }
      th#activeSort { background-color: #ace; }
      table.serviceNetboxes th { text-align: left;  }
    """
    try:
        response = template.respond()
    except RedirectError, error:
        redirect(req, error.args[0])

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
    if name in 'device cat vlan room service sla notfound org'.split():
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
    


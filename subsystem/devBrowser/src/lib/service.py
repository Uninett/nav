from mod_python import apache
import forgetHTML as html
from nav import db
from nav.db import manage 
from nav.web.devBrowser import servicetable
from nav.web import urlbuilder
from nav.web.tableview import TableView
from nav.errors import *
import random
import time

_serviceStates = {
    'y': 'Up',
    'n': 'Down',
    's': 'Shadow',
}

def getServiceState(service):
    return _serviceStates.get(service.up, "Unknown")

def process(request):
    args = request['args']
    query = request['query']
    sort = 2
    if query:
        query = query.split("=")
    if query and query[0]=='sort' and query[1:]:
        sort = query[1]
    try:
        sort = int(sort)
    except:
        sort = 2
    if not args:
        # We need a trailing /
        raise RedirectError, urlbuilder.createUrl(division="service")
    if args[0] == '':
        request['templatePath'].append(('Services', None))
        return showIndex()
    else:    
        request['templatePath'].append(('Services', 
               urlbuilder.createUrl(division="service")))

    if args[0] == 'all':
        request['templatePath'].append(('All', None))

        return showAll(request,sort)
        
    if args[0] == 'allMatrix':
        request['templatePath'].append(('All matrix', None)) 
        return showAllMatrix(request,sort)
    
    # else...
    handler = args[0]
    request['templatePath'].append((handler, None)) 
    return getNetboxes(handler, sort)

def getServices(netbox):
    services = netbox.getChildren(manage.Service)
    return services

def showIndex(showAll=0):
    result = html.Division()
    result.append(html.Header("All services", level=1))
    curs = db.cursor()
    # We'll do this manually to do it alot quicker (and smoother)
    curs.execute("""SELECT handler, count(serviceid) 
                    FROM service 
                    GROUP BY handler 
                    ORDER BY handler""")
    for (handler, count) in curs.fetchall():
            link = html.Anchor(handler, href=handler)         
            line = html.Division(link)
            line.append(' (%s)' % count)
            result.append(line)
    result.append(html.Paragraph(html.Anchor("Show all", href="all")))        
    result.append(html.Paragraph(html.Anchor("Show matrix", href="allMatrix")))        
    return result

def showAllMatrix(request, sort):
    curs = db.cursor()
    curs.execute("""SELECT DISTINCT handler
                    FROM service 
                    ORDER BY handler""")
    handlers = [handler for (handler,) in curs.fetchall()]                
    netboxes = {}
    for service in manage.Service.getAll():
        netbox = service.netbox
        if not netboxes.has_key(netbox.sysname):
            # First time, remember to make a list
            netboxes[netbox.sysname] = netbox
            netbox.services = {}
        netbox.services[service.handler] = service
    
    # Convert to a list, sorted by sysname
    netboxes = netboxes.items()
    netboxes.sort()
    
    # ok, generate HTML
    result = TableView('Netbox', sortBy=sort, *handlers)
    for (_, netbox) in netboxes:
        row = []
        # sysname with link
        row.append(urlbuilder.createLink(netbox))
        for handler in handlers:
            service = netbox.services.get(handler)
            state = html.TableCell()
            if not service:
                state.append('')
            else:    
                state.append(getServiceState(service))    
                state['class'] = service.up
            row.append(state)    
        result.add(*row)          
    result.sort()
    return result            

def showAll(request, sort):
    result = html.Division()
    start = time.time()
    try:
        if not request['session'].has_key("servicetable"):
            raise "NotFound"
        (table, stored) = request['session']['servicetable']
        if time.time() - stored > 60*5:
            # max 5 min to cache
            raise "NotFound"
        table.html.sortBy = sort
        table.html.sort()
        result.append(table.html)
        end = time.time() - start
        result.append("Sorted in %s seconds, " %  end)
        result.append("last updated %s" % time.strftime("%H:%M:%S"))
    except "NotFound":    
        table = servicetable.ServiceTable(sort=sort)
        result.append(table.html)
        end = time.time() - start
        result.append("Generated in %s seconds" %  end)
        request['session']['servicetable'] = (table, time.time())
    return result
    
def getNetboxes(servicename, sort):
    result = html.Division()
    result.append(html.Header("All servers running %s" % servicename, level=1))
    table = servicetable.ServiceTable(servicenames=(servicename,), sort=sort)
    result.append(table.html)
    return result

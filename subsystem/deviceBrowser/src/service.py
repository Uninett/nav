from mod_python import apache
import forgetHTML as html
from nav import tables
from nav import database
from nav import utils
from nav.web import tableview
from errors import *

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
    sort = 1
    if query:
        query = query.split("=")
    if query and query[0]=='sort' and query[1:]:
        sort = query[1]
    if not args:
        # We need a trailing /
        raise RedirectError, "http://isbre.itea.ntnu.no/stain/service/"    

    if args[0] == '':
        return showIndex()

    if args[0] == 'all':
        return showAll(sort)

    return getNetboxes(args[0], sort)

def getServices(netbox):
    services = netbox.getChildren(tables.Service)
    return services

def downSince(service):
    where = ["eventtypeid='serviceState'"]
    where.append("end_time='infinity'")
    alerts = service.getChildren(tables.Alerthist, 'subid', where)
    if not alerts:
        return None
    # Eh.. there should be only one with end_time==infinity
    lastAlert = alerts[-1]
    return lastAlert.start_time

def showIndex(showAll=0):
    result = html.Division()
    result.append(html.Header("All services", level=1))
    curs = database.cursor()
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
    return result

def showAll(sort):
    services = tables.Service.getAll()
    result = html.Division()
    result.append(html.Header("All services", level=2))
    table = tableview.TableView("Service", "Server", "Status", "Version", 
                                baseurl="all", sortBy=sort)
    table['class'] = "serviceNetboxes"
    result.append(table)
                              
    for service in services:
        version = service.version or "Unknown"
        sysname = service.netbox.sysname
        # Prepare for some css-stylish
        # row['class'] = service.up
        
        linkNetbox = html.Anchor(sysname, href='../%s' % sysname)
        linkService = html.Anchor(service.handler, href=service.handler)
        status = getServiceState(service)
        if service.up == 'n':
            since = downSince(service)
            status += " since %s" % since
        table.add(linkService, linkNetbox, status, version, _class=service.up)
    table.sort()    
    return result      
    
def getNetboxes(servicename, sort):
    service = database.escape(servicename)
    services = tables.Service.getAll("handler=%s" % service)
    result = html.Division()
    result.append(html.Header("All servers running %s" % servicename, level=2))
    table = tableview.TableView("Server", "Version", "Status", 
                                baseurl=servicename, sortBy=sort)
    table['class'] = "serviceNetboxes"
    result.append(table)
                              
    for service in services:
        version = service.version or "Unknown"
        sysname = service.netbox.sysname
        # Prepare for some css-stylish
        # row['class'] = service.up
        
        link = html.Anchor(sysname, href='../%s' % sysname)
        status = getServiceState(service)
        if service.up == 'n':
            since = downSince(service)
            status += " since %s" % since
        table.add(link, version, status, _class=service.up)
    table.sort()    
    return result      


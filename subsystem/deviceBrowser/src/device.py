from mod_python import apache
from nav.db import manage
from nav.web.tableview import TableView
from nav.web.servicetable import ServiceTable
from nav.web import urlbuilder
from nav.errors import *

import service
import forgetHTML as html
import rrdpresenter
import random

def process(request):
    args = request['args']
    query = request['query']
    sortBy = 1
    if query:
        query = query.split("=")
    if query and query[0]=='sort' and query[1:]:
        sortBy = query[1]
    try:
        sortBy = int(sortBy)
    except:
        sortBy = 1

    hostname = request.get("hostname","")
    if not hostname:
        # How did we get here?
        return showIndex()
    netbox = manage.getNetbox(hostname)
    result = html.Division()
    if not netbox:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
    #for i in netbox._sqlFields.keys():
    #    line = "%s: %s\n" % (i, getattr(netbox, i))
    #    result.append(html.Division(line))
    
    result.append(showInfo(netbox))
    services = showServices(netbox, sortBy)
    if services:
        result.append(services)
    return result
    
def showInfo(netbox):
    result = html.Division()
    title = html.Header("%s - General information" % netbox.sysname, level=2)
    result.append(title)
    info = html.SimpleTable()
    info['class'] = "netboxinfo"
    #info['Sysname'] = netbox.sysname
    info.add('Status', netbox.up)
    info.add('Category', urlbuilder.createLink(netbox.cat))
    if netbox.type:
        info.add('Type', urlbuilder.createLink(netbox.type))
    info.add('Organisation', urlbuilder.createLink(netbox.org))
    info.add('Room', urlbuilder.createLink(netbox.room))
    # info.add('Snmp version', netbox.snmp_version or "Unknown")
    # info.add('Snmp agent', netbox.snmp_agent or "Unknown")
    result.append(info)
    return result
    

def showServices(netbox, sort):
    try:
        table = ServiceTable(netboxes=(netbox,), sort=sort)
    except NoServicesFound:
        return None
    div = html.Division()
    div.append(html.Header("Services", level=2))
    div.append(table.html)
    return div
    


from mod_python import apache
from nav import tables
import service
import forgetHTML as html
from nav import rrdpresenter

def process(request):
    hostname = request.get("hostname","")
    if not hostname:
        # How did we get here?
        return showIndex()
    netbox = tables.getNetbox(hostname)
    result = html.Division()
    if not netbox:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
    #for i in netbox._sqlFields.keys():
    #    line = "%s: %s\n" % (i, getattr(netbox, i))
    #    result.append(html.Division(line))
    
    result.append(showInfo(netbox))
    services = showServices(netbox)
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
    room = "%s %s" % (netbox.room.roomid, netbox.room.descr)
    info.add('Room', html.Anchor(room, href="room/%s" %netbox.room.roomid))
    organisation = "%s (%s)" % (netbox.org.descr, netbox.org.orgid)
    info.add('Organisation', organisation)
    category = "%s (%s)" % (netbox.cat.descr, netbox.cat.catid)
    info.add('Category', category)
    info.add('Snmp version', netbox.snmp_version or "Unknown")
    info.add('Snmp agent', netbox.snmp_agent or "Unknown")
    result.append(info)
    return result
    

def showServices(netbox):
    services = service.getServices(netbox)
    if not services:
        return 
    result = html.Division()
    result['class'] = 'services'
    title = html.Header("Monitored services", level=2)
    result.append(title)
    table = html.Table()
    tableHeader = html.TableRow()
    tableHeader.append(html.TableHeader("Handler", align='left'))
    tableHeader.append(html.TableHeader("Status", align='left'))
    tableHeader.append(html.TableHeader("rrdtull", align='lef'))
    table.append(tableHeader)
    result.append(table)
    for i in services:
        row = html.TableRow()
        handler = html.Anchor(i.handler, href="service/%s" % i.handler)
        row.append(handler)
        if i.version:
            handler['title'] = i.version
        status = service.getServiceState(i)
        if i.up == 'n':
            since = service.downSince(i)
            status += ' since %s' % since
        row.append(status)
        row['class'] = i.up # ie. 
        row.append(getServiceRrds(i))
        table.append(row)
    return result
def showIndex():
    return "<html><body>hei</body></html>"
def getServiceRrds(service):
    rrdFiles = tables.Rrd_file.getAll("key='serviceid' and value=%i" % service.serviceid)
    rrd = rrdpresenter.presentation()
    for rrdFile in rrdFiles:
        datasources = rrdFile.getChildren(tables.Rrd_datasource)
        for datasource in datasources:
            id = datasource.rrd_datasourceid
            rrd.addDs(id)
            
    return str(rrd.average())
        

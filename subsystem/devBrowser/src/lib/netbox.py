
from mod_python import apache
import forgetHTML as html
import random
import re
from mx import DateTime

from nav.db import manage
from nav.web import urlbuilder
from nav.errors import *
from nav.rrd import presenter
from nav.web import tableview
import module
from nav.web.devBrowser.servicetable import ServiceTable

_statusTranslator = {'y':'Up',
                     'n':'Down',
                     's':'Shadow'
                     }

def distance(a,b):
    """
    Calculates the Levenshtein distance between a and b.
    """
    n, m = len(a), len(b)
    if n > m:
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*m
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]

def findNetboxes(hostname):
    """
    Finds a netbox from sysname or partial sysname. Returns
    a list of netboxes in which hostname is a substring of
    their sysname. huh
    """
    netbox = manage.getNetbox(hostname)
    if netbox:
        return [netbox]
    # Now we can try to see if hostname is a substing of
    # a real sysname
    netboxes = manage.Netbox.getAll()
    sysnames = [nb.sysname for nb in netboxes]
    matches = []
    for sysname in sysnames:
        if sysname.find(hostname) >= 0:
            matches.append(manage.getNetbox(sysname))

    if len(matches) == 1:
        raise RedirectError, urlbuilder.createUrl(matches[0])
    elif matches:
        return matches
    # try mr. levenshtein...
    a=hostname.count('.')
    for sysname in sysnames:
        # should be fixed in a better way...
        if not sysname.find('129.241') >= 0:
            shortname = '.'.join(sysname.split('.')[:a+1])
            matches.append((distance(hostname, shortname), sysname))
    matches.sort()
    return [manage.getNetbox(x[1]) for x in matches[:20]]
    
    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
    
def showMatches(netboxes):
    result = html.Division()
    heading = html.Header("Found %s netboxes matching your query" % len(netboxes),
                          level=2)
    result.append(heading)
    for netbox in netboxes:
        line = html.Division()
        line.append(urlbuilder.createLink(netbox))
        result.append(line)
    return result    

def process(request):
    args = request['args']
    query = request['query']
    sortBy = 2
    if query:
        query = query.split("=")
    if query and query[0]=='sort' and query[1:]:
        sortBy = query[1]
    try:
        sortBy = int(sortBy)
    except:
        sortBy = 2

    hostname = request.get("hostname","")
    if not hostname:
        # How did we get here?
        return showIndex()
    netboxes = findNetboxes(hostname)
    if len(netboxes) > 1:
        return showMatches(netboxes)
    else:
        netbox = netboxes[0]
    request['templatePath'].append((str(netbox), None))

    #for i in netbox._sqlFields.keys():
    #    line = "%s: %s\n" % (i, getattr(netbox, i))
    #    result.append(html.Division(line))
    
    # Ok, instanciate our NetboxInfo using netbox
    info = NetboxInfo(netbox)
    result = html.Division()
    result.append(info.showInfo())
    result.append(urlbuilder.createLink(netbox, 
                            subsystem='editdb', content="[Edit]"))
    services = info.showServices(sortBy)
    if services:
        result.append(services)
    rrds = info.showRrds()
    if rrds:
        result.append(rrds)
##    links = info.showLinks()    
##    if links:
##        result.append(links)
    ports = info.showPorts()
    if ports:
        result.append(ports)
    return result

class NetboxInfo(manage.Netbox):
    def __init__(self, netbox):
        manage.Netbox.__init__(self,netbox)
        self.setPrefix()
    
    def showInfo(self):
        result = html.Division()
        title = html.Header("%s - General information" % self.sysname, level=2)
        result.append(title)
        alerts = self.showAlerts()    
        if alerts:
            result.append(alerts)    
        info = html.SimpleTable()
        info['class'] = "netboxinfo"
        info.add('Status', _statusTranslator.get(self.up, self.up))
        info.add('Availability', self.availability())
        info.add('Ip address', self.showIp())
        info.add('Vlan', self.showVlan())
        info.add('Gateway', self.showGw())
        info.add('Switch', self.showSw())
        info.add('Category', urlbuilder.createLink(self.cat,
            subsystem="report"))
        if self.type:
            info.add('Type', urlbuilder.createLink(self.type))
        info.add('Organisation', urlbuilder.createLink(self.org))
        info.add('Room', urlbuilder.createLink(self.room))
        result.append(info)
        return result
    def setPrefix(self):
        prefixes = manage.Prefix.getAll(where="'%s' << netaddr" % self.ip,
                                        orderBy='netaddr')
        if not prefixes:
            self.prefix = 0
        else:
            # the last one is the one with most spesific network address
            self.prefix = prefixes[-1]
        
    def showGw(self):
        if not self.prefix:
            return 'Unknown'
        # Find the gw
        gws = self.prefix.getChildren(manage.Gwportprefix,
                                 orderBy='hsrp')
        if not gws:
            return 'Unknown'
        # If we have hsrp, the active gw is listed last
        gw = gws[-1]
        gwNetbox = gw.gwport.module.netbox
        gwLink = urlbuilder.createLink(gwNetbox, content=gw.gwip)
        return gwLink

    def showVlan(self):
        if self.prefix:
            vlan = self.prefix.vlan
            vlan = urlbuilder.createLink(vlan, 
                                         content="Vlan %s" % vlan.vlan)
        else:
            vlan = 'Unknown'
        return vlan

    def showSw(self):
        sw = self.getChildren(manage.Swport, 'to_netbox')
        if not sw:
            return 'Unknown'
        vlans = []
        for i in sw:
            vlan = i.vlan
            if vlan not in vlans:
                vlans.append(vlan)
        if len(vlans) > 1:
            return 'More then one vlan' 
        sw = sw[0]
        swNetbox = sw.module.netbox
        swPort = sw.port
        swModule = sw.module.module
        swLink = urlbuilder.createLink(swNetbox)
        swLink.append('(Module %s, Port %s)' % (swModule, swPort))
        return swLink
        
        
    def showIp(self):
        return self.ip

    def availability(self):
        TIMERANGES = ('day', 'week', 'month')
        rrdfiles = self.getChildren(manage.Rrd_file,
                                      where="subsystem='pping'")
        if not rrdfiles:
            return "Unknown"
        rrdfile = rrdfiles[0]
        datasources = rrdfile.getChildren(manage.Rrd_datasource)
        if not datasources:
            return "Unknown"
        statusDS = None
        for ds in datasources:
            if ds.name == 'STATUS':
                statusDS = ds
        if not statusDS:
            return 'Unknown'
        result=html.Division()
        for timerange in TIMERANGES:
            value = self.rrdAverage(statusDS, timerange)
            if value is None:
                value = 0 # unknown -> not availabe..?
            else:
                value = (1-value)*100    
            value = tableview.Value(value, "%")
            dsids = [ds.rrd_datasourceid for ds in datasources]
            link = urlbuilder.createLink(subsystem='rrd',
                                         division='datasources',
                                         id=dsids,
                                         tf=timerange,
                                         content=value)
            result.append(link)
        result.append(html.Small('(%s)' % ' / '.join(TIMERANGES)))
        return result

    def rrdAverage(self, ds, timeframe):
        rrd = presenter.presentation()
        rrd.timeLast(timeframe)
        rrd.addDs(ds)
        value = rrd.average()
        if not value:
            return None
        else:
            value = value[0]
        return value

    def showAlerts(self):
        alerts = self.getChildren(manage.Alerthist, orderBy='start_time',
                                    where= """end_time = 'infinity' OR
                                    (now() - end_time) < '1 week' """)
        alerts.reverse()
        # dirty dirty, we just requested ALL alerts from the database..
        if len(alerts) > 15:
            moreAlerts = True
        else:
            moreAlerts = False
        alerts = alerts[:15] # only the 15 last events
        if not alerts:
            return None
        table = html.SimpleTable("row")
        table.add("Event", "Start", "Downtime")
        for alert in alerts:
            row = []
            if alert.source == 'serviceping':
                service = manage.Service(alert.subid)
                try:
                    type = service.handler
                except:
                    type = "%s (%s)" % (alert.eventtype, alert.subid)
            else:
                type = str(alert.eventtype)

            msg = alert.getChildren(manage.Alerthistmsg,
                                    where="""msgtype='sms' """)

            if msg:
                type = html.TableCell(type)
                type['title'] = msg[0].msg
                        
            row.append(type)
            start_time = alert.start_time.strftime("%Y-%m-%d %H:%M")
            row.append(start_time)
            oneYear = DateTime.oneDay * 365
            if not alert.end_time:
                # should NOT be NULL, but sometimes it is ... brrr
                age = "Unknown"
            else:
                age = alert.end_time - alert.start_time
                end_time = alert.end_time.strftime("%Y-%m-%d %H:%M")
                if age > oneYear:
                    age = DateTime.now() - alert.start_time
                    end_time = 'Still down'
                if age > DateTime.oneDay:    
                    age = "%dd %s" % (age.days, age.strftime("%kh %Mm"))    
                else:
                    age = age.strftime("%kh %Mm")
                # note - %k is %H but without leading 0    
            age = html.TableCell(age)
            age['title'] = end_time
            age['align'] = 'right'
            row.append(age)       
            if end_time == 'Still down':
                table.add(_class="stillDown", *row)
            else:    
                table.add(*row)
        div = html.Division()
        div['class'] = "alerts"
        div.append(html.Header("Recent alerts (last week)", level=3))
        div.append(table)
        if moreAlerts:
            div.append(html.Emphasis(html.Small("More alerts exists for this time frame.")))
        return div 

    def showServices(self, sort):
        try:
            table = ServiceTable(netboxes=(self,), sort=sort)
        except NoServicesFound:
            return None
        div = html.Division()
        div.append(html.Header("Service availability", level=2))
        div.append(table.html)
        return div

    def showLinks(self):
        # Vi må hente ifra swport-tabellen istedet!
        up = self.getChildren(manage.Swport, 'to_netbox')
        down = []
        for module in self.getChildren(manage.Module):
            modLinks = module.getChildren(manage.Swport, 'module')
            down.extend(modLinks)
        if not (up or down):
            return None
        info = html.Division()
        info.append(html.Header("Links with this box", level=2))
        def swporturl(netbox, module, port):
            """Generates a link to a given port"""
            url = urlbuilder.createUrl(netbox)
            url += 'module%s/port%s/' % (module, port)
            return html.Anchor(str(port), href=url)
        if up:
            for link in up:
                line = html.Division()
                info.append(line)
                line.append(urlbuilder.createLink(link.to_netbox))
                # His port
                line.append("(")
                if link.module and link.port:
                    line.append("%s %s" % 
                            (link.module, 
                             swporturl(link.netbox, link.module,link.port)))
                line.append("&nbsp;--&gt;&nbsp;")
                # our 
                if link.to_module and link.to_port:
                    line.append("%s %s" % 
                        (link.to_module, 
                         swporturl(link.to_netbox, link.to_module,link.to_port)))
                line.append(")")
        if down:
            for link in down:
                line = html.Division()
                info.append(line)
                line.append(urlbuilder.createLink(link.to_netbox))
                # His port
                line.append("(")             
                if link.to_module and link.to_port:
                    line.append("(%s %s" % 
                        (link.to_module, 
                         swporturl(link.to_netbox, link.to_module,link.to_port)))
                line.append("&nbsp;&lt;--&nbsp;")
                # our port
                if link.module and link.port:
                    line.append("%s %s" % 
                            ( link.module, 
                             swporturl(link.netbox, link.module,link.port)))
                line.append(")")             
        return info                    

    def showRrds(self):
        rrdfiles = self.getChildren(manage.Rrd_file,
                   where="not subsystem in ('pping', 'serviceping')")
        if not rrdfiles:
            return None
        result = html.Division()
        result.append(html.Header("Statistics", level=3))
        for rrd in rrdfiles:
            info = "%s: %s" % (rrd.key, rrd.value)
            if rrd.key == 'swport' or rrd.key == 'gwport':
                continue # skip swports for now
                port = manage.Swport(rrd.value)
                try:
                    port.load()
                except:
                    port = None
                if port:
                    info = "%s %s %s" % (
                        port.module.netbox.sysname,
                        port.module.module,
                        port.port)
                       
            all = []
            for ds in rrd.getChildren(manage.Rrd_datasource):
                link = urlbuilder.createLink(subsystem='rrd',
                                             id=ds.rrd_datasourceid,
                                             division="datasources",
                                             content=(ds.descr or "(unknown)"))
                all.append(ds.rrd_datasourceid)
                result.append(html.Division(link))

        link = urlbuilder.createLink(subsystem='rrd',
                    id=all, division="datasources", content="[All]")
        result.append(html.Division(link))
        return result                

    def showPorts(self):
        div = html.Division(_class="ports")
        div.append(html.Header("Switchports", level=2))
        div.append(module.showModuleLegend())        
        modules = self.getChildren(module.ModuleInfo)
        if not modules:
            return None
        isNum = lambda x: x and re.match("^[0-9]+$",str(x))
        # høhø
        modules.sort(lambda a,b:
            # sort by number - if possible
            (isNum(a.module) and isNum(b.module) 
             and cmp(int(a.module), int(b.module))) 
            or cmp(a.module,b.module)) 
        for mod in modules:
            moduleView = mod.showModule()
            if moduleView:
                div.append(moduleView)
        return div


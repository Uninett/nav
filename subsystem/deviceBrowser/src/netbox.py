from mod_python import apache
from nav.db import manage
from nav.web.servicetable import ServiceTable
from nav.web import urlbuilder
from nav.errors import *
from nav.rrd import presenter

from  nav.web import tableview
import service
import forgetHTML as html
import random
from mx import DateTime

_statusTranslator = {'y':'Up',
                     'n':'Down',
                     's':'Shadow'
                     }
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
    netbox = manage.getNetbox(hostname)
    if not netbox:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
    #for i in netbox._sqlFields.keys():
    #    line = "%s: %s\n" % (i, getattr(netbox, i))
    #    result.append(html.Division(line))
    
    # Ok, instanciate our NetboxInfo using netbox
    info = NetboxInfo(netbox)
    result = html.Division()
    result.append(info.showInfo())
    services = info.showServices(sortBy)
    if services:
        result.append(services)
    rrds = info.showRrds()
    if rrds:
        result.append(rrds)
    ports = info.showPorts()
    if ports:
        result.append(ports)
    return result

class NetboxInfo(manage.Netbox):
    
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
        info.add('Category', urlbuilder.createLink(self.cat))
        if self.type:
            info.add('Type', urlbuilder.createLink(self.type))
        info.add('Organisation', urlbuilder.createLink(self.org))
        info.add('Room', urlbuilder.createLink(self.room))
        result.append(info)
        return result
    def showIp(self):
        prefixes = manage.Prefix.getAll(where="'%s' << netaddr" % self.ip,
                                    orderBy='netaddr')
        return self.ip
        if not prefixes:
            vlan = "(Unknown network)"
        else:
            # the last one is the one with most spesific network address
            vlan = prefixes[-1].vlan
            if vlan:
                vlan = urlbuilder.createLink(vlan, 
                                content="Vlan %s" % vlan.vlan)
            else:
                vlan = "(Unknown vlan)"
        return "%s %s" % (self.ip, vlan)


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
            return ""
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

    def showRrds(self):
        rrdfiles = self.getChildren(manage.Rrd_file,
                   where="not subsystem in ('pping', 'serviceping')")
        if not rrdfiles:
            return None
        table = html.SimpleTable()
        for rrd in rrdfiles:
            info = "%s: %s" % (rrd.key, rrd.value)
            if rrd.key == 'swport':
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
                       
            for ds in rrd.getChildren(manage.Rrd_datasource):
                table.add(str(rrd.value), info, str(ds.descr))
                
    #            ds.load()
     #           ds.rrd_file.load()
      #          table.add(str(ds.rrd_file._values), str(ds._values))
        return table

    def showPorts(self):
        div = html.Division(_class="ports")
        div.append(html.Header("Switchports", level=2))
        # div.append(modules)
        modules = self.getChildren(manage.Module)
        modules.sort()
        if not modules:
            return None
        for module in modules:
            moduleView = self.showModule(module)
            if moduleView:
                div.append(moduleView)
        div.append(self.showModuleLegend())        
        return div

    def showModule(self,module):
        def findDisplayWidth(ports):
            # Normally we'll show 12 ports in a row, but
            # sometimes (?) 16 could be the one.
            length = len(ports)
            for x in 12,16,8,14:
                if not length % x:
                    return x
            return 12        
        
        ports = module.getChildren(manage.Swport)
        if not ports:
            type = "gw"
        else:
            type = "sw"
        ports += module.getChildren(manage.Gwport)

        if not ports:
            return None
        
        moduleView = html.Division(_class="module")
        if type == "gw":
            moduleView['class'] += ' gw'
        # a <h3><span>-trick to get nice header
        moduleView.append(html.Header(
            html.Span("Module %s" % module.module), level=3))
        # calc width
        width = findDisplayWidth(ports)
        count = 0
        for port in ports:
            if count and not count % width:
                moduleView.append(html.Break())
            count += 1
            if type=="gw":
                if port.masterindex:
                    portNr = "%s-%s" % (port.masterindex, port.ifindex)
                else:    
                    portNr = port.ifindex
            else:
                portNr = port.port
            portView = html.Span("%s"% portNr,  _class="port")
            titles = []
            portView['title'] = ""
            if type == 'sw' and port.link <> 'y':
                portView['class'] += ' passive'
                titles.append('not active')
            if port.speed:    
                portView['class'] += ' Mb%d' % port.speed
                titles.append( '%d Mbit' % port.speed)
            if type == 'sw':
                if port.trunk:
                    portView['class'] += ' trunk'
                    titles.append("trunk")
                portView['class'] += ' %sduplex' % port.duplex
                if port.media:
                    titles.append(port.media)
            if type == 'gw':
                for item in port._values.items():
                    titles.append("%s %s" % item)
            if titles:
                # beautiful! but .capitalize() lowercases everything first
                titles[0] = titles[0][0].upper() + titles[0][1:]
                title = ', '.join(titles)
                portView['title'] = title
            moduleView.append(portView)
        return moduleView

    def showModuleLegend(self):
        legend = html.Division(_class="legend")
        legend.append(html.Header("Legend", level=3))
        def mkLegend(name, descr):
            port = html.Span("1")
            port['class'] = "port %s" % name
            legend.append(port)
            legend.append(descr)
            legend.append(" ")
        mkLegend("passive", "Not active")
        mkLegend("hduplex", "Half duplex")
        mkLegend("trunk", "Trunk")
        legend.append(html.Break())
        mkLegend("Mb10", "10 Mbit")
        mkLegend("Mb100", "100 Mbit")
        mkLegend("Mb1000", "1 Gbit")
        return legend    

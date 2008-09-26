# -*- coding: UTF-8 -*-
#
# Copyright 2002-2005 Norwegian University of Science and Technology
# Copyright 2006-2007 UNINETT AS
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
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Stian Soiland <stain@itea.ntnu.no>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

"""Top level view of a netbox.
Includes generic information (hostname, ip), ping statistics, switch
modules, statistics (RRD), services monitored, network connectivity,
vlans, etc."""

import sys
import time
import IPy
try:
    from mod_python import apache
except:
    pass
import forgetHTML as html
import re
from mx import DateTime


import nav.db
from nav.db import manage
from nav.web.devBrowser import urlbuilder
from nav.errors import *
from nav.rrd import presenter
from nav.web import tableview
import module
from nav.web.devBrowser.servicetable import ServiceTable
from nav.event import EventQ, Event
import logging

logger = logging.getLogger("nav.web.devBrowser.netbox")

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

import types
def getChildrenIterator(self, forgetter, field=None, where=None, orderBy=None,
                        useObject=None):
  """Mimics forgetSQL forgetters' getChildren, except that it returns an
  iterator, like getAllIterator.
  """
  if type(where) in (types.StringType, types.UnicodeType):
    where = (where,)

  if not field:
    for (i_field, i_class) in forgetter._userClasses.items():
      if isinstance(self, i_class):
        field = i_field
        break # first one found is ok :=)
  if not field:
    raise "No field found, check forgetter's _userClasses"
  sqlname = forgetter._sqlFields[field]
  myID = self._getID()[0] # assuming single-primary !

  whereList = ["%s='%s'" % (sqlname, myID)]
  if where:
    whereList.extend(where)

  return forgetter.getAllIterator(whereList, useObject=useObject,
                                  orderBy=orderBy)
# Dirrty hack to extend forgetSQL for perfomance reasons
import forgetSQL
if not hasattr(forgetSQL.Forgetter, 'getChildrenIterator'):
    forgetSQL.Forgetter.getChildrenIterator = getChildrenIterator

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
    matches = [nb for nb in manage.Netbox.getAllIterator(
        where="sysname like %s" % nav.db.escape('%'+hostname+'%')) ]

    if len(matches) == 1:
        raise RedirectError, urlbuilder.createUrl(matches[0])
    elif matches:
        return [(match, None) for match in matches]
    # try mr. levenshtein...
    a=hostname.count('.')
    for nb in manage.Netbox.getAllIterator():
        try:
            IPy.IP(nb.sysname)
        except ValueError:
            # Only accept non-IP sysnames
            shortname = '.'.join(nb.sysname.split('.')[:a+1])
            matches.append((distance(hostname, shortname), nb))
    matches.sort()
    result = []
    for match in matches:
        dist, nb = match
        # 5 seems to be a reasonable distance...
        if dist < 5:
            result.append((nb, dist))
        else:
            break

    # If no matches have low enough Levenstein, just show the five closest
    # matches
    if len(result) == 0:
        for i, match in enumerate(matches):
            if i < 5:
                dist, nb = match
                result.append((nb, dist))
                i += 1
            else:
                break

    if len(result) == 1:
        raise RedirectError, urlbuilder.createUrl(result[0][0])
    return result
    #return [(manage.getNetbox(x[1]),x[0]) for x in matches[:20]]

    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

def showMatches(netboxes):
    result = html.Division()
    heading = html.Header("Listing %s closest matches" % len(netboxes),
                          level=2)
    result.append(heading)
    for match in netboxes:
        netbox, distance = match
        line = html.Division()
        line.append("%s (%s)" % (urlbuilder.createLink(netbox), distance))
        result.append(line)
    return result

def process(request):
    args = request['args']
    fields = request['fields']
    if 'sort' in fields:
        sortBy = fields.getfirst('sort')
    try:
        sortBy = int(sortBy)
    except:
        sortBy = 2

    hostname = request.get("hostname","")
    if not hostname:
        # How did we get here?
        return showIndex()
    netboxes = findNetboxes(hostname)
    # returns a list of tuples; [(netbox, distance),]
    if len(netboxes) > 1:
        return showMatches(netboxes)
    elif len(netboxes) == 1:
        netbox = netboxes[0]
    else:
        raise "This should not happen."
    request['templatePath'].append((str(netbox), None))

    #for i in netbox._sqlFields.keys():
    #    line = "%s: %s\n" % (i, getattr(netbox, i))
    #    result.append(html.Division(line))

    if 'refresh' in request['fields']:
        refresh = RefreshHandler(request, netbox)
        if not refresh.isDone():
            return refresh.process()

    # Ok, instanciate our NetboxInfo using netbox
    result = html.Division()

    info = NetboxInfo(netbox)
    result.append(info.showInfo())

    interval = fields.getfirst('interval', '30')
    interval = interval.isdigit() and int(interval) or 30
    ports = info.showPorts(activePerspective=
                           fields.getfirst('perspective', 'standard'),
                           interval=interval)
    if ports:
        result.append(ports)

    services = info.showServices(sortBy)
    if services:
        result.append(services)

    rrds = info.showRrds()
    if rrds:
        result.append(rrds)

    return result

class RefreshHandler:
    refreshVar = 'devBrowseRefresh'

    def __init__(self, request, netbox):
        self.request = request
        self.netbox = netbox
        self.session = self.request['session']
        self.postRefresh()

    def postRefresh(self):
        if self.refreshVar not in self.session:
            # Post the event here
            refreshTime = time.time()
            refreshId = '%d%d' % (self.netbox.netboxid,refreshTime)
            refreshId = long(refreshId) % sys.maxint

            event = Event(source='devBrowse', target='getDeviceData',
                          netboxid=self.netbox.netboxid, subid=refreshId,
                          eventtypeid='notification')
            event['command'] = 'runNetbox'
            req = self.request['request']
            logger.debug("Posting refresh event for IP Device %s, "
                         "refreshID=%s", self.netbox.sysname, refreshId)
            event.post()

            self.session[self.refreshVar] = (refreshId, refreshTime)
            self.session.save()

    def cancelRefresh(self):
        if self.refreshVar in self.session:
            del self.session[self.refreshVar]

        result = html.Division()
        result.append(html.Paragraph('Refresh cancelled...'))
        backUrl = urlbuilder.createUrl(division='netbox',
                                       id=self.netbox.netboxid)
        refreshMeta = '<meta http-equiv="refresh" content="0;url=%s" />\n'
        self.request['template'].additionalMeta = lambda: refreshMeta % backUrl
        return result

    def isDone(self):
        "If received, consume reply event and return true"
        req = self.request['request']
        def deleteStale(events):
            staleMinutes = 5
            staleTime = DateTime.now() - DateTime.oneMinute * staleMinutes
            stale = [event for event in events
                     if event.time < staleTime \
                     and event['command'] == 'runNetboxDone']
            for event in stale:
                age = (DateTime.now() - event.time).minutes
                logger.debug("Deleting stale refresh reply event "
                             "%s (%.01f minutes old)", event.eventqid, age)
                event.dispose()

        # Only check for replies if we actually know that we've posted an event
        if self.refreshVar in self.session:
            (refreshId, refreshTime) = self.session[self.refreshVar]
            events = EventQ.consumeEvents(target='devBrowse')
            logger.debug("Checking for refresh replies, found %d events "
                         "directed at me", len(events))
            deleteStale(events)
            # Get the event(s) directed at this refresh instance
            forMe = [event for event in events
                     if int(event.subid) == int(refreshId)]
            if len(forMe) > 0:
                logger.debug("Got reply event for refreshId=%s", refreshId)
                event = forMe[0]
                event.dispose()
                del self.session[self.refreshVar]
                self.session.save()
                return True
        return False

    def process(self):
        fields = self.request['fields']
        if 'refresh' in fields \
               and fields.getfirst('refresh').lower() == 'cancel':
            return self.cancelRefresh()
        return self._waitPage()

    def _waitPage(self):
        "Wait for gDD to reply to our refresh request"
        result = html.Division()
        timeElapsed = time.time() - self.session[self.refreshVar][1]
        waitString = '(%d seconds elapsed)' % timeElapsed
        result.append(html.Paragraph('Please wait for collector to ' + \
                                     'refresh data from %s %s...' %
                                     (self.netbox.sysname, waitString)))
        cancelForm = html.Form(method="GET", action="")
        cancelForm.append(html.Submit(name="refresh", value="Cancel"))
        result.append(cancelForm)
        self.request['templatePath'][-1] = \
                                         ('Refreshing ' + \
                                          self.request['templatePath'][-1][0],
                                          None)
        refreshMeta = '<meta http-equiv="refresh" content="5" />\n'
        self.request['template'].additionalMeta = lambda: refreshMeta
        return result


class NetboxInfo(manage.Netbox):
    def __init__(self, netbox):
        manage.Netbox.__init__(self, netbox)
        self.setPrefix()

    def showInfo(self):
        result = html.Division()
        title = html.Header(self.sysname, level=2)
        result.append(title)
        result.append(self.showActions())
        alerts = self.showAlerts()
        if alerts:
            result.append(alerts)
        info = html.SimpleTable()
        info['class'] = 'vertitable'
        info.add('Status', _statusTranslator.get(self.up, self.up))
        info.add('Availability', self.availability())
        info.add('Uptime', self.showUptime())
        info.add('IP address', self.showIp())
        info.add('Vlan', self.showVlan())
        info.add('Gateway', self.showGw())
        info.add('Uplink', self.showSw())
        info.add('Category', urlbuilder.createLink(self.cat,
            subsystem="report"))
        if self.type:
            info.add('Type', urlbuilder.createLink(self.type))
        info.add('Organisation', urlbuilder.createLink(self.org))
        info.add('Room', urlbuilder.createLink(self.room))
        info.add('Software', self.showSoftware())
        info.add('Serial number', self.showSerialNumber())
        info.add('# of modules', self.showModuleCount())
        info.add('# of switch ports', self.showSwportCount())
        info.add('# of router ports', self.showGwportCount())
        info.add('Last updated', self.showLastUpdate())
        info.add('First discovered', self.showFirstDiscovered())
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
        netmasklen = self.prefix.netaddr.split('/')[1]
        netmask = IPy.intToIp(IPy._prefixlenToNetmask(int(netmasklen), 4), 4)
        # Find the gw
        gws = self.prefix.getChildren(manage.Gwportprefix,
                                 orderBy=['hsrp','gwip'])
        if not gws:
            return 'Unknown'
        # If we have hsrp, the active gw is listed last
        # else, we select the one with lowest ip
        if gws[-1].hsrp:
            gw = gws[-1]
        else:
            gw = gws[0]
        gwNetbox = gw.gwport.module.netbox
        gwLink = urlbuilder.createLink(gwNetbox, content=gw.gwip)
        return "%s /%s (%s) " % (gwLink, netmasklen, netmask)

    def showVlan(self):
        if self.prefix:
            vlan = self.prefix.vlan
            vlan = urlbuilder.createLink(vlan,
                                         content="Vlan %s" % vlan.vlan)
        else:
            vlan = 'Unknown'
        return vlan

    def showSw(self):
        sw = self.getChildrenIterator(manage.Swport, 'to_netbox')
        if not sw:
            return 'Unknown'
        vlanList = []
        swList = []
        for i in sw:
            # vlan = i.vlan
            vlans = i.getChildrenIterator(manage.Swportvlan)
            for vlan in vlans:
                if i not in swList and vlan.direction=='n':
                    vlanList.append(vlan)
                    swList.append(i)
        #if len(vlans) > 1:
        #    return 'Unknown'
        #if len(swList) > 1:
            #raise str(swList)
        #    return 'Unknown'
        # raise str(swList)
        result = html.Division()
        #sw = swList[0]
        for sw in swList:
            swNetbox = sw.module.netbox
            swPort = sw.interface or sw.port
            swModule = sw.module.module
            swLink = urlbuilder.createLink(swNetbox)
            swLink.append('(Module %s, Interface %s)' % (swModule, swPort))
            div = html.Division()
            div.append(swLink)
            result.append(div)
        return result

    def showUptime(self):
        uptime = (DateTime.now() - self.upsince)
        formatted = ''
        if uptime.day == 1:
            formatted += '1 day '
        if uptime.day > 1:
            formatted += str(uptime.day) + ' days '
        if uptime.hour == 1:
            formatted += '1 hour '
        if uptime.hour > 1:
            formatted += str(uptime.hour) + ' hours '
        if uptime.minute == 1:
            formatted += '1 minute'
        if uptime.minute > 1:
            formatted += str(uptime.minute) + ' minutes'
        return formatted

    def showIp(self):
        return str(self.ip)

    def availability(self):
        TIMERANGES = ('day', 'week', 'month')
        rrdfiles = self.getChildren(manage.Rrd_file,
                                      where="subsystem='pping'")
        if not rrdfiles:
            return "Unknown"
        rrdfile = rrdfiles[0]
        datasources = [ds for ds in
                       rrdfile.getChildrenIterator(manage.Rrd_datasource)]
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
        alerts = self.getChildren(manage.Alerthist,
                                  orderBy='start_time',
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

            msg = [m for m in
                   alert.getChildrenIterator(manage.Alerthistmsg,
                                             where="""msgtype='sms' """)]

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
        div.append(html.Division('See <a href="/devicemanagement/?view_netbox=%d&history=1">Device History</a> for more details.' % self.netboxid.netboxid))
        return div

    def showServices(self, sort):
        try:
            table = ServiceTable(netboxes=(self,), sort=sort)
        except NoServicesFound:
            return None
        div = html.Division()
        div.append(html.Header("Service availability", level=3))
        div.append(table.html)
        return div

    def showLinks(self):
        # Vi må hente ifra swport-tabellen istedet!
        up = self.getChildrenIterator(manage.Swport, 'to_netbox')
        down = []
        for module in self.getChildrenIterator(manage.Module):
            modLinks = module.getChildrenIterator(manage.Swport, 'module')
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
        rrdfiles = self.getChildrenIterator(manage.Rrd_file,
                   where="not subsystem in ('pping', 'serviceping')")
        if not rrdfiles:
            return None
        result = html.Division()
        result.append(html.Header("Statistics", level=3))
        rrdlist = html.UnorderedList()
        all = []
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

            for ds in rrd.getChildrenIterator(manage.Rrd_datasource):
                link = urlbuilder.createLink(subsystem='rrd',
                                             id=ds.rrd_datasourceid,
                                             division="datasources",
                                             content=(ds.descr or "(unknown)"))
                all.append(ds.rrd_datasourceid)
                rrdlist.append(html.ListItem(link))
        if not all:
            # skip if only ports where defined
            return None
        link = urlbuilder.createLink(subsystem='rrd',
                    id=all, division="datasources", content="[All]")
        rrdlist.append(html.ListItem(link))
        result.append(rrdlist)
        return result

    def showPorts(self, activePerspective='standard', interval=30):
        # ugly, but only those categorys have swports or gwports
        if self.cat.catid not in ('GW', 'GSW', 'SW', 'EDGE'):
            return None

        div = html.Division(_class="ports")
        div.append(html.Header('Port view', level=3))

        def perspectiveToggler(active):
            div = html.Division(_class="tabs")
            list = html.UnorderedList()
            div.append(list)

            perspectives = []
            if self.cat.catid in ('GSW', 'SW', 'EDGE'):
                perspectives.append(
                    ('Switch port status', 'portstatus', 'standard'))
                perspectives.append(
                    ('Switch port activity', 'activeports', 'active'))
            if self.cat.catid in ('GW', 'GSW'):
                perspectives.append(
                    ('Router port status', 'gwportstatus', 'gwstandard'))

            for p in perspectives:
                if active == p[2]:
                    list.append(html.ListItem(
                        html.Anchor(p[0]), _class='tabactive'))
                else:
                    list.append(html.ListItem(
                        html.Anchor(p[0], href='#',
                                    onClick="showPorts('%s'); return false" %
                                    p[1])))
            return div

        def intervalForm():
            form = html.Form(method="GET", action="")
            form.append(html.Hidden(name='perspective', value='active'))
            label = html.Label('Interval (in days):')
            label['for'] ='interval'
            form.append(label)
            form.append(html.Textfield(id='interval', name='interval',
                                       value=interval, size=3))
            form.append(html.Submit(value='Recheck activity'))
            return form

        def showPerspective(perspective, id):
            result = html.Division(id=id)
            result.append(perspectiveToggler(perspective))
            div = html.Division(_class='tabcontent')
            result.append(div)
            div.append(module.showModuleLegend(perspective=perspective,
                                               interval=interval))

            if perspective == 'active':
                div.append(intervalForm())
            modules = [m for m in self.getChildrenIterator(module.ModuleInfo)]
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
                try:
                    moduleView = mod.showModule(perspective=perspective,
                                                interval=interval)
                    if moduleView:
                        div.append(moduleView)
                except AttributeError:
                    pass
            return result

        if self.cat.catid == 'GW':
            activePerspective = 'gwstandard'

        if self.cat.catid in ('GSW', 'SW', 'EDGE'):
            std = showPerspective('standard', 'portstatus')
            act = showPerspective('active', 'activeports')
        else:
            std = None
            act = None
        if self.cat.catid in ('GW', 'GSW'):
            gwstd = showPerspective('gwstandard', 'gwportstatus')
        else:
            gwstd = None

        if std:
            if not activePerspective == 'standard':
                std['style'] = 'display: none;'
            div.append(std)
        if act:
            if not activePerspective == 'active':
                act['style'] = 'display: none;'
            div.append(act)
        if gwstd:
            if not activePerspective == 'gwstandard':
                gwstd['style'] = 'display: none;'
            div.append(gwstd)
        return div

    def showLastUpdate(self):
        unixEpoch = DateTime.DateTime(1970)
        refreshUrl = urlbuilder.createUrl(division='netbox',
                                          id=self.netboxid.netboxid) + \
                                          '?refresh=1'
        refreshLink = html.Anchor('(Force refresh)', href=refreshUrl)

        infoBits = [i for i in
                    self.getChildrenIterator(manage.Netboxinfo,
                                             where="var='lastUpdated'")]
        if len(infoBits) > 0:
            try:
                lastUpdated = long(infoBits[0].val)
            except ValueError:
                return '(Invalid value in database)'

            # lastUpdated value is actually the number of milliseconds since
            # the epoch (apparently UTC time, not local), we use DateTime to
            # calculate a usable timestamp.
            lastUpdated = unixEpoch + \
                          DateTime.oneSecond * (lastUpdated / 1000.0)
            return "%s %s" % (str(lastUpdated.localtime()), refreshLink)
        else:
            return "N/A " + str(refreshLink)

    def showSoftware(self):
        return str(self.device.sw_ver or "N/A")

    def showSerialNumber(self):
        return str(self.device.serial or "N/A")

    def showModuleCount(self):
        count = len(manage.Module.getAllIDs(where='netboxid=%d'
                                            % self.netboxid.netboxid))
        return '<a href="/report/modules?sysname=%s">%d</a>' \
            % (self.sysname, count)

    def showSwportCount(self):
        count = 0
        modules = manage.Module.getAllIterator(where='netboxid=%d'
                                               % self.netboxid.netboxid)
        for module in modules:
            count += len(manage.Swport.getAllIDs(where='moduleid=%d'
                                                 % module.moduleid))
        return '<a href="/report/swport?b1.netboxid=%d">%d</a>' \
            % (self.netboxid.netboxid, count)

    def showGwportCount(self):
        count = 0
        modules = manage.Module.getAllIterator(where='netboxid=%d'
                                               % self.netboxid.netboxid)
        for module in modules:
            count += len(manage.Gwport.getAllIDs(where='moduleid=%d'
                                                 % module.moduleid))
        return '<a href="/report/gwport?netbox.netboxid=%d">%d</a>' \
            % (self.netboxid.netboxid, count)

    def showFirstDiscovered(self):
        return str(self.netboxid.discovered or 'N/A')

    def showActions(self):
        actions = html.Paragraph()
        actions.append('[%s]' % urlbuilder.createLink(self.netboxid,
                                                      subsystem='seeddb',
                                                      content="Edit"))
        actions.append('[%s]' % urlbuilder.createLink(self.netboxid,
                                                      subsystem='maintenance',
                                                      content='Schedule maintenance'))
        actions.append('[<a href="/devicemanagement/?view_netbox=%d&history=1">Device history</a>]'
                       % self.netboxid.netboxid)
        return actions

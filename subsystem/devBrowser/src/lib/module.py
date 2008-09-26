# -*- coding: UTF-8 -*-
#
# Copyright 2002-2004 Norwegian University of Science and Technology
# Copyright 2007 UNINETT AS
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

"""Presentation logic for switchport modules.
Displays the module as a stack of ports, include simple port information
(duplex, speed) in CSS style and for mouse hovering.
"""

try:
    from mod_python import apache
except:
    pass
from nav.db import manage
from nav.web.devBrowser import urlbuilder
from nav import util
import forgetHTML as html
#import warnings
from sets import Set
from datetime import datetime, timedelta

# Color range for port activity tab
color_recent = (116, 196, 118)
color_longago = (229, 245, 224)

# Active result set cache. Will live as long as the Apache child.
active_cache = {}

def process(request):
    import netbox
    netbox = netbox.findNetboxes(request['hostname'])
    if len(netbox) > 1:
        return
    netbox=netbox[0]
    module = findModule(netbox, request['module'])
    request['templatePath'].append((str(netbox),
                                    urlbuilder.createUrl(netbox)))
    request['templatePath'].append(('Module %s' % module.module, None))
    result = html.Division()
    header = html.Header("Module %s at %s" %
                         (module.module,
                         urlbuilder.createLink(module.netbox)), level=2)
    result.append(header)

    perspectives = []
    if netbox.cat.catid in ('GSW', 'SW', 'EDGE'):
        perspectives.append(('Switch port status', 'standard'))
        perspectives.append(('Switch port activity', 'active'))
    if netbox.cat.catid in ('GW', 'GSW'):
        perspectives.append(('Router port status', 'gwstandard'))

    legends = []
    for header, perspective in perspectives:
        legends.append(perspective)
    result.append(showModuleLegend(legends))

    moduleInfo = ModuleInfo(module)
    for header, perspective in perspectives:
        module = moduleInfo.showModule(perspective)
        if module:
            result.append(html.Header(header, level=3))
            result.append(module)

    return result

def findModule(netbox, moduleName):
    moduleName = moduleName.replace("module", "")
    try:
        # Safe variable, must be integer
        module = int(moduleName)
    except TypeError:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

    modules = netbox.getChildren(manage.Module,
                    where="module='%s'" % module)
    if not modules:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

    return modules[0]

class ModuleInfo(manage.Module):
    def showModule(self, perspective='standard', interval=30):
        def findDisplayWidth(ports):
            # Normally we'll show 12 ports in a row, but
            # sometimes (?) 16 could be the one.
            length = len(ports)
            for x in 12,16,8,14:
                if not length % x:
                    return x
            return 12

        def perspectiveStandard(port, portView):
            """Return module view from the standard status perspective"""
            titles = []
            if port.interface:
                # Add the interface name to the popup title
                titles.append(port.interface)
            if port.speed:
                portView['class'] += ' Mb%d' % port.speed
                title = '%d Mbit' % port.speed
                if port.to_netbox:
                    title += ' -> %s' % port.to_netbox
                titles.append(title)
            if type == 'sw':
                if port.link == 'd':
                    portView['class'] += ' disabled'
                    titles.append('disabled')
                elif port.link <> 'y':
                    portView['class'] += ' passive'
                    titles.append('inactive')
                if port.trunk:
                    portView['class'] += ' trunk'
                    titles.append("trunk")
                if port.duplex:
                    portView['class'] += ' %sduplex' % port.duplex
                if port.duplex == 'h':
                    titles.append("half duplex")
                elif port.duplex == 'f':
                    titles.append("full duplex")
                if port.media:
                    titles.append(port.media)
                vlans = port.getChildren(manage.Swportvlan)
                if vlans:
                    vlans = [x.vlan for x in vlans]
                    vlans = map(lambda x: manage.Vlan(x), vlans)
                    vlans = [str(x.vlan) for x in vlans]
                    titles.append('Vlan ' + ','.join(vlans))
                blocked = port.getChildren(manage.Swportblocked)
                if blocked:
                    portView['class'] += ' blocked'
                    vlans = [str(block.vlan) for block in blocked]
                    titles.append("blocked " + ','.join(vlans))
            if type == 'gw':
                if port.portname:
                    titles.append(port.portname)
            return titles

        def perspectiveActive(port, portView):
            """Return module view from the 'last active ports' perspective"""
            titles = []
            if port.interface:
                # Add the interface name to the popup title
                titles.append(port.interface)
            if port.ifindex in active:
                daysago = int(active[port.ifindex])
                if daysago > 1:
                    titles.append("%d days ago" % active[port.ifindex])
                elif daysago == 1:
                    titles.append("%d day ago" % active[port.ifindex])
                else:
                    titles.append("used today")
                bgcolor = gradient[daysago]
                portView['style'] = 'background-color: #%s;' % \
                                    util.colortohex(bgcolor)
                portView['class'] +=  ' active'
            if port.link == 'y':
                titles.append('active now')
                try:
                    portView['style']
                except:
                    portView['style'] = 'background-color: #%s;' % \
                                        util.colortohex(gradient[0])
                portView['class'] +=  ' active link'
            if portView['class'].count('active') == 0:
                titles.append('free')
                portView['class'] +=  ' inactive'
            return titles

        def getActive():
            """Return a dictionary of CAM activity per ifindex.

            ifindex => days since last CAM entry
            """

            # XXX: This is a hack, but caching of this result set reduces page
            # response time by about 75%
            global active_cache

            # Remove expired cache entries
            # Removing items during iteration causes a RuntimeError, so this
            # has to be done in two steps.
            expired = []
            for key, value in active_cache.iteritems():
                if value['expires_at'] < datetime.now():
                    expired.append(key)
            for key in expired:
                del active_cache[key]

            # If cached, get result from cache
            cache_key = (self.netbox.netboxid, interval)
            if cache_key in active_cache:
                return active_cache[cache_key]['result']

            sql = \
                """
                SELECT ifindex,
                       EXTRACT(days FROM
                               CASE WHEN MAX(end_time) = 'infinity' THEN interval '0 days'
                               ELSE NOW() - MAX(end_time)
                               END) AS days_ago
                FROM cam
                WHERE end_time > NOW() - interval '%d days'
                AND netboxid=%s
                GROUP BY ifindex
                ORDER BY ifindex"""
            cursor = self.cursor()
            cursor.execute(sql, (interval, self.netbox.netboxid,))
            active_cache[cache_key] = {
                'result': dict(cursor.fetchall()),
                'expires_at': datetime.now() + timedelta(seconds=60),
            }
            return active_cache[cache_key]['result']

        def sortPortsByInterfaceName(ports):
            """Do natural sort of ports by interface name"""

            import nav.natsort

            map = {}
            list = []
            rest = []
            for port in ports:
                if port.interface is not None:
                    map[port.interface] = port
                    list.append(port.interface)
                else:
                    rest.append(port)
            list.sort(nav.natsort.inatcmp)
            result = []
            for port in list:
                result.append(map[port])
            result.extend(rest)
            return result

        def filterInterfaceName(name):
            """Filter interface names from ifDescr to ifName style"""

            filters = (
                ('Vlan', 'Vl'),
                ('TenGigabitEthernet', 'Te'),
                ('GigabitEthernet', 'Gi'),
                ('FastEthernet', 'Fa'),
                ('Ethernet', 'Et'),
                ('Loopback', 'Lo'),
                ('Tunnel', 'Tun'),
                ('Serial', 'Se'),
                ('Dialer', 'Di'),
                ('-802.1Q vLAN subif', ''),
                ('-ISL vLAN subif', ''),
                ('-aal5 layer', ''),
            )

            for old, new in filters:
                name = str(name).replace(old, new)
            return name

        if perspective.startswith('gw'):
            ports = self.getChildren(manage.Gwport, orderBy=('interface'))
            type = "gw"
        else:
            ports = self.getChildren(manage.Swport, orderBy=('interface'))
            type = "sw"

        if not ports:
            return None

        ports = sortPortsByInterfaceName(ports)
        moduleView = html.Division(_class="module")
        if type == "gw":
            moduleView['class'] += ' gw'
        moduleView.append(html.Header(
            urlbuilder.createLink(self, content=self.module),
            level=3))

        # calc width
        width = findDisplayWidth(ports)
        count = 0
        portTable = html.Table()
        moduleView.append(portTable)
        row = html.TableRow()

        if perspective == 'active':
            active = getActive()
            gradient = util.color_gradient(color_recent, color_longago,
                                           interval)

        for port in ports:
            if count and not count % width:
                portTable.append(row)
                row = html.TableRow()
            count += 1
            if type == 'gw':
                portNr = port.interface
            else:
                portNr = port.interface or port.port or port.ifindex

            portNr = filterInterfaceName(portNr)
            portView = html.TableCell(urlbuilder.createLink(port, content=portNr), _class="port")
            row.append(portView)

            portView['title'] = ""
            if perspective == 'active':
                titles = perspectiveActive(port, portView)
            else:
                titles = perspectiveStandard(port, portView)

            if titles:
                # beautiful! but .capitalize() lowercases everything first
                titles[0] = titles[0][0].upper() + titles[0][1:]
                title = ', '.join(titles)
                portView['title'] = title

        portTable.append(row)
        return moduleView

def showModuleLegend(perspective='standard', interval=30):
    result = html.Division(_class="legend")
    legendtable = html.Table()

    def mkLegend(name, descr, style=None):
        port = html.Span("11")
        port['class'] = "port %s" % name
        if style:
            port['style'] = style
        legenditem = html.TableCell()
        legenditem.append(port)
        legenditem.append(descr)
        return legenditem

    def legendSpeed():
        legend = html.TableRow()
        legend.append(html.TableCell(html.Big("Speed legend")))
        legend.append(mkLegend("passive", "Not active"))
        legend.append(mkLegend("disabled", "Disabled"))
        legend.append(mkLegend("Mb10", "10 Mbit"))
        legend.append(mkLegend("Mb100", "100 Mbit"))
        legend.append(mkLegend("Mb1000", "1 Gbit"))
        legend.append(mkLegend("Mb10000", "10 Gbit"))
        legendtable.append(legend)

    def legendFrame():
        legend = html.TableRow()
        legend.append(html.TableCell(html.Big("Frame legend")))
        legend.append(mkLegend("hduplex", "Half duplex"))
        legend.append(mkLegend("fduplex", "Full duplex"))
        legend.append(mkLegend("trunk", "Trunk"))
        legend.append(mkLegend("blocked", "Blocked"))
        legend.append(html.TableCell())
        legend.append(html.TableCell())
        legendtable.append(legend)

    def legendActive():
        legend = html.TableRow()
        legend.append(html.TableCell(html.Big("Activity legend")))
        legend.append(mkLegend("inactive", "Not used in %d days" % interval))
        legend.append(mkLegend("active", "Used last %d days" % interval,
            "background-color: #%s" % util.colortohex(color_longago)))
        legend.append(mkLegend("active", "Used today",
            "background-color: #%s" % util.colortohex(color_recent)))
        legend.append(mkLegend("active link", "Active now",
            "background-color: #%s" % util.colortohex(color_recent)))
        legend.append(html.TableCell())
        legend.append(html.TableCell())
        legendtable.append(legend)

    if not type(perspective) is list:
        perspective = [perspective]

    legends = Set()
    if 'gwstandard' in perspective:
        legends.add((1, legendSpeed))
    if 'standard' in perspective:
        legends.add((1, legendSpeed))
        legends.add((2, legendFrame))
    if 'active' in perspective:
        legends.add((3, legendActive))

    legends = list(legends)
    legends.sort()
    for order, legend in legends:
        legend()

    result.append(html.Division(legendtable))
    result.append(html.Paragraph(html.Emphasis("Hold mouse over port for info, click for details")))
    return result

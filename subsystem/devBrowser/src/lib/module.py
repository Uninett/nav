# -*- coding: ISO8859-1 -*-
# Copyright 2002-2004 Norwegian University of Science and Technology
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
# 

"""Presentation logic for switchport modules.
Displays the module as a stack of ports, include simple port information
(duplex, speed) in CSS style and for mouse hovering.
"""

from mod_python import apache
from nav.db import manage
from nav.web import urlbuilder
from nav import util
import forgetHTML as html
#import warnings

# Color range for port activity tab
color_recent = (0, 175, 0 )
color_longago = (208, 255, 208)

def process(request):
    # PYTHON IMPORTS ZUCZ=RZZZ!!
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
    result.append("Module %s, netbox %s" % 
                   (module.module,
                   urlbuilder.createLink(module.netbox)))
    result.append(showModuleLegend())                
    moduleInfo = ModuleInfo(module)
    result.append(moduleInfo.showModule())               
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
                    title +=' -> %s' % port.to_netbox
                titles.append(title)
            if type == 'sw':
                if port.link == 'd':
                    portView['class'] += 'disabled'
                elif port.link <> 'y':
                    portView['class'] += 'passive'
                    titles.append('inactive')
                if port.trunk:
                    portView['class'] += ' trunk'
                    titles.append(", trunk")
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
                for item in port._values.items():
                    titles.append("%s %s" % item)
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
                portView['style'] = 'background-color: white;'
                portView['class'] +=  ' inactive'
            return titles

        def getActive():
            """Return a dictionary of CAM activity per ifindex.

            ifindex => days since last CAM entry
            """
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
            active = dict(cursor.fetchall())
            return active

        ports = self.getChildren(manage.Swport, orderBy=('port'))
        if not ports:
            type = "gw"
        else:
            type = "sw"
        #ports += self.getChildren(manage.Gwport)

        if not ports:
            return None

        moduleView = html.Division(_class="module")
        if type == "gw":
            moduleView['class'] += ' gw'
        moduleView.append(html.Header(str(self.module), level=3))
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
            if type=="gw":
                if port.masterindex:
                    portNr = "%s-%s" % (port.masterindex, port.ifindex)
                else:
                    portNr = port.ifindex
            else:
                # Hmmmmmm what's the difference between these?
                # portNr = (port.ifindex is not None and port.ifindex) or port.port
                portNr = port.port
                if not portNr:
                    # warnings.warn("Unknown portNr for %s" % port)
                    continue
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
    legend = html.Division(_class="legend")
    legend.append(html.Header("Legend", level=3))
    def mkLegend(name, descr, style=None):
        port = html.Span("1")
        port['class'] = "port %s" % name
        if style: port['style'] = style
        legend.append(port)
        legend.append(descr)
        legend.append(" ")
    def legendStandard():
        mkLegend("passive", "Not active")
        mkLegend("hduplex", "Half duplex")
        mkLegend("blocked", "Blocked")
        mkLegend("Mb10", "10 Mbit")
        mkLegend("Mb100", "100 Mbit")
        mkLegend("Mb1000", "1 Gbit")
        mkLegend("trunk", "Trunk")
    def legendActive():
        mkLegend("inactive", "Not used in %d days" % interval)
        mkLegend("active", "Used %d days ago" % interval,
                 "background-color: %s" % util.colortohex(color_longago))
        mkLegend("active", "Used today",
                 "background-color: %s" % util.colortohex(color_recent))
        mkLegend("active link", "Active now",
                 "background-color: %s" % util.colortohex(color_recent))
    if perspective == 'active':
        legendActive()
    else:
        legendStandard()
    legend.append(html.Break())
    legend.append(html.Emphasis("Hold mouse over port for info, click for details"))
    return legend

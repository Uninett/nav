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

"""Detailed view of a specific switchport.
In-depth view, includes states, links, vlans
and statistics (RRD).
"""

try:
    from mod_python import apache
except:
    pass
import forgetHTML as html
from nav.db import manage
from nav.web import urlbuilder
import re

_directions = {
    'u': 'undefined',
    'o': 'up',
    'n': 'down',
    'b': 'both',
    'x': 'crossed',
}
_duplex = {
    'f': 'Full duplex',
    'h': 'Half duplex',
}
_link = {
    'd': 'Denied',
    'n': 'Not active',
    'y': 'Active',
}

def process(request):
    import netbox, module
    netbox = netbox.findNetboxes(request['hostname'])
    if len(netbox) > 1:
        return
    netbox = netbox[0]
    module = module.findModule(netbox, request['module'])
    porttype, port = findPort(module, request['port'])
    request['templatePath'].append((str(netbox), 
                                    urlbuilder.createUrl(netbox)))
    request['templatePath'].append(("Module %s" % module.module, 
                                    urlbuilder.createUrl(module)))
    if porttype == 'sw':
        request['templatePath'].append(('Port %s' % port.port, None))
    elif porttype == 'gw':
        request['templatePath'].append(('Port %s' % port.interface, None))
    result = html.Division()
    result.append(showInfo(porttype, port))
    return result

def findPort(module, portName):
    if portName.startswith('gwport'):
        portName = portName.replace("gwport", "").lower()
        allPorts = module.getChildren(manage.Gwport)
        type = 'gw'
    else:
        portName = portName.replace("port", "").lower()
        allPorts = module.getChildren(manage.Swport)
        type = 'sw'
    for p in allPorts:
        if ((type == 'sw' and portName == str(p.port)) or
            (type == 'gw' and portName == str(p.gwportid))):
            return type, p
    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

def showInfo(porttype, port):
    info = html.Division()
    module = port.module
    if porttype == 'sw':
        portname = port.port
        portid = port.port
    elif porttype == 'gw':
        portname = port.interface
        portid = port.gwportid
    info.append(html.Header("Device %s, module %s, port %s" %
                (urlbuilder.createLink(module.netbox),
                urlbuilder.createLink(module, content=module.module),
                portname)))

    table = html.SimpleTable()
    info.append(table)
    for field in ('port', 'interface', 'duplex', 'ifindex', 'portname',
                  'media', 'link', 'speed', 'trunk'):
        try:
            value = getattr(port, field)
        except AttributeError:
            # gwport lacks some fields, so we just skip to the next field
            continue
        if type(value) == bool:
            # convert to a string
            value = value and "y" or "n"
        if value is None:
            continue
        if field == 'duplex':
            value = _duplex.get(value, 'Unknown %s' % value)
        table.add(field.capitalize(), value)
    for field in 'to_netbox', 'to_swport':
        value = getattr(port, field)
        if value is None:
            continue
        title = field.replace("_", " ").capitalize()
        table.add(title, urlbuilder.createLink(value))

    # Actions
    if porttype == 'sw':
        machinetracker = '[<a href="/machinetracker/swp?switch=%s&amp;module=%s&amp;port=%s">Track MAC behind port</a>]' \
            % (module.netbox, module.module, portid)
        actions = '<p>%s</p>' % machinetracker
        info.append(actions)

    rrd = showRrds(porttype, port)
    if rrd:
        info.append(rrd)
    vlanInfo = getVlanInfo(porttype, port)
    if vlanInfo:
        info.append(vlanInfo)
    return info

def getVlanInfo(porttype, port):
    vlans = blocked = None

    if porttype == 'sw':
        vlans = port.getChildren(manage.Swportvlan)
        blocked = port.getChildren(manage.Swportblocked)
        #allowed = port.getChildren(manage.Swportallowedvlan)
    elif porttype == 'gw':
        # FIXME: Are vlan info interesting for gwports? Most of them are
        # already named after the vlan they are handling.
        pass

    if not vlans and not blocked: #and not allowed:
        return None # Nothing to show

    vlanInfo = html.Division()
    vlanInfo.append(html.Header("VLANs", level=2))
    if vlans:
        for vlanlink in vlans:
            vlan = manage.Vlan(vlanlink.vlan)
            line = html.Division()
            try:
                line.append(urlbuilder.createLink(vlan))
            except:
                #raise str(vlan)
                pass
            if vlanlink.direction is not None:
                line.append("(direction %s)" %
                    _directions.get(vlanlink.direction,
                                    "Unknown %s" % vlanlink.direction))
            vlanInfo.append(line)
    if blocked:
        vlanInfo.append(html.Header("Blocked", level=3))
        for vlanlink in blocked:
            vlan = manage.Vlan(vlanlink.vlan)
            div = html.Division()
            try:
                div.append(urlbuilder.createLink(vlan))
            except:
                #raise str(vlan.vlanid)
                pass
            vlanInfo.append(div)

    return vlanInfo

def showRrds(porttype, port):
    netbox = port.module.netbox
    key = value = rrdfiles = None
    if porttype == 'sw':
        key = 'swport'
        value = port.swportid
    elif porttype == 'gw':
        key = 'gwport'
        value = port.gwportid
    if key and value:
        rrdfiles = manage.Rrd_file.getAll(where="key='%s' and value='%s'" \
            % (key, value))
    if not rrdfiles:
        return None
    result = html.Division()
    result.append(html.Header("Statistics", level=2))
    all = []
    for rrd in rrdfiles:
        for ds in rrd.getChildren(manage.Rrd_datasource):
            link = urlbuilder.createLink(subsystem='rrd',
                id=ds.rrd_datasourceid, division="datasources", content=(ds.descr or "(unknown)"))
            all.append(ds.rrd_datasourceid)
            result.append(html.Division(link))
    link = urlbuilder.createLink(subsystem='rrd',
                id=all, division="datasources", content="[All]")
    result.append(html.Division(link))
    return result

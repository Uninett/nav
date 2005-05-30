#
# $Id: machinetracker.py 3106 2005-01-20 10:47:13Z mortenv $
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# Authors: Kristian Eide <kreide@gmail.com>
#
from __future__ import generators
# Catch the test case where we import this module outside the
# mod_python environment
if 'apache' not in globals():
    try:
        from mod_python import apache
    except ImportError:
        apache = None
from pprint import pprint,pformat
from mx import DateTime
from socket import gethostbyaddr,gethostbyname,herror
import re
from nav import db
from nav.web.URI import URI
from nav.web.templates.l2traceTemplate import l2traceTemplate

connection = db.getConnection('webfront', 'manage')
database = connection.cursor()

def isGw(netboxid):
    if netboxid not in gwCache:
        isGw = False
        try:
            database.execute("SELECT netboxid FROM netbox WHERE netboxid="+`netboxid`+" AND catid IN ('GW','GSW')")
            d = database.fetchall()
            isGw = len(d) > 0
        except:
            pass
        gwCache[netboxid] = isGw
    return gwCache[netboxid]

def getIpSysname(netboxid):
    database.execute("SELECT ip, sysname FROM netbox WHERE netboxid="+`netboxid`)
    d = database.fetchall()
    return d[0][0], d[0][1]

def getNetboxidVlan(sysname):
    database.execute("SELECT netboxid, vlan.vlan, swport.swportid FROM netbox JOIN prefix USING(prefixid) JOIN vlan USING(vlanid) LEFT JOIN module USING(netboxid) LEFT JOIN swport USING(moduleid) LEFT JOIN swportvlan ON (swport.swportid=swportvlan.swportid AND direction='o') WHERE sysname LIKE '%"+sysname+"%' OR ip::varchar LIKE '%"+sysname+"%' ORDER BY length(sysname) LIMIT 1")
    d = database.fetchall()
    if len(d) > 0:
        baseNetboxid = None
        baseVlan = None
        mp = MP()
        # Special case for netboxes without uplink (servers)
        netboxid = d[0][0]
        vlan = d[0][1]
        if not d[0][2]:
            database.execute("SELECT netboxid, vlan.vlan, ifindex, module, port FROM swport JOIN module USING(moduleid) JOIN netbox USING(netboxid) JOIN swportvlan USING(swportid) JOIN vlan USING(vlanid) WHERE to_netboxid='"+str(netboxid)+"' LIMIT 1")
            d = database.fetchall()
            if len(d) > 0:
                baseNetboxid = netboxid
                baseVlan = vlan
                netboxid = d[0][0]
                vlan = d[0][1]
                mp = MP(d[0][2], d[0][3], d[0][4])                
            
        return netboxid, vlan, baseNetboxid, baseVlan, mp

    # Try to lookup vlan for host
    vlan = ''
    ip = lookupIp(sysname)
    if ip:
        database.execute("SELECT vlan FROM prefix JOIN vlan USING(vlanid) WHERE '"+ip+"' << netaddr")
        d = database.fetchall()
        if len(d) > 0:
            vlan = d[0][0]
    
    return None, vlan, None, None, MP()

def getBoxForHost(ip):
    # Find match in arp/cam
    try:
        database.execute("select cam.netboxid,cam.ifindex,module.module,swport.port,vlan.vlan from arp join cam using(mac) join swport on (moduleid in (select moduleid from module where module.netboxid=cam.netboxid) and swport.ifindex=cam.ifindex) JOIN module USING(moduleid) join swportvlan using(swportid) join vlan using(vlanid) where ip='" + ip + "' and cam.end_time='infinity' and arp.end_time='infinity' LIMIT 1")
        d = database.fetchall()
        if len(d) > 0:
            return d[0][0], MP(d[0][1], d[0][2], d[0][3]), d[0][4]
    except:
        pass
    return None, None, None

def getPathToGw(netboxid, mpIn, vlan, trunk, path):
    if trunk:
        vlanS = 'trunk'
    else:
        vlanS = vlan
        
    if isGw(netboxid):
        path.append([netboxid, vlanS, mpIn, MP(), 2])
        return True
    
    # Fetch uplink
    database.execute("SELECT a.to_netboxid, a.ifindex, moda.module, a.port, a.trunk, b.ifindex AS to_ifindex, modb.module AS to_module, b.port AS to_port FROM module moda JOIN swport a USING(moduleid) JOIN swportvlan USING (swportid) JOIN vlan USING(vlanid) JOIN swport b ON (a.to_swportid = b.swportid) JOIN module modb ON (b.moduleid=modb.moduleid) WHERE moda.netboxid="+`netboxid`+" AND vlan.vlan="+`vlan`+" AND direction='o' LIMIT 1")
    d = database.fetchall()
    if len(d) == 0:
        #print "Error, " + getSysname(netboxid) + "("+`netboxid`+") has no uplink on vlan " + `vlan` + ", aborting."
        path.append([netboxid, vlanS, mpIn, MP(), 2])
        return False
    if d[0][4] == 1:
        trunk = True
    else:
        trunk = False
        
    mpOut = MP(d[0][1], d[0][2], d[0][3])
    path.append([netboxid, vlanS, mpIn, mpOut, 2])
    
    mpNextIn = MP(d[0][5], d[0][6], d[0][7])
    return getPathToGw(d[0][0], mpNextIn, vlan, trunk, path)

def getPath(host):
    path = []
    id, vlan, baseNetboxid, baseVlan, mpOut = getNetboxidVlan(host)
    if baseNetboxid:
        path.append([baseNetboxid, baseVlan, MP(), MP(), 2])

    ip = host
    if not id:
        ip = lookupIp(host)
        if ip:
            path.append([ip, vlan])
            id, mpOut, vlan = getBoxForHost(ip)
        else:
            path.append([host, vlan])
    foundGw = False
    if id:
        foundGw = getPathToGw(id, mpOut, vlan, False, path)

    if not foundGw:
        # Didn't find GW, look up gw for this vlan
        database.execute("SELECT netboxid, vlan FROM netbox JOIN module USING(netboxid) JOIN gwport USING(moduleid) JOIN gwportprefix USING(gwportid) JOIN prefix ON (gwportprefix.prefixid=prefix.prefixid) JOIN vlan USING(vlanid) WHERE '"+ip+"' << netaddr ORDER BY gwip")
        d = database.fetchall()
        if len(d) > 0:
            path.append([d[0][0], str(d[0][1]), MP(), MP(), 2])

        
    return path

def handler(req):
    global hostCache
    hostCache = {}
    global gwCache
    gwCache = {}
    global ipCache
    ipCache = {}
    
    args = URI(req.unparsed_uri) 
    
    page = l2traceTemplate()
    page.l2tracer = None
    page.form = l2traceForm(args.get("host_from"), args.get("host_to"))

    if args.get("host_from") or args.get("host_to"):
        page.l2tracer = l2traceQuery(args.get("host_from"), args.get("host_to"))
        page.l2tracer.loadTable()

    req.content_type = "text/html"
    req.send_http_header()

    req.write(page.respond())
    return apache.OK

class MP:
    def __init__(self, ifindex='', module='', port=''):
        self.ifindex = ifindex
        self.module = module
        self.port = port

class ResultRow:

    def __init__(self, idx, level=2, netboxid=None, ipaddr='', sysname='', mpIn=MP(), mpOut=MP(), vlan=''):
        self.netboxid = netboxid
        self.ipaddr = ipaddr
        self.sysname = sysname
        self.mpIn = mpIn
        self.mpOut = mpOut
        self.vlan = vlan
        if level == 2:
            self.level = 'L2'
        else:
            self.level = 'L3'
        self.idx = idx

        self.ifindexIn = mpIn.ifindex
        self.ifindexOut = mpOut.ifindex
        self.portIn = str(mpIn.module)
        if mpIn.port:
            self.portIn += '/' + str(mpIn.port)
        self.portOut = str(mpOut.module)
        if mpOut.port:
            self.portOut += '/' + str(mpOut.port)

class l2traceQuery:
    row_idx=0

    def __init__(self, host_from, host_to):
        self.host_from = host_from
        self.host_to = host_to

    def reverse_path_list(self, path):
        path.reverse()
        for x in path:
            if len(x) > 2:
                t = x[2]
                x[2] = x[3]
                x[3] = t
        return path

    def trace(self):
        self.path = []

        if self.host_from:
            self.path = getPath(self.host_from)
            if self.host_to:
                self.path.append(-1)            

        to_path = None
        if self.host_to:
            to_path = getPath(self.host_to)

        # Check if hosts are on the same vlan
        if self.host_from and self.host_to:
            ip_from = lookupIp(self.host_from)
            ip_to = lookupIp(self.host_to)
            if ip_from and ip_to:
                database.execute("SELECT COUNT(prefixid) FROM prefix WHERE '"+ip_from+"' << netaddr OR '"+ip_to+"' << netaddr GROUP BY prefixid")
                d = database.fetchall()
                if d[0][0] == 1:
                    # Same vlan, find first matching box in both lists and remove everything above
                    l1 = []
                    break_outer = False
                    for b1 in self.path:
                        if b1 == -1 or isGw(b1[0]):
                            break
                        l1.append(b1)
                        l2 = []
                        for b2 in to_path:
                            if b1[0] == b2[0] and b1[1]!='trunk' and b1[1] == b2[1]:
                                # Same box
                                for x in self.reverse_path_list(l2):
                                    l1.append(x)
                                to_path = None
                                self.path = l1
                                break_outer = True
                                break
                            l2.append(b2)
                        if break_outer:
                            break
                    

        if to_path:
            for x in self.reverse_path_list(to_path):
                self.path.append(x)

    def getRows(self):
        for row in self.path:
            self.row_idx += 1
            if row == -1:
                yield ResultRow(self.row_idx, 3)
            elif len(row) == 2:
                yield ResultRow(self.row_idx, 2, None, row[0], hostname(row[0]), MP(), MP(), row[1])
            else:
                netboxid, vlan, mpIn, mpOut, level = row
                ip, sysname = getIpSysname(netboxid)
                yield ResultRow(self.row_idx, level, netboxid, ip, sysname, mpIn, mpOut, vlan)
                
    def getTable(self):
        self.trace()
        return [row for row in self.getRows()]

    def loadTable(self):
        self.table = self.getTable()


class l2traceForm:
    def __init__(self,host_from, host_to):
        self.host_from = host_from
        self.host_to = host_to

def lookupIp(host):
    try:
        ip = gethostbyname(host)
    except:
        return None
    return ip

def hostname(ip):
    """Perform a reverse DNS lookup for ip.

    Uses an internal cache to speed up results when the same ip is
    lookup up several times during one session.
    """
    if ip is None:
        return None
    if ip not in hostCache:
        try:
            hostCache[ip] = gethostbyaddr(ip)[0]
        except:
            hostCache[ip] = "--"
    return hostCache[ip]

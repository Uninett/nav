#! /usr/bin/env python
# $Id: machinetracker.py 3106 2005-01-20 10:47:13Z mortenv $
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# Authors: Kristian Eide <kreide@gmail.com>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
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
from socket import gethostbyaddr,gethostbyname,herror
import re
import psycopg2.extras

from nav import db
from nav.web.URI import URI
from nav.web.templates.l2traceTemplate import l2traceTemplate

def isGw(netboxid):
    if netboxid not in gwCache:
        isGw = False
        try:
            database.execute("""
                SELECT netboxid FROM netbox
                WHERE netboxid=%s AND catid IN ('GW','GSW')""",
                (netboxid,))
            d = database.fetchall()
            isGw = len(d) > 0
        except db.driver.ProgrammingError:
            connection.rollback()
        gwCache[netboxid] = isGw
    return gwCache[netboxid]

def getIpSysname(netboxid):
    database.execute("""
        SELECT ip, sysname FROM netbox WHERE netboxid=%s""",
        (netboxid,))
    r = database.fetchall()[0]
    return r['ip'], r['sysname']

def getNetboxidVlan(sysname):
    database.execute("""
        SELECT netboxid, vlan.vlan, swport.swportid
        FROM netbox
            JOIN prefix USING(prefixid)
            JOIN vlan USING(vlanid)
            LEFT JOIN module USING(netboxid)
            LEFT JOIN swport USING(moduleid)
            LEFT JOIN swportvlan ON (swport.swportid=swportvlan.interfaceid AND direction='o')
        WHERE sysname LIKE %s OR ip::varchar LIKE %s
        ORDER BY length(sysname) LIMIT 1""",
        ("%"+sysname+"%",)*2)

    d = database.fetchall()
    if len(d) > 0:
        baseNetboxid = None
        baseVlan = None
        mp = MP()
        # Special case for netboxes without uplink (servers)
        r = d[0]
        netboxid = r['netboxid']
        vlan = r['vlan']

        if not r['swportid']:
            database.execute("""
                SELECT netboxid, vlan.vlan, ifindex, module, port
                FROM swport
                    JOIN module USING(moduleid)
                    JOIN netbox USING(netboxid)
                    JOIN swportvlan ON(swportid=interfaceid)
                    JOIN vlan USING(vlanid)
                WHERE to_netboxid=%s LIMIT 1""",
                (netboxid,))

            d = database.fetchall()
            if len(d) > 0:
                r = d[0]
                baseNetboxid = netboxid
                baseVlan = vlan
                netboxid = r['netboxid']
                vlan = r['vlan']
                mp = MP(r['ifindex'], r['module'], r['port'], r['interface'])

        return netboxid, vlan, baseNetboxid, baseVlan, mp

    # Try to lookup vlan for host
    vlan = ''
    ip = lookupIp(sysname)
    if ip:
        database.execute("""
            SELECT vlan
            FROM prefix
                JOIN vlan USING(vlanid)
            WHERE %s << netaddr""",
            (ip,))
        d = database.fetchall()
        if len(d) > 0:
            vlan = d[0]['vlan']

    return None, vlan, None, None, MP()

def getBoxForHost(ip):
    # Find match in arp/cam
    try:
        database.execute("""
            SELECT cam.netboxid, cam.ifindex, module.module, swport.port,
                swport.interface, vlan.vlan
            FROM arp
                JOIN cam USING(mac)
                JOIN swport ON (moduleid IN
                    (SELECT moduleid FROM module
                     WHERE module.netboxid=cam.netboxid)
                    AND swport.ifindex=cam.ifindex)
                JOIN module USING(moduleid)
                JOIN swportvlan USING(swportid)
                JOIN vlan USING(vlanid)
            WHERE ip=%s AND cam.end_time='infinity' AND arp.end_time='infinity' LIMIT 1""",
            (ip,))

        d = database.fetchall()
        if len(d) > 0:
            r = d[0]
            return r['netboxid'], MP(r['ifindex'], r['module'], r['port'],
                                     r['interface']), r['vlan']
    except db.driver.ProgrammingError:
        connection.rollback()
    return None, None, None

def getPathToGw(netboxid, mpIn, vlan, trunk, gwId, path):
    if trunk:
        vlanS = 'trunk'
    else:
        vlanS = vlan

    #if isGw(netboxid):
    if netboxid == gwId:
        path.append([netboxid, vlanS, mpIn, MP(), 2])
        return True

    # Fetch uplink
    database.execute("""
        SELECT a.to_netboxid, a.ifindex, moda.module, a.port,
            a.interface, a.trunk, b.ifindex AS to_ifindex,
            modb.module AS to_module, b.port AS to_port,
            b.interface AS to_interface
        FROM module moda
            JOIN swport a USING(moduleid)
            JOIN swportvlan ON(swportid=interfaceid)
            JOIN vlan USING(vlanid)
            JOIN swport b ON (a.to_swportid = b.swportid)
            JOIN module modb ON (b.moduleid = modb.moduleid)
        WHERE moda.netboxid=%s AND vlan.vlan=%s AND
            direction='o' LIMIT 1""",
        (netboxid, vlan))

    d = database.fetchall()
    if len(d) == 0:
        #print "Error, " + getSysname(netboxid) + "("+`netboxid`+") has no uplink on vlan " + `vlan` + ", aborting."
        path.append([netboxid, vlanS, mpIn, MP(), 2])
        return False
    r = d[0]
    if r['trunk'] == 1:
        trunk = True
    else:
        trunk = False

    mpOut = MP(r['ifindex'], r['module'], r['port'], r['interface'])
    path.append([netboxid, vlanS, mpIn, mpOut, 2])

    mpNextIn = MP(r['to_ifindex'], r['to_module'], r['to_port'],
                  r['to_interface'])
    return getPathToGw(r['to_netboxid'], mpNextIn, vlan, trunk, gwId, path)

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
        # Find correct netboxid for GW
        database.execute("""
            SELECT module.netboxid
            FROM vlan
                JOIN prefix USING(vlanid)
                JOIN gwportprefix ON (prefix.prefixid = gwportprefix.prefixid AND (hsrp='t' OR gwip::text IN
                    (SELECT MIN(gwip::text) FROM gwportprefix GROUP BY prefixid HAVING COUNT(DISTINCT hsrp) = 1)))
                JOIN gwport ON(gwportid=interfaceid)
                JOIN module USING(moduleid)
            WHERE vlan=%s""",
            (vlan,))

        d = database.fetchall()
        gwId = None
        if len(d) > 0:
            gwId = d[0]['netboxid']
        foundGw = getPathToGw(id, mpOut, vlan, False, gwId, path)

    if not foundGw:
        path.append(['Path to router not found', 'error'])
        # Didn't find GW, look up gw for this vlan
        d = []
        try:
            database.execute("""
                SELECT netboxid, vlan
                FROM netbox
                    JOIN module USING(netboxid)
                    JOIN gwport USING(moduleid)
                    JOIN gwportprefix USING(gwportid)
                    JOIN prefix ON (gwportprefix.prefixid=prefix.prefixid)
                    JOIN vlan USING(vlanid)
                WHERE %s << netaddr ORDER BY gwip""",
                 (ip,))

            d = database.fetchall()
        except db.driver.ProgrammingError:
            connection.rollback()
        if len(d) > 0:
            path.append([d[0]['netboxid'], str(d[0]['vlan']), MP(), MP(), 2])
        else:
            path.append(['Host not active', 'error'])

    return path

def handler(req):
    global hostCache
    hostCache = {}
    global gwCache
    gwCache = {}
    global ipCache
    ipCache = {}

    global connection
    connection = db.getConnection('webfront', 'manage')
    global database
    database = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

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
    def __init__(self, ifindex='', module='', port='', interface=''):
        self.ifindex = ifindex
        self.module = module
        self.port = port
        self.interface = interface

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

        self.hostOk = True
        if self.vlan == 'error':
            self.level = ''
            self.vlan = ''
            self.hostOk = False

        self.ifindexIn = mpIn.ifindex
        self.ifindexOut = mpOut.ifindex
        self.portIn = str(mpIn.module)
        if mpIn.interface or mpIn.port:
            self.portIn += '/' + str(mpIn.interface or mpIn.port)
        self.portOut = str(mpOut.module)
        if mpOut.interface or mpOut.port:
            self.portOut += '/' + str(mpIn.interface or mpOut.port)

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
                database.execute("""
                    SELECT COUNT(prefixid)
                    FROM prefix
                    WHERE %s << netaddr OR %s << netaddr
                    GROUP BY prefixid""",
                    (ip_from, ip_to))

                r = database.fetchall()[0]
                if r['count'] == 1:
                    # Same vlan, find first matching box in both lists and remove everything above
                    l1 = []
                    break_outer = False
                    for b1 in self.path:
                        if b1 == -1:
                            break
                        l1.append(b1)
                        l2 = []
                        for b2 in to_path:
                            if b1[0] == b2[0] and b1[1]!='error':
                                # Same box
                                if len(b1) >= 4 and len(b2) >= 3:
                                    b1[3] = b2[2] # Connect up the ports
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
    if host is None:
        return None
    if host not in ipCache:
        try:
            ipCache[host] = gethostbyname(host)
        except:
            ipCache[host] = None
    return ipCache[host]

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
            hostCache[ip] = ''
    return hostCache[ip]

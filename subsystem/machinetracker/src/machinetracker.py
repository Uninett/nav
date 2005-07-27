# -*- coding: ISO8859-1 -*-
# $Id$
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
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
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
from nav.web.templates.MachineTrackerTemplate import MachineTrackerTemplate

connection = db.getConnection('webfront', 'manage')
database = connection.cursor()

def handler(req):
    global hostCache
    hostCache = {}
    
    args = URI(req.unparsed_uri) 
    
    section = ""
    s = re.search("\/(\w+?)(?:\/$|\?|\&|$)",req.uri)
    if s:   
        section = s.group(1)

    page = MachineTrackerTemplate()
    page.tableCam = None
    page.tableArp = None
    page.tableSwp = None
    tracker = None

    if section.lower() == "mac":
        page.form = MACForm(args.get("mac"), args.get("days"), args.get("dns"),
                            args.get("aip"), args.get("naip"))
        if args.get("mac"):
            tracker = MACSQLQuery(args.get("mac"), args.get("days"))
            page.tableCam = tracker
    elif section.lower() in ("switchports", "switchport", "swport", "port",
                                 "swp"):
        page.form = SwPortForm(args.get("switch"), args.get("module"),
                               args.get("port"), args.get("days"),
                               args.get("dns"), args.get("aip"),
                               args.get("naip"))
        if args.get("switch"):
            tracker = SwPortSQLQuery(args.get("switch"), args.get("module"),
                                     args.get("port"), args.get("days"))
            page.tableSwp = tracker
    else:
        prefixid = args.get("prefixid")
        if prefixid:
            sql = "select netaddr from prefix where prefixid=%s" % prefixid
            database.execute(sql)
            (host,mask) = database.fetchone()[0].split("/")
            from_ip = IP(host).toIP()
            to_ip = IP(IP(host)+pow(2,32-int(mask))-1).toIP()
            
        else:
            from_ip = args.get("from_ip")
            to_ip = args.get("to_ip")

        page.form = IPForm(from_ip, to_ip, args.get("days"), args.get("dns"),
                           args.get("aip"), args.get("naip"))
                
        if from_ip or to_ip:
            # If only one IP field was filled, use the same value for
            # both from- and to-fields.  Perform the old switcheroo if
            # the latter IP is greater than the former.
            if from_ip and not to_ip:
                to_ip = from_ip
            elif to_ip and not from_ip:
                from_ip = to_ip
            elif IP(from_ip) > IP(to_ip):
                temp_ip = to_ip
                to_ip = from_ip
                from_ip = temp_ip
            
            tracker = IPSQLQuery(from_ip, to_ip, args.get("days"))
            page.tableArp = tracker

    if tracker:
        tracker.loadTable(args.get("dns"), args.get("aip"),
                         args.get("naip"))
    if page.tableCam:
        ipTracker = IPSQLQuery(days = args.get("days"),
                               macTracker = tracker)
        ipTracker.loadTable(dns=args.get("dns"))
        page.tableArp = ipTracker

    req.content_type = "text/html"
    req.send_http_header()

    req.write(page.respond())
    return apache.OK


class MachineTrackerSQLQuery:

    def __init__(self, days=7, order_by=""):
        if not days:
            days = 7
        from_time = DateTime.today()-(int(days)*DateTime.oneDay)
        from_time = from_time.strftime("%Y-%m-%d")
        self.where = ["end_time  > '%s'" % from_time]
        
        if not order_by:
            order_by = "arp.ip,arp.mac,cam.sysname,module,port,start_time"
        self.order_by = order_by
        self.select = ""
            
    def sql(self):
        where = " AND ".join(self.where)
        return """%s WHERE %s ORDER BY %s""" % (self.select,
                                                where,
                                                self.order_by)

    def execute(self):
        sql = self.sql()
        if apache:
            apache.log_error("MachineTracker query: " + sql,
                             apache.APLOG_NOTICE)
        database.execute(sql)
        self.result = database.fetchall()
        if self.result and apache:
            apache.log_error("MachineTracker query returned %d results" %
                             len(self.result),
                             apache.APLOG_NOTICE)
        return self.result

    def getRows(self, dns=False, active=False, nonActive=False):
        yield None

    def getTable(self, dns=False, active=False, nonActive=False):
        if not active and not nonActive:
            active = True

        newresult = []
        self.execute()
        return [row for row in self.getRows(dns, active, nonActive)]

    def loadTable(self, dns=False, active=False, nonActive=False):
        self.table = self.getTable(dns, active, nonActive)


class ResultRow:

    def __init__(self, ipaddr, mac, switch, module, port, start_time, end_time,
                 dns=False):
        self.ipaddr = ipaddr
        self.mac = mac
        self.switch = switch
        self.module = module
        self.port = port
        
        if start_time is not None:
            self.start_time = start_time.strftime("%Y-%m-%d %H:%M")
        else:
            self.start_time = None

        if end_time is not None:
            if end_time.year > DateTime.now().year + 1:
                self.end_time = "Still active"
            else:
                self.end_time = end_time.strftime("%Y-%m-%d %H:%M")
        else:
            self.end_time = None

        if dns:
            self.dnsname = hostname(ipaddr)
        else:
            self.dnsname = ""


class MACSQLQuery(MachineTrackerSQLQuery):

    def __init__(self,mac=None,days=7):
        MachineTrackerSQLQuery.__init__(self, days)
        self.select = ("SELECT mac, sysname, module, port, start_time,  " +
                       "end_time FROM cam")
        if mac:
            mac = re.sub("[^0-9a-fA-F%*]+","",mac)
            mac = mac.lower()
            if mac.startswith("*") or mac.endswith("*"):
                self.where.append("mac ILIKE '%s'" % mac.replace("*","%"))
            else:
                self.where.append("mac = '%s'" % mac)
        self.order_by = "mac,sysname,module,port,start_time DESC"

    def getRows(self, dns=False, active=False, nonActive=False):
        lastKey = None
        for row in self.result:
            mac, switch, module, port, start, end = row
            key = (mac, switch, module, port)
            if key == lastKey:
                yield ResultRow(None, None, None, None, None, start, end,
                                False)
            else:
                lastKey = key
                yield ResultRow(None, mac, switch, module, port, start, end,
                                False)


class IPSQLQuery(MachineTrackerSQLQuery):

    def __init__(self, ip_from=None, ip_to=None, days=7, macTracker=None):
        MachineTrackerSQLQuery.__init__(self, days)

        self.select = ("SELECT ip, mac, start_time AS start, " +
                       "end_time AS end FROM arp")

        if not macTracker:
            ip_from = re.sub("[^0-9.]+","",ip_from)
            ip_to = re.sub("[^0-9.]+","",ip_to)
            self.ip_from = ip_from
            self.ip_to = ip_to

            self.where.append("ip BETWEEN '%s' AND '%s'" % (ip_from,ip_to))
            self.order_by = "ip,mac,start_time DESC"
        else:
            # Perform a search for MAC addresses in the arp table,
            # instead of the typical IP search.  This hack uses the
            # mac limitation from the WHERE clause of a MACSQLQuery.
            self.macTracker = macTracker
            self.where.append(macTracker.where[-1])
            self.order_by = "mac,ip,start_time DESC"
            # Replace the "advanced" IP table generator for a simpler
            # one when searching for a MAC address
            self.getRows = self.getRowsMac

    def getRowsMac(self, dns=False, active=False, nonActive=False):
        lastKey = None
        for row in self.result:
            ipaddr, mac, start, end = row
            key = (ipaddr, mac)
            if key == lastKey:
                yield ResultRow(None, None, None, None, None, start, end, dns)
            else:
                lastKey = key
                yield ResultRow(ipaddr, mac, None, None, None, start, end, dns)

    def getRows(self, dns=False, active=False, nonActive=False):
        currentRow = 0 # Counts current row in SQL result set
        firstIP = IP(self.ip_from)
        lastIP = IP(self.ip_to)
        ipCounter = IP(self.ip_from)
        lastKey = None

        while ipCounter <= lastIP:
            isActive = False
            while True:
                try:
                    ipaddr, mac, start, end = self.result[currentRow]
                    key = (ipaddr, mac)
                except IndexError:
                    break
                if IP(ipaddr) == ipCounter:
                    isActive = True
                    currentRow += 1
                    if active:
                        if key == lastKey:
                            yield ResultRow(None, None, None, None, None,
                                            start, end, dns)
                        else:
                            lastKey = key
                            yield ResultRow(ipaddr, mac, None, None, None,
                                            start, end, dns)
                else:
                    break

            if nonActive and not isActive:
                yield ResultRow(ipCounter.toIP(), None, None, None, None,
                                None, None, dns)
            ipCounter += 1
            
        
class SwPortSQLQuery(MACSQLQuery):

    def __init__(self, ip, module, port, days=7):
        MACSQLQuery.__init__(self, mac=None, days=days)

        self.order_by = "sysname, module, port, mac, start_time DESC"
        self.where.append("sysname ILIKE '%s%%'" % ip)
        if module and module != "*":
            self.where.append("module = '%s'" % module)
        if port and port != "*":
            self.where.append("port = '%s'" % port)

class MachineTrackerForm:

    def __init__(self,days="",dns="",active="",nonActive=""):
        offon = ['off', 'on']
        self.dns = offon[bool(dns)]
        self.days = days

        if not active and not nonActive:
            active = True
        self.aip = offon[bool(active)]
        self.naip = offon[bool(nonActive)]
        self.search = ""

class IPForm (MachineTrackerForm):

    def __init__(self,ip_from,ip_to,days,dns,active,nonActive): 
        MachineTrackerForm.__init__(self,days,dns,active,nonActive)
        self.ip_from = ip_from
        self.ip_to = ip_to
        self.search = "ip"

class MACForm (MachineTrackerForm):
    
    def __init__(self,mac,days,dns,active,nonActive):
        MachineTrackerForm.__init__(self,days,dns,active,nonActive)
        self.mac = mac
        self.search = "mac"

class SwPortForm (MachineTrackerForm):

    def __init__(self, switch, module="*", port="*", days="", dns="",
                 active="", nonActive=""):
        MachineTrackerForm.__init__(self,days,dns,active,nonActive)
        self.switch = switch
        self.module = module
        self.port = port
        self.search = "swp" 

class IP(long):
    def __new__(cls, value):
        if type(value) == str and value.count('.') == 3:
            return cls.fromIP(value)
        return long.__new__(cls, value)

    def fromIP(cls, value):
        splitted = value.split('.')
        result = 0
        for part in splitted:
            # Shift 1 byte
            result <<= 8      
            result += long(part)
        return long.__new__(cls, result)

    fromIP = classmethod(fromIP)

    def toIP(self):
        number = self        
        result = []
        while number >0:
            result.append(str(number % 256))
            number >>= 8
        # Ok -- extend with 0s
        result.extend(["0"] * (4-len(result)))
        result.reverse()
        return '.'.join(result)
    def __repr__(self):
        return self.toIP()
    def __add__(self, value):
        return IP(long.__add__(self, value))
    def __sub__(self, value):
        return IP(long.__sub__(self, value))
        return IP(long.__add__(self, value))


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
        except herror:
            hostCache[ip] = "--"
    return hostCache[ip]

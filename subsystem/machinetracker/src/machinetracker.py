# -*- coding: UTF-8 -*-
# $Id$
#
# Copyright 2003-2004 Norwegian University of Science and Technology
# Copyright 2006-2008 UNINETT AS
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
from pprint import pprint, pformat
from mx import DateTime
from socket import gethostbyaddr, gethostbyname, herror
import re
import IPy
import logging

from nav import db
from nav.web.URI import URI
from nav.web.templates.MachineTrackerTemplate import MachineTrackerTemplate

logger = logging.getLogger("nav.web.machinetracker")
connection = db.getConnection('webfront', 'manage')
database = connection.cursor()

def handler(req):
    global hostCache
    hostCache = {}

    args = URI(req.unparsed_uri)

    section = ""
    s = re.search("\/(\w+?)(?:\/$|\?|\&|$)", req.uri)
    if s:
        section = s.group(1)

    # Create initial menu
    menu = []
    menu.append({'link': 'ip', 'text': 'IP Search', 'admin': False})
    menu.append({'link': 'mac', 'text': 'MAC Search', 'admin': False})
    menu.append({'link': 'swp', 'text': 'Switch Search', 'admin': False})

    page = MachineTrackerTemplate()
    page.menu = menu
    page.tableCam = None
    page.tableArp = None
    page.tableSwp = None
    page.errors = []
    tracker = None

    if section.lower() == "mac":
        page.current = 'mac'
        page.title = 'MAC Search'
        page.form = MACForm(args.get("mac"), args.get("days"), args.get("dns"),
                            args.get("aip"), args.get("naip"))
        if args.get("mac"):
            tracker = MACSQLQuery(args.get("mac"), args.get("days"))
            page.tableCam = tracker
    elif section.lower() in ("switchports", "switchport", "swport", "port",
                                 "swp"):
        page.current = 'swp'
        page.title = 'Switch Search'
        page.form = SwPortForm(args.get("switch"), args.get("module"),
                               args.get("port"), args.get("days"),
                               args.get("dns"), args.get("aip"),
                               args.get("naip"))
        if args.get("switch"):
            tracker = SwPortSQLQuery(args.get("switch"), args.get("module"),
                                     args.get("port"), args.get("days"))
            page.tableSwp = tracker
    else:
        page.current = 'ip'
        page.title = 'IP Search'

        prefixid = args.get("prefixid")
        if prefixid:
            sql = "select netaddr from prefix where prefixid=%s"
            database.execute(sql, (prefixid,))
            subnet = IPy.IP(database.fetchone()[0])
            from_ip = subnet[0]
            to_ip = subnet[-1]

        else:
            from_ip = args.get("from_ip")
            if from_ip:
                try:
                    from_ip = IPy.IP(from_ip)
                except ValueError:
                    page.errors.append('%s is not a valid IP address' % \
                                       repr(from_ip))
            to_ip = args.get("to_ip")
            if to_ip:
                try:
                    to_ip = IPy.IP(to_ip)
                except ValueError:
                    page.errors.append('%s is not a valid IP address' % \
                                       repr(to_ip))

        page.form = IPForm(from_ip, to_ip, args.get("days"), args.get("dns"),
                           args.get("aip"), args.get("naip"))

        if len(page.errors) == 0 and (from_ip or to_ip):
            # If only one IP field was filled, use the same value for
            # both from- and to-fields.  Perform the old switcheroo if
            # the latter IP is greater than the former.
            if from_ip and not to_ip:
                to_ip = from_ip
            elif to_ip and not from_ip:
                from_ip = to_ip
            elif from_ip > to_ip:
                (from_ip, to_ip) = (to_ip, from_ip)

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


def ip_range(from_addr, to_addr):
    """Generate all IPs between from_addr and to_addr inclusive.

    Should only be used for IPv4 addresses!
    """
    current_addr = from_addr
    while current_addr <= to_addr:
        yield current_addr
        current_addr = IPy.IP(current_addr.ip + 1)


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
            logger.debug("Executing SQL query: %s", sql)
        database.execute(sql)
        self.result = database.fetchall()
        if self.result and apache:
            logger.debug("Query returned %d results", len(self.result))
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

    def __init__(self, mac=None, days=7):
        MachineTrackerSQLQuery.__init__(self, days)
        self.select = ("SELECT mac, sysname, module, port, start_time,  " +
                       "end_time FROM cam")
        if mac:
            mac = re.sub("[^0-9a-fA-F]+", "", mac)
            mac = mac.lower()
            if len(mac) < 12:
                mac_min = mac + '0' * (12 - len(mac))
                mac_max = mac + 'f' * (12 - len(mac))
                self.where.append("mac >= '%s' and mac <= '%s'" % (
                        mac_min, mac_max))
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
        if self.ip_from.version() == 6 or self.ip_to.version() == 6:
            # Never generate results for inactive IPv6 addresses, the
            # result set will usually become HUGE and take forever to
            # compute.
            nonActive = False

        # Generate a list of ip addresses in the result range
        if nonActive:
            addr_range = ip_range(self.ip_from, self.ip_to)
        else:
            # Get IP list from result and remove dupes
            addr_range = set(r[0] for r in self.result)
            addr_range = list(IPy.IP(ip) for ip in addr_range)
            addr_range.sort()

        def in_result(ip_addr):
            """Verify that the next result row, if any, is for ip_addr"""
            return len(self.result) > 0 and \
                   IPy.IP(self.result[0][0]) == ip_addr

        lastKey = None
        for addr in addr_range:
            if in_result(addr):
                # Consume all result records for this IP address
                # This loop assumes the result is sorted by IP,MAC
                while in_result(addr):
                    # Address is active (i.e. part of arp result)
                    ipaddr, mac, start, end = self.result.pop(0)
                    key = (ipaddr, mac)
                    if active:
                        if key == lastKey:
                            yield ResultRow(None, None, None, None, None,
                                            start, end, dns)
                        else:
                            lastKey = key
                            yield ResultRow(ipaddr, mac, None, None, None,
                                            start, end, dns)
            elif nonActive:
                yield ResultRow(addr, None, None, None, None,
                                None, None, dns)


class SwPortSQLQuery(MACSQLQuery):

    def __init__(self, ip, module, port, days=7):
        MACSQLQuery.__init__(self, mac=None, days=days)

        # If ip is an IP address, get hostname. Logic? But of course!
        try:
            IPy.IP(ip)
            ip = hostname(ip)
        except ValueError:
            pass

        self.order_by = "sysname, module, port, mac, start_time DESC"
        self.where.append("sysname ILIKE '%s%%'" % ip)
        if module and module != "*":
            self.where.append("module = '%s'" % module)
        if port and port != "*":
            self.where.append("port = '%s'" % port)

class MachineTrackerForm:

    def __init__(self, days="", dns="", active="", nonActive=""):
        offon = ['off', 'on']
        self.dns = offon[bool(dns)]
        self.days = days

        if not active and not nonActive:
            active = True
        self.aip = offon[bool(active)]
        self.naip = offon[bool(nonActive)]
        self.search = ""

class IPForm (MachineTrackerForm):

    def __init__(self, ip_from, ip_to, days, dns, active, nonActive):
        MachineTrackerForm.__init__(self,days,dns,active,nonActive)
        self.ip_from = ip_from
        self.ip_to = ip_to
        self.search = "ip"

class MACForm (MachineTrackerForm):

    def __init__(self, mac, days, dns, active, nonActive):
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

def hostname(ip):
    """Perform a reverse DNS lookup for ip.

    Uses an internal cache to speed up results when the same ip is
    lookup up several times during one session.
    """
    if ip is None:
        return None
    if ip not in hostCache:
        try:
            hostCache[ip] = gethostbyaddr(str(ip))[0]
        except herror:
            hostCache[ip] = "--"
    return hostCache[ip]

#
# Copyright 2005 Norwegian University of Science and Technology
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
# $Id$
#
"""An IP address information page.

This module is a mod_python handler to extract all available, relevant
information about a single IP address from the NAVdb and display on a
single page.  The page can also be configured to display external
links to information about the IP address.
"""

__author__ = "Morten Vold <morten.vold@ntnu.no>"

import sys
import re
import socket
from UserDict import UserDict
from IPy import IP
try:
    from mod_python import apache
except ImportError:
    print >> sys.stderr, "Unable to import mod_python.apache, " + \
          "probably not running under a mod_python environment!"
else:
    from mod_python.util import FieldStorage
from nav.web.templates.IPInfo import IPInfo
import nav.db
import config
import psycopg2.extras

conn = nav.db.getConnection('default')
cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def handler(req):
    """mod_python handler"""
    req.content_type = 'text/html'
    page = IPInfo()
    page.title = 'IP Info'
    page.target = gettarget(req)
    if page.target:
        try:
            page.info = IPInformation(page.target)
        except TargetError:
            pass
        else:
            page.title += ': ' + page.target
            conf = config.theConfig()
            # Evaluate the info table as per. the local config, and
            # put the output directly into the page (look out!!)
            page.localsiteinfo = conf.output(page.info)
    #page.debug = str(descriptions)

    req.write(page.respond())
    return apache.OK

def gettarget(req):
    form = FieldStorage(req)
    return form.getfirst('ip', '')

class IPInformation(UserDict):
    descriptions = {
        'navreg': 'Registered in NAV',
        'arp': 'Found in ARP data',
        'description': 'VLAN description',
        'org': 'Organization',
        'opt1': 'Org opt1',
        'opt2': 'Org opt2',
        'opt3': 'Org opt3',
        'subnet': 'Subnet',
        'usage': 'VLAN usage',
        'ip': 'IP',
        'dns': 'DNS name',
        'mac': 'Last seen with MAC',
        'switch': 'MAC last seen on switch',
        'module': 'MAC last seen on module',
        'port': 'MAC last seen on port'
        }
    
    def __init__(self, target):
        UserDict.__init__(self)
        self.target = target
        self.retrieveInfo()

    def describe(self, key):
        """Return a slightly verbose description of an information key.

        If the key has no description, the key name is returned instead.
        """
        return self.descriptions.get(key, key)

    def retrieveInfo(self):
        self.resolveTarget()
        self.fetchNetbox()
        self.fetchPrefixInfo()
        self.fetchLastArpEntry()
        self.fetchLastCamEntry()

    def resolveTarget(self):
        "Resolve IP/DNS information for the target"
        try:
            # Is the target an IP address?
            ip = IP(self.target)
        except ValueError:
            try:
                # Is it a DNS name we can look up?
                ip = socket.gethostbyname(self.target)
            except socket.gaierror:
                # Whatever it was, we couldn't use it
                raise TargetError, "Target %s not found" % str(self.target)
            else:
                ip = IP(ip)
        try:
            # Reverse lookup
            host = socket.gethostbyaddr(str(ip))
        except socket.herror:
            self['dns'] = ''
        else:
            self['dns'] = host[0]
        self['ip'] = ip

    def fetchNetbox(self):
        sql = "SELECT sysname FROM netbox WHERE ip=%s"
        cursor.execute(sql, (str(self['ip']),))
        if cursor.rowcount > 0:
            self['navreg'] = cursor.fetchone()[0]

    def fetchLastArpEntry(self):
        sql = "SELECT start_time, mac FROM arp " + \
              "WHERE ip=%s ORDER BY end_time DESC LIMIT 1"
        cursor.execute(sql, (str(self['ip']),))
        if cursor.rowcount > 0:
            self['arp'], self['mac'] = cursor.fetchone()

    def fetchLastCamEntry(self):
        sql = """SELECT COALESCE(ABBREV(ip), cam.sysname) AS switch,
                        module,
                        port
                 FROM cam
                 LEFT JOIN netbox ON (cam.netboxid=netbox.netboxid)
                 WHERE mac=%s
                 ORDER BY end_time DESC LIMIT 1"""
        if 'mac' in self:
          cursor.execute(sql, (str(self['mac']),))
          if cursor.rowcount > 0:
              self.update(cursor.fetchone())

    def fetchPrefixInfo(self):
        sql = """SELECT netaddr as subnet,
                        usageid as usage,
                        description,
                        vlan.orgid as org, 
                        opt1,
                        opt2,
                        opt3
                 FROM prefix
                 LEFT JOIN vlan ON (prefix.vlanid = vlan.vlanid)
                 LEFT JOIN org ON (vlan.orgid = org.orgid)
                 WHERE %s << netaddr
                   AND nettype <> 'scope'"""
        cursor.execute(sql, (str(self['ip']),))
        if cursor.rowcount > 0:
            self.update(cursor.fetchone())

class TargetError(Exception):
    pass

# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Holds meta information on one IPy.IP address."""


from math import ceil
from IPy import IP
from nav import db


class MetaIP:
    """Class for holding meta information on one IPy.IP address"""

    # Class variables for caching
    IPv4MetaMap = None
    IPv6MetaMap = None

    def __init__(self,ip):
        self.netaddr = ip
        self.prefixid = None
        self.active_ip_cnt = None
        self.max_ip_cnt = None
        self.nettype = None
        self.usage_percent = None

        if ip.version() == 4:
            if MetaIP.IPv4MetaMap == None:
                MetaIP.IPv4MetaMap = self._createIpv4MetaMap()
            self._setupIpv4()
        else:
            if MetaIP.IPv6MetaMap == None:
                MetaIP.IPv6MetaMap = self._createIpv6MetaMap()
            self._setupIpv6()

    @classmethod
    def invalidateCache(cls):
        """Class method for invalidating the cache between calls from the
        handler."""

        cls.IPv4MetaMap = None
        cls.IPv6MetaMap = None

    def getTreeNet(self,leadingZeros=True):
        """This method is used to get the string representation of the IP
        shown in the tree to left of the prefix matrix."""

        #IPv6: Whole address
        #IPv4: Not whole address
        if self.netaddr.version() == 6:
            return self._getTreeNetIpv6(leadingZeros)
        elif self.netaddr.version() == 4:
            return self._getTreeNetIpv4()

    def _getTreeNetIpv4(self):
        """Remove host octet."""
        netaddr_string = self.netaddr.net().strNormal()
        return netaddr_string[:netaddr_string.rfind(".")]

    def _getTreeNetIpv6(self,leadingZeros):
        """Compress self.netaddr, remove "::", and padd with ":0"."""
        netaddr = None
        hexlets_in_address = int(float(self.netaddr.prefixlen())/16+0.5)
        if self.netaddr.prefixlen() < 112:
            netaddr = self.netaddr.net().strCompressed()[:-2]
        else:
            netaddr = self.netaddr.net().strCompressed()

        #in case .strCompressed() compressed it too much
        while netaddr.count(":") < hexlets_in_address-1:
            netaddr = ":".join([netaddr,"0"])

        if leadingZeros:
            last_hexlet = netaddr[netaddr.rfind(':')+1:]
            zeros_to_pad = 4-len(last_hexlet)
            last_hexlet = zeros_to_pad*'0' + last_hexlet

            netaddr = netaddr[:netaddr.rfind(':')+1] + last_hexlet

        return netaddr

    @classmethod
    def _createIpv6MetaMap(cls):
        """At the time of writing, neither prefix_active_ip_cnt nor prefix_max_ip_cnt
        contain/calculates the correct values for IPv6. Once this has been fixed, this
        function needs to be changed."""

        sql = """SELECT prefixid, nettype, netaddr
                 FROM prefix LEFT OUTER JOIN vlan USING(vlanid)
                 WHERE family(netaddr)=6"""

        cursor = db.getConnection('default','manage').cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        result = {}
        for row in rows:
            tupple = {}
            tupple["prefixid"] = row[0]
            tupple["nettype"] = row[1]
            result[IP(row[2])] = tupple
        return result

    @classmethod
    def _createIpv4MetaMap(cls):
        sql = """SELECT prefixid, active_ip_cnt, max_ip_cnt, nettype, netaddr
                 FROM prefix LEFT OUTER JOIN prefix_active_ip_cnt USING(prefixid)
                             LEFT OUTER JOIN prefix_max_ip_cnt USING(prefixid)
                             LEFT OUTER JOIN vlan USING(vlanid)
                 WHERE family(netaddr)=4"""

        cursor = db.getConnection('default','manage').cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        result = {}
        for row in rows:
            tupple = {}
            tupple["prefixid"] = row[0]
            tupple["active_ip_cnt"] = row[1]
            tupple["max_ip_cnt"] = row[2]
            tupple["nettype"] = row[3]
            result[IP(row[4])] = tupple
        return result

    def _setupIpv6(self):
        if self.netaddr in MetaIP.IPv6MetaMap:
            metainfo = MetaIP.IPv6MetaMap[self.netaddr]
            self.prefixid = metainfo["prefixid"]
            self.nettype = metainfo["nettype"]
            self.usage_percent = 4

    def _setupIpv4(self):
        if self.netaddr in MetaIP.IPv4MetaMap:
            metainfo = MetaIP.IPv4MetaMap[self.netaddr]
            self.prefixid = metainfo["prefixid"]
            self.nettype = metainfo["nettype"]

            active_ip_cnt = metainfo["active_ip_cnt"]
            max_ip_cnt = metainfo["max_ip_cnt"]

            if active_ip_cnt is None:
                self.active_ip_cnt = 0
            else:
                self.active_ip_cnt = int(active_ip_cnt)

            self.max_ip_cnt = int(max_ip_cnt)

            if self.active_ip_cnt > 0 and self.max_ip_cnt > 0:
                self.usage_percent = int(ceil(100*float(self.active_ip_cnt)/self.max_ip_cnt))
            else:
                self.usage_percent = 0

class UnexpectedRowCountError(Exception): pass

#
# Copyright (C) 2007-2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details. You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Holds meta information on one IPy.IP address."""


import math
from IPy import IP
from nav import db


class MetaIP:
    """Class for holding meta information on one IPy.IP address"""

    # Class variables for caching
    MetaMap = None

    def __init__(self, ip):
        self.netaddr = ip
        self.prefixid = None
        self.nettype = None

        if MetaIP.MetaMap == None:
            MetaIP.MetaMap = self._createMetaMap(ip.version())
        self._setup()

    @classmethod
    def invalidateCache(cls):
        """Class method for invalidating the cache between calls from the
        handler."""
        cls.MetaMap = None

    def getTreeNet(self, leadingZeros=True):
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

    def _getTreeNetIpv6(self, leadingZeros):
        """Compress self.netaddr, remove "::", and padd with ":0"."""
        netaddr = None
        hexlets_in_address = int(float(self.netaddr.prefixlen())/16+0.5)
        if self.netaddr.prefixlen() < 112:
            netaddr = self.netaddr.net().strCompressed()[:-2]
        else:
            netaddr = self.netaddr.net().strCompressed()

        #in case .strCompressed() compressed it too much
        while netaddr.count(":") < hexlets_in_address-1:
            netaddr = ":".join([netaddr, "0"])

        if leadingZeros:
            last_hexlet = netaddr[netaddr.rfind(':')+1:]
            zeros_to_pad = 4-len(last_hexlet)
            last_hexlet = zeros_to_pad*'0' + last_hexlet

            netaddr = netaddr[:netaddr.rfind(':')+1] + last_hexlet

        return netaddr

    @staticmethod
    def _createMetaMap(family):
        sql = """SELECT prefixid, nettype, netaddr
                 FROM prefix LEFT JOIN vlan USING (vlanid)
                 WHERE family(netaddr) = %s""" % family
        cursor = db.getConnection('default', 'manage').cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        result = {}
        for row in rows:
            result[IP(row[2])] = {
                "prefixid": row[0],
                "nettype": row[1],
            }

        return result

    def _setup(self):
        if self.netaddr in MetaIP.MetaMap:
            metainfo = MetaIP.MetaMap[self.netaddr]
            self.prefixid = metainfo["prefixid"]
            self.nettype = metainfo["nettype"]

class UnexpectedRowCountError(Exception): pass

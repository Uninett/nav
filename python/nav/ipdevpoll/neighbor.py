#
# Copyright (C) 2009-2011 UNINETT AS
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
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utility functions for device neighbor identification.

Useful for ipdevpoll plugins who collect neighbor information from neigbor
discovery protocols and such (e.g. CDP, LLDP, switch forwarding tables).

The classes and function within this module operate synchronously, and should
therefore be run in the threadpool instead of the main reactor thread.

"""
import re
from datetime import timedelta
from nav.util import cachedfor

from nav.models import manage
from django.db.models import Q

from nav.ipdevpoll.log import ContextLogger
from nav.ipdevpoll import shadows

@cachedfor(timedelta(minutes=5))
def get_netbox_macs():
    "Returns a dict of (mac, netboxid) mappings of NAV-monitored devices"
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('SELECT mac, netboxid FROM netboxmac')
    netbox_macs = dict(cursor.fetchall())
    return netbox_macs

# pylint: disable=R0903
class Neighbor(object):
    "Abstract base class for neigbor identification"
    _logger = ContextLogger()

    def __init__(self, record):
        self.record = record
        self.netbox = self._identify_netbox()
        self.interface = self._identify_interface()
        self.identified = bool(self.netbox or self.interface)

    def _identify_netbox(self):
        raise NotImplementedError

    def _identify_interface(self):
        raise NotImplementedError

    @classmethod
    def _netbox_from_ip(cls, ip):
        """Tries to find a Netbox from NAV's database based on an IP address.

        :returns: A shadows.Netbox object representing the netbox, or None if no
                  corresponding netbox was found.

        """
        ip = unicode(ip)
        assert ip
        return (cls._netbox_query(Q(ip=ip)) or
                cls._netbox_query(Q(interface__gwportprefix__gw_ip=ip)))

    ID_PATTERN = re.compile(r'(.*\()?(?P<sysname>[^\)]+)\)?')
    @classmethod
    def _netbox_from_sysname(cls, sysname):
        """Tries to find a Netbox from NAV's database based on a sysname string.

        The sysname string is interpreted in various ways that have been seen
        in the wild in CDP and LLDP implementations.  Valid examples are the
        remote device's sysname, with or without a qualified domain name, or a
        string following the "SERIAL(sysname)" pattern.

        :returns: A shadows.Netbox object representing the netbox, or None if no
                  corresponding netbox was found.

        """
        match = cls.ID_PATTERN.search(sysname)
        sysname = match.group('sysname').lower()
        assert sysname
        try:
            sysname.decode('ascii')
        except UnicodeDecodeError:
            return None
        query = Q(sysname=sysname)

        is_fqdn = '.' in sysname
        if not is_fqdn:
            query = query | Q(sysname__startswith=sysname + '.')

        return cls._netbox_query(query)

    @staticmethod
    def _netbox_query(query):
        """Runs a Django get()-query on the Netbox model, based on query.

        :param query: A Q object usable in a Netbox query.
        :returns: A shadows.Netbox object if a db object was found, otherwise
                  None.

        """
        assert query
        try:
            netbox = manage.Netbox.objects.values('id', 'sysname').get(query)
        except manage.Netbox.DoesNotExist:
            return None
        return shadows.Netbox(**netbox)

    def _interface_from_name(self, name):
        """Tries to find an Interface in NAV's database for the already
        identified netbox.

        The ifName, ifDescr and ifAlias attributes are searched for name.

        :returns: A shadows.Interface object representing the interface, or None
                  if no corresponding interface was found.

        """
        if not (self.netbox and name):
            return

        netbox = Q(netbox__id=self.netbox.id)
        ifdescr = netbox & Q(ifdescr=name)
        ifname = netbox & Q(ifname=name)
        ifalias = netbox & Q(ifalias=name)

        return (self._interface_query(ifdescr)
                or self._interface_query(ifname)
                or self._interface_query(ifalias))

    @staticmethod
    def _interface_query(query):
        assert query
        try:
            ifc = manage.Interface.objects.values(
                'id', 'ifname', 'ifdescr').get(query)
        except manage.Interface.DoesNotExist:
            return None

        return shadows.Interface(**ifc)

class CDPNeighbor(Neighbor):
    "Parses a CDP tuple from nav.mibs.cisco_cdp_mib to identify a neighbor"

    def _identify_netbox(self):
        if self.record.ip:
            netbox = self._netbox_from_ip(self.record.ip)

        if not netbox and self.record.deviceid:
            netbox = self._netbox_from_sysname(self.record.deviceid)

        return netbox

    def _identify_interface(self):
        return self._interface_from_name(self.record.deviceport)


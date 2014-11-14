#
# Copyright (C) 2012 UNINETT AS
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
import threading
from itertools import groupby
from IPy import IP
from nav.util import cachedfor, synchronized

from nav.models import manage
from django.db.models import Q

from nav.mibs.lldp_mib import IdSubtypes

from nav.ipdevpoll.log import ContextLogger
from nav.ipdevpoll import shadows
from nav.ipdevpoll.db import autocommit
from nav.ipdevpoll.utils import is_invalid_utf8

HSRP_MAC_PREFIXES = ('00:00:0c:07:ac',)
VRRP_MAC_PREFIXES = ('00:00:5e:00:01', '00:00:5e:00:02') # RFC5798
IGNORED_MAC_PREFIXES = HSRP_MAC_PREFIXES + VRRP_MAC_PREFIXES

@synchronized(threading.Lock())
@cachedfor(timedelta(minutes=5))
@autocommit
def get_netbox_macs():
    """Returns a dict of (mac, netboxid) mappings of NAV-monitored devices.

    Special MAC address will be ignored, such as those reserved by VRRP.

    """
    return _get_netbox_macs()

def _get_netbox_macs():
    """Actual implementation of get_netbox_macs()"""
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('SELECT mac, netboxid FROM netboxmac')
    netbox_macs = dict((mac, netboxid) for (mac, netboxid) in cursor.fetchall()
                       if not _mac_is_ignored(mac))
    return netbox_macs

def _mac_is_ignored(mac):
    for ignored in IGNORED_MAC_PREFIXES:
        if mac.lower().startswith(ignored.lower()):
            return True
    return False

@synchronized(threading.Lock())
@cachedfor(timedelta(minutes=10))
@autocommit
def get_netbox_catids():
    """Returns a dict of {netboxid: catid} pairs of NAV-monitored devices"""
    return _get_netbox_catids()

def _get_netbox_catids():
    """Actual implementation of get_netbox_catids()"""
    catids = dict((i['id'], i['category__id'])
                  for i in manage.Netbox.objects.values('id', 'category__id'))
    return catids

INVALID_IPS = ('None', '0.0.0.0',)

# pylint: disable=R0903
class Neighbor(object):
    "Abstract base class for neigbor identification"
    _logger = ContextLogger()

    def __init__(self, record, local_address=None):
        """Given a supported neighbor record, tries to identify the remote
        device and port among the ones registered in NAV's database.

        If a neighbor can be identified, the identified attribute is set to
        True.  The netbox and interface attributes will represent the
        identified items.

        :param record: Some namedtuple instance representing the
                       neighboring record read from the device.
        :param local_address: The management IP address used by the local
                              system. If supplied, will be used to identify
                              and ignore possible self-loops.

        """
        self.record = record
        self._invalid_neighbor_ips = list(INVALID_IPS)
        if local_address:
            self._invalid_neighbor_ips.append(str(local_address))

        self.netbox = self.interface = None
        self.identified = False

        self.identify()

    def identify(self):
        self.netbox = self._identify_netbox()
        self.interface = self._identify_interface()
        self.identified = bool(self.netbox or self.interface)

    def _identify_netbox(self):
        raise NotImplementedError

    def _identify_interface(self):
        raise NotImplementedError

    def _netbox_from_ip(self, ip):
        """Tries to find a Netbox from NAV's database based on an IP address.

        :returns: A shadows.Netbox object representing the netbox, or None if no
                  corresponding netbox was found.

        """
        try:
            ip = unicode(IP(ip))
        except ValueError:
            self._logger.warn("Invalid IP (%s) in neighbor record: %r",
                              ip, self.record)
            return

        assert ip
        if ip in self._invalid_neighbor_ips:
            return
        return (self._netbox_query(Q(ip=ip)) or
                self._netbox_query(Q(interface__gwportprefix__gw_ip=ip)))

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
        sysname = match.group('sysname')
        assert sysname
        try:
            sysname.decode('ascii')
        except UnicodeDecodeError:
            return None
        query = Q(sysname__iexact=sysname)

        is_fqdn = '.' in sysname
        if not is_fqdn:
            query = query | Q(sysname__istartswith=sysname + '.')

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

        The ifName, ifDescr, ifAlias, and optionally, baseport attributes are
        searched for name.

        :returns: A shadows.Interface object representing the interface, or None
                  if no corresponding interface was found.

        """
        if not (self.netbox and name):
            return

        if is_invalid_utf8(name):
            self._logger.warn("cannot search database for malformed "
                              "neighboring port name %r", name)
            return

        queries = [Q(ifdescr=name), Q(ifname=name), Q(ifalias=name)]
        if name.isdigit():
            queries.append(Q(baseport=int(name)))

        netbox = Q(netbox__id=self.netbox.id)
        for query in queries:
            ifc = self._interface_query(netbox & query)
            if ifc:
                return ifc

    def _interface_query(self, query):
        assert query
        netbox = Q(netbox__id=self.netbox.id)
        try:
            ifc = manage.Interface.objects.values(
                'id', 'ifname', 'ifdescr', 'iftype').get(netbox & query)
        except manage.Interface.DoesNotExist:
            return None

        ifc = shadows.Interface(**ifc)
        ifc.netbox = self.netbox
        return ifc

    def __repr__(self):
        return ('<{myclass} '
                'identified={identified} '
                'netbox={netbox} '
                'interface={interface}>'
                ).format(myclass=self.__class__.__name__,
                         **vars(self))

class CDPNeighbor(Neighbor):
    "Parses a CDP tuple from nav.mibs.cisco_cdp_mib to identify a neighbor"

    def _identify_netbox(self):
        netbox = None
        if self.record.ip:
            netbox = self._netbox_from_ip(self.record.ip)

        if not netbox and self.record.deviceid:
            netbox = self._netbox_from_sysname(self.record.deviceid)

        return netbox

    def _identify_interface(self):
        return self._interface_from_name(self.record.deviceport)


class LLDPNeighbor(Neighbor):
    "Parses an LLDP tuple from nav.mibs.lldp_mib to identify a neighbor"

    def _identify_netbox(self):
        chassid = self.record.chassis_id
        netbox = None
        if chassid:
            lookup = None
            if isinstance(chassid, IdSubtypes.macAddress):
                lookup = self._netbox_from_mac
            elif isinstance(chassid, IdSubtypes.networkAddress):
                lookup = self._netbox_from_ip
            elif isinstance(chassid, IdSubtypes.local):
                lookup = self._netbox_from_sysname

            if lookup:
                netbox = lookup(str(chassid))

        if not netbox and self.record.sysname:
            netbox = self._netbox_from_sysname(self.record.sysname)

        return netbox

    @classmethod
    def _netbox_from_mac(cls, mac):
        mac_map = get_netbox_macs()
        if mac in mac_map:
            return cls._netbox_query(Q(id=mac_map[mac]))

    def _identify_interface(self):
        portid = self.record.port_id
        if self.netbox and portid:
            lookup = None
            if isinstance(portid, (IdSubtypes.interfaceAlias,
                                   IdSubtypes.interfaceName,
                                   IdSubtypes.local)):
                lookup = self._interface_from_name
            elif isinstance(portid, (IdSubtypes.macAddress)):
                lookup = self._interface_from_mac
            elif isinstance(portid, (IdSubtypes.networkAddress)):
                lookup = self._interface_from_ip

            if lookup:
                try:
                    return lookup(str(portid))
                except manage.Interface.MultipleObjectsReturned:
                    portdesc = self.record.port_desc
                    if portdesc:
                        return self._interface_from_name(str(portdesc))

    def _interface_from_mac(self, mac):
        assert mac
        return self._interface_query(Q(ifphysaddress=mac))

    def _interface_from_ip(self, ip):
        ip = unicode(ip)
        assert ip
        if ip in self._invalid_neighbor_ips:
            return
        return self._interface_query(Q(gwportprefix__gw_ip=ip))

def filter_duplicate_neighbors(nborlist):
    """Filters out duplicate neighbors on a port.

    If the duplicates are all subinterfaces of a single master interface, the
    returned Neighbor object's interface attribute will be set to the master
    interface (if one could be found in the db).

    """
    def _keyfunc(nbor):
        return nbor.record.ifindex

    grouped = groupby(sorted(nborlist, key=_keyfunc), _keyfunc)
    for _key, group in grouped:
        group = list(group)
        if len(group) > 1:
            yield _reduce_to_single_neighbor(group)
        else:
            yield group[0]

IFTYPE_L2VLAN = 135
def _reduce_to_single_neighbor(nborlist):
    target_boxes = set(nbor.netbox.id for nbor in nborlist)
    same_netbox = len(target_boxes) == 1
    if same_netbox:
        are_all_subifcs = all(
            nbor.interface and nbor.interface.iftype == IFTYPE_L2VLAN
            for nbor in nborlist)

        if are_all_subifcs:
            pick = nborlist[0]
            ifc = _get_parent_interface(pick.interface)
            pick.interface = ifc
            return pick
    # nuts. Just return one of the records on random, basically
    return nborlist[0]

SUBIF_PATTERN = re.compile(r'(?P<basename>.*)\.(?P<subname>[0-9]+)$')
def _get_parent_interface(ifc):
    # NAV doesn't yet store data from ifStackTable in the database, so we can
    # only guess at the parent interface based on naming conventions (used by
    # Cisco).
    match = SUBIF_PATTERN.match(ifc.ifname)
    if match:
        basename = match.group('basename')
        try:
            parent = manage.Interface.objects.values(
                'id', 'ifname', 'ifdescr', 'iftype').get(
                netbox__id=ifc.netbox.id, ifname=basename)
        except manage.Interface.DoesNotExist:
            pass
        else:
            parent = shadows.Interface(**parent)
            parent.netbox = ifc.netbox
            return parent
    return ifc

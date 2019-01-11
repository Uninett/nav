#
# Copyright (C) 2007, 2010, 2011, 2014 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Layer 2 traceroute web tool for NAV."""

import socket
from socket import gethostbyaddr, gethostbyname

from django.db.models import Q
from nav.models.manage import Netbox, SwPortVlan, GwPortPrefix, Prefix, Arp, Cam
import datetime
from IPy import IP

from nav.util import is_valid_ip

INFINITY = datetime.datetime.max
PATH_NOT_FOUND = None
LAYER_3_PATH = -1


class L2TraceQuery(object):
    def __init__(self, host_from, host_to):
        self.host_from = Host(host_from)
        self.host_to = host_to and Host(host_to)
        self.path = []

    def trace(self):
        if self.host_from:
            self.path = get_path(self.host_from)

        to_path = []
        if self.host_to:
            to_path = get_path(self.host_to)
            reverse_path(to_path)

            if are_hosts_on_same_vlan(self.host_from, self.host_to) and \
                            PATH_NOT_FOUND not in (self.path + to_path):
                self.path = join_at_junction(self.path, to_path)
            else:
                self.path.append(LAYER_3_PATH)
                self.path.extend(to_path)

    def make_rows(self):
        for index, node in enumerate(self.path):
            if node is PATH_NOT_FOUND:
                yield ResultRow(index, ipaddr='Path not found', vlan='error')
            elif node is LAYER_3_PATH:
                yield ResultRow(index, level=3)
            else:
                yield self.make_row_from_node(index, node)

    @staticmethod
    def make_row_from_node(index, node):
        netboxid = hasattr(node.host, 'id') and node.host.id or None
        sysname = hasattr(node.host, 'sysname') and \
                  node.host.sysname or node.host.hostname
        return ResultRow(index,
                         netboxid=netboxid,
                         ipaddr=node.host.ip,
                         sysname=sysname,
                         if_in=node.if_in,
                         if_out=node.if_out,
                         vlan=node.vlan)


def join_at_junction(from_path, to_path):
    from_node, to_node = find_junction(from_path, to_path)
    from_index = from_path.index(from_node)
    to_index = to_path.index(to_node)

    junction_node = PathNode(from_node.vlan, from_node.if_in, from_node.host,
                             to_node.if_out)
    path = from_path[:from_index] + [junction_node] + to_path[to_index + 1:]
    return path


def find_junction(from_path, to_path):
    for from_node in from_path:
        for to_node in to_path:
            if from_node and to_node and from_node.host == to_node.host:
                return (from_node, to_node)
    return (None, None)


def reverse_path(path):
    path.reverse()
    for node in path:
        if node:
            node.swap_in_out_interfaces()


def get_path(addr):
    start_node = get_start_path(addr)
    path = [start_node]
    gateway = get_vlan_gateway(start_node.vlan)

    while path[-1].host != gateway:
        if isinstance(path[-1].host, Netbox):
            uplink = get_vlan_uplink_from_netbox(path[-1].host, path[-1].vlan)
            if uplink:
                path[-1].if_out = uplink.interface
            swpvlan = get_vlan_downlink_to_netbox(path[-1].host, path[-1].vlan)
        else:
            swpvlan = get_vlan_downlink_to_host(path[-1].host)

        if swpvlan:
            path.append(PathNode(swpvlan.vlan, swpvlan.interface,
                                 swpvlan.interface.netbox, None))
        else:
            path.append(PATH_NOT_FOUND)
            break
    return path


def get_start_path(addr):
    source = get_host_or_netbox_from_addr(addr)
    target_vlan = get_vlan_from_ip(source.ip)
    node = PathNode(target_vlan, None, source, None)
    return node


def get_host_or_netbox_from_addr(addr):
    host = Host(addr)
    netbox = get_netbox_from_host(host)
    if netbox:
        return netbox
    else:
        return host


def is_netbox_gateway(netbox):
    return netbox.category_id in ('GW', 'GSW')


def are_hosts_on_same_vlan(host1, host2):
    vlan1 = get_vlan_from_host(Host(host1))
    vlan2 = get_vlan_from_host(Host(host2))
    return vlan1 == vlan2


def get_netbox_from_host(host):
    if host.is_ip():
        query = Q(sysname=host.ip) | Q(ip=host.ip)
    else:
        query = Q(sysname__startswith=host.hostname) | Q(ip=host.ip)

    try:
        return Netbox.objects.get(query)
    except Netbox.DoesNotExist:
        pass


def get_vlan_from_host(host):
    return get_vlan_from_ip(host.ip)


def get_vlan_from_ip(ip):
    if not ip:
        return
    matching_prefixes = Prefix.objects.extra(
        select={'mlen': 'masklen(netaddr)'},
        where=["%s << netaddr"],
        params=[ip],
        order_by=["-mlen"]).select_related('vlan')
    if matching_prefixes:
        return matching_prefixes[0].vlan


def get_netbox_vlan(netbox):
    return netbox.get_prefix().vlan


def get_vlan_uplink_from_netbox(netbox, vlan=None):
    if not vlan:
        vlan = get_netbox_vlan(netbox)
    swpvlans = SwPortVlan.objects.filter(
        direction=SwPortVlan.DIRECTION_UP,
        interface__netbox=netbox,
        vlan=vlan,
    ).select_related('interface')
    if swpvlans:
        return swpvlans[0]


def get_vlan_downlink_to_netbox(netbox, vlan=None):
    if not vlan:
        vlan = get_netbox_vlan(netbox)
    swpvlans = SwPortVlan.objects.filter(
        interface__to_netbox=netbox,
        direction=SwPortVlan.DIRECTION_DOWN,
        vlan=vlan,
    ).select_related('interface', 'netbox')
    if swpvlans:
        return swpvlans[0]


def get_vlan_downlink_to_host(host):
    if not host.ip:
        return
    arps = Arp.objects.filter(end_time=INFINITY).extra(
        where=["%s = ip"],
        params=[host.ip]
    ).values('mac')
    macs = [arp['mac'] for arp in arps]
    cams = Cam.objects.filter(
        end_time=INFINITY,
        mac__in=macs)
    if cams:
        cam = cams[0]
        swpvlans = SwPortVlan.objects.filter(
            interface__netbox=cam.netbox,
            interface__ifindex=cam.ifindex
        ).select_related('interface', 'netbox')
        if swpvlans:
            return swpvlans[0]


def get_vlan_gateway(vlan):
    gwport_prefixes = GwPortPrefix.objects.filter(
        prefix__vlan=vlan).order_by('prefix__net_address')
    gateways = Netbox.objects.filter(
        category__in=('GW', 'GSW'),
        interface__gwportprefix__in=gwport_prefixes).distinct()
    if gateways:
        return gateways[0]


class Host(object):
    def __init__(self, host):
        if isinstance(host, Host):
            self.host = host.host
            self.ip = host.ip
            self.hostname = host.hostname
            return
        elif not host:
            raise ValueError("Host argument must be hostname or IP address")

        self.host = host
        if self.is_ip():
            self.ip = host
            self.hostname = self.get_host_by_addr() or host
        else:
            self.hostname = host
            self.ip = self.get_host_by_name() or None

    def is_ip(self):
        return is_valid_ip(self.host, use_socket_lib=True)

    def get_host_by_name(self):
        if self.host is not None:
            try:
                return gethostbyname(self.host)
            except socket.error:
                pass

    def get_host_by_addr(self):
        if self.host is not None:
            try:
                return gethostbyaddr(self.host)[0]
            except socket.error:
                pass

    def __repr__(self):
        return "<%s(%s) = %s>" % (self.__class__.__name__,
                                  repr(self.host),
                                  repr((self.ip, self.hostname)))

    def __eq__(self, other):
        return hasattr(other, 'ip') and self.ip == other.ip


class PathNode(object):
    def __init__(self, vlan, if_in, host, if_out):
        self.vlan = vlan
        self.if_in = if_in
        self.host = host
        self.if_out = if_out

    def __repr__(self):
        return "%s(%r, %r, %r, %r)" % (
            self.__class__.__name__,
            self.vlan,
            self.if_in,
            self.host,
            self.if_out,
        )

    def swap_in_out_interfaces(self):
        (self.if_out, self.if_in) = (self.if_in, self.if_out)


class ResultRow(object):
    def __init__(self, idx, level=2, netboxid=None, ipaddr='', sysname='',
                 if_in=None, if_out=None, vlan=''):
        self.netboxid = netboxid
        self.ipaddr = ipaddr
        self.sysname = sysname
        self.if_in = if_in
        self.if_out = if_out
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

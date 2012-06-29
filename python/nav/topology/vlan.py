#
# Copyright (C) 2011, 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Analysis of VLAN topology as subset of layer 2 topology"""

import logging
import networkx as nx

from nav.models.manage import GwPortPrefix, Interface, SwPortVlan, SwPortBlocked

from django.db.models import Q
from django.db import transaction
from itertools import groupby, chain
from operator import attrgetter
from collections import defaultdict

_LOGGER = logging.getLogger(__name__)
NO_TRUNK = Q(trunk=False) | Q(trunk__isnull=True)

class VlanGraphAnalyzer(object):
    """Analyzes VLAN topologies as a subset of the layer 2 topology"""
    def __init__(self):
        self.vlans = self._build_vlan_router_dict()
        self.layer2 = build_layer2_graph()
        self.stp_blocked = get_stp_blocked_ports()
        _LOGGER.debug("blocked ports: %r", self.stp_blocked)
        self.ifc_vlan_map = {}

    @staticmethod
    def _build_vlan_router_dict():
        addrs = get_active_addresses_of_routed_vlans()
        return dict((addr.prefix.vlan, addr) for addr in addrs)

    def analyze_all(self):
        """Analyze all VLAN topologies"""
        for vlan in self.vlans:
            _LOGGER.debug("Analyzing VLAN %s", vlan)
            self.analyze_vlan(vlan)
        return self.ifc_vlan_map

    def analyze_vlans_by_id(self, vlans):
        """Analyzes a list of VLANs by their PVIDs"""
        vlan_id_map = dict((vlan.vlan, vlan) for vlan in self.vlans.keys())
        for vlan in vlans:
            if vlan in vlan_id_map:
                self.analyze_vlan(vlan_id_map[vlan])

    def analyze_vlan(self, vlan):
        """Analyzes a single vlan"""
        addr = self.vlans[vlan]
        analyzer = RoutedVlanTopologyAnalyzer(addr, self.layer2,
                                              self.stp_blocked)
        topology = analyzer.analyze()
        self._integrate_vlan_topology(vlan, topology)

    def _integrate_vlan_topology(self, vlan, topology):
        for ifc, direction in topology.items():
            if ifc not in self.ifc_vlan_map:
                self.ifc_vlan_map[ifc] = {}
            self.ifc_vlan_map[ifc][vlan] = direction

    def add_access_port_vlans(self):
        """Detects and adds Vlan entries for access ports to the ifc_vlan_map"""
        access_vlan_map = dict(self.find_access_port_vlans())
        self.ifc_vlan_map.update(access_vlan_map)
        return self.ifc_vlan_map

    def find_access_port_vlans(self):
        """Finds and yields the vlans of access ports.

        After the analyze_all step, the ifc_vlan_map will normally only
        contain vlans for uplink/downlink ports, not access ports.  This
        method will find the actual vlan objects of each of the switch access
        ports and yield those as tuples: (interface, {vlan: 'down'}).  These
        can be made into a dictionary suitable for updating ifc_vlan_map.

        """
        groups = groupby(self.ifc_vlan_map, lambda ifc: ifc.netbox)
        for netbox, ifcs in groups:
            for result in self._find_netbox_access_vlans(netbox, list(ifcs)):
                yield result

    def _find_netbox_access_vlans(self, netbox, ifcs):
        vlans = chain(*(self.ifc_vlan_map[ifc].keys() for ifc in ifcs))
        active_vlans = dict((vlan.vlan, vlan) for vlan in vlans)

        access_ifcs = netbox.interface_set.filter(
            vlan__isnull=False).filter(NO_TRUNK).exclude(
            id__in=(ifc.id for ifc in ifcs))
        for ifc in access_ifcs:
            if ifc.vlan in active_vlans:
                yield ifc, {active_vlans[ifc.vlan]: 'down'}

class RoutedVlanTopologyAnalyzer(object):
    """Analyzer of a single routed VLAN topology"""

    def __init__(self, address, layer2_graph, stp_blocked=None):
        """Initializes an analyzer for a given routed VLAN.

        :param address: A GwPortPrefix representing the router address of this
                        VLAN.
        :param layer2_graph: A layer 2 graph, as produced by the
                             build_layer2_graph() function.

        """
        self.address = address
        self.layer2 = layer2_graph

        self.vlan = address.prefix.vlan
        self.router_port = address.interface
        self.router = self.router_port.netbox

        self.stp_blocked = stp_blocked or {}
        self.ifc_directions = {}

    def analyze(self):
        """Runs the analysis on the associdated VLAN"""
        if self.router in self.layer2:
            if not self.router_port.to_netbox:
                # likely a GSW, descend on its switch ports by faking an edge
                start_edge = (self.router, self.router, None)
            else:
                start_edge = (self.router, self.router_port.to_netbox,
                              self.router_port)
            self._examine_edge(start_edge)

        return self.ifc_directions

    def _examine_edge(self, edge, visited_nodes=None):
        _source, dest, ifc = edge

        visited_nodes = visited_nodes or set()
        direction = 'up' if dest in visited_nodes else 'down'
        visited_nodes.add(dest)

        vlan_is_active = (
            (direction == 'up'
             and self._vlan_is_active_on_reverse_edge(edge, visited_nodes))
            or self._is_vlan_active_on_destination(dest, ifc))

        if direction == 'down':
            # Recursive depth first search on each outgoing edge
            for next_edge in self._out_edges_on_vlan(dest):
                if not self._is_blocked_on_any_end(next_edge):
                    self._log_descent(next_edge)
                    sub_active = self._examine_edge(next_edge, visited_nodes)
                    vlan_is_active = vlan_is_active or sub_active
                else:
                    vlan_is_active = False
                    self._mark_both_ends_as_blocked(next_edge)
                    self._log_block(next_edge)

        if vlan_is_active and ifc:
            self.ifc_directions[ifc] = direction

        return vlan_is_active

    def _vlan_is_active_on_reverse_edge(self, edge, visited_nodes):
        _source, dest, ifc = edge
        reverse_edge = self._find_reverse_edge(edge)
        if reverse_edge:
            reverse_ifc = reverse_edge[2]
            been_there = (self._interface_has_been_seen_before(reverse_ifc)
                          or dest in visited_nodes)
            if been_there:
                return self._ifc_has_vlan(ifc)
        return False

    def _find_reverse_edge(self, edge):
        source, dest, ifc = edge
        dest_ifc = ifc.to_interface

        if source in self.layer2[dest]:
            if dest_ifc and dest_ifc in self.layer2[dest][source]:
                return (dest, source, dest_ifc)
            else:
                # pick first available return edge when any exist
                return (dest, source, self.layer2[dest][source].keys()[0])

    def _interface_has_been_seen_before(self, ifc):
        return ifc in self.ifc_directions

    def _is_vlan_active_on_destination(self, dest, ifc):
        if not ifc:
            return False

        if not ifc.trunk:
            return self._ifc_has_vlan(ifc)
        else:
            non_trunks_on_vlan = dest.interface_set.filter(
                vlan=self.vlan.vlan).filter(NO_TRUNK)
            if ifc.to_interface:
                non_trunks_on_vlan = non_trunks_on_vlan.exclude(
                    id=ifc.to_interface.id)

            return non_trunks_on_vlan.count() > 0

    def _out_edges_on_vlan(self, node):
        return (
            (u, v, w)
            for u, v, w in self.layer2.out_edges_iter(node, keys=True)
            if self._ifc_has_vlan(w))

    def _ifc_has_vlan(self, ifc):
        return ifc.vlan == self.vlan.vlan or self._vlan_allowed_on_trunk(ifc)

    def _vlan_allowed_on_trunk(self, ifc):
        return (ifc.trunk and
                hasattr(ifc, 'swportallowedvlan') and ifc.swportallowedvlan and
                self.vlan.vlan in ifc.swportallowedvlan)

    def _is_blocked_on_any_end(self, edge):
        """Returns True if at least one of the edge endpoints are blocked"""
        reverse_edge = self._find_reverse_edge(edge)
        if not reverse_edge:
            _LOGGER.debug("could not find reverse edge for %r", edge)
        return (self._is_edge_blocked(edge) or
                self._is_edge_blocked(reverse_edge))

    def _is_edge_blocked(self, edge):
        if edge:
            _source, _dest, ifc = edge
            return self.vlan.vlan in self.stp_blocked.get(ifc.id, [])
        return False

    def _log_descent(self, next_edge):
        source, dest, ifc = next_edge
        _LOGGER.debug("(%s) descending from %s (%s [%d]) to %s",
                      self.vlan.vlan,
                      source.sysname, ifc.ifname, ifc.id,
                      dest.sysname)

    def _log_block(self, next_edge):
        source, _dest, source_ifc = next_edge
        reverse_edge = self._find_reverse_edge(next_edge)
        if reverse_edge:
            dest, _source, dest_ifc = reverse_edge
            _LOGGER.info("at least one of %s (%s) <-> %s (%s) is blocked "
                         "on VLAN %s",
                         source.sysname, source_ifc.ifname,
                         dest.sysname, dest_ifc.ifname,
                         self.vlan.vlan)
        else:
            _LOGGER.info("%s (%s) is blocked on VLAN %s",
                         source.sysname, source_ifc.ifname, self.vlan.vlan)

    def _mark_both_ends_as_blocked(self, edge):
        _source, _dest, source_ifc = edge
        self.ifc_directions[source_ifc] = 'blocked'
        reverse_edge = self._find_reverse_edge(edge)
        if reverse_edge:
            _dest, _source, dest_ifc = reverse_edge
            self.ifc_directions[dest_ifc] = 'blocked'



class VlanTopologyUpdater(object):
    """Updater of the VLAN topology.

    Usage example:

      >>> a = VlanGraphAnalyzer()
      >>> ifc_vlan_map = a.analyze_all()
      >>> updater = VlanTopologyUpdater(ifc_vlan_map)
      >>> updater()
      >>>

    """
    def __init__(self, ifc_vlan_map):
        """Initializes a vlan topology updater.

        :param ifc_vlan_map: A dictionary mapping interfaces to Vlans and
                             directions; just as returned by a call to
                             VlanGraphAnalyzer.analyze_all().

        """
        self.ifc_vlan_map = ifc_vlan_map

    def __call__(self):
        return self.update()

    @transaction.commit_on_success
    def update(self):
        """Updates the VLAN topology in the NAV database"""
        for ifc, vlans in self.ifc_vlan_map.items():
            for vlan, dirstr in vlans.items():
                self._update_or_create_new_swportvlan_entry(ifc, vlan, dirstr)
            self._remove_dead_swpvlan_records_for_ifc(ifc)

        self._delete_swportvlans_from_untouched_ifcs()

    @classmethod
    def _update_or_create_new_swportvlan_entry(cls, ifc, vlan, dirstr):
        direction = cls._direction_from_string(dirstr)
        obj, created = SwPortVlan.objects.get_or_create(
            interface=ifc, vlan=vlan,
            defaults={'direction': direction})
        if not created and obj.direction != direction:
            obj.direction = direction
            obj.save()
        return object


    DIRECTION_MAP = {
        'up': SwPortVlan.DIRECTION_UP,
        'down': SwPortVlan.DIRECTION_DOWN,
        'blocked': SwPortVlan.DIRECTION_BLOCKED,
    }

    @classmethod
    def _direction_from_string(cls, string):
        return (cls.DIRECTION_MAP[string]
                if string in cls.DIRECTION_MAP
                else SwPortVlan.DIRECTION_UNDEFINED)

    def _remove_dead_swpvlan_records_for_ifc(self, ifc):
        records_for_ifc = SwPortVlan.objects.filter(interface=ifc)
        active_vlans = self.ifc_vlan_map[ifc].keys()
        dead = records_for_ifc.exclude(vlan__in=active_vlans)
        dead.delete()

    def _delete_swportvlans_from_untouched_ifcs(self):
        touched = self.ifc_vlan_map.keys()
        SwPortVlan.objects.exclude(interface__in=touched).delete()


def build_layer2_graph(related_extra=None):
    """Builds a graph representation of the layer 2 topology stored in the NAV
    database.

    :param related_extra Additional selection_related fields

    :returns: A MultiDiGraph of Netbox nodes, edges annotated with Interface
              model objects.

    """
    graph = nx.MultiDiGraph(name="Layer 2 topology")

    select_related = ('netbox', 'to_netbox', 'to_interface')
    if related_extra:
        select_related = select_related+related_extra

    links = Interface.objects.filter(to_netbox__isnull=False).select_related(*select_related)

    for i in xrange(0, len(links)):
        dest = links[i].to_interface.netbox if links[i].to_interface else links[i].to_netbox
        graph.add_edge(links[i].netbox, dest, key=links[i])

    return graph

def get_active_addresses_of_routed_vlans():
    """Gets a single router port address for each routed VLAN.

    :returns: A list of GwPortPrefix objects.

    """
    addrs = get_routed_vlan_addresses().select_related(
        'prefix__vlan', 'interface__netbox')
    return filter_active_router_addresses(addrs)

def filter_active_router_addresses(gwportprefixes):
    """Filters a GwPortPrefix queryset, leaving only active router addresses.

    For any given prefix, if multiple router addresses exist, the lowest IP
    address will be picked.  If the prefix has an HSRP address, it will be
    picked instead.

    :param gwportprefixes: A GwPortPrefix QuerySet.
    :returns: A list of GwPortPrefix objects.

    """
    # It is more or less impossible to get Django's ORM to generate the
    # wonderfully complex SQL needed for this, so we do it by hand.
    raddrs = gwportprefixes.order_by('prefix__id', '-hsrp', 'gw_ip')
    grouper = groupby(raddrs, attrgetter('prefix_id'))
    return [group.next() for _key, group in grouper]

def get_routed_vlan_addresses():
    """Gets router port addresses for all routed VLANs.

    :returns: A GwPortPrefix QuerySet.

    """
    raddrs = get_router_addresses()
    return raddrs.filter(
        prefix__vlan__vlan__isnull=False)

def get_router_addresses():
    """Gets all router port addresses.

    :returns: A GwPortPrefix QuerySet.

    """
    return GwPortPrefix.objects.filter(
        interface__netbox__category__id__in=('GW', 'GSW'))

def get_stp_blocked_ports():
    """Returns a dictionary of ports in STP blocking mode.

    :returns: A dictionary: {interfaceid: [vlan1, vlan2, ...]}

    """
    blocked = defaultdict(list)
    for block in SwPortBlocked.objects.all():
        blocked[block.interface_id].append(block.vlan)
    return dict(blocked)

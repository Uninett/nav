#
# Copyright (C) 2011 UNINETT AS
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

import networkx as nx

from nav.models.manage import GwPortPrefix, Interface

from django.db.models import Q
from itertools import groupby
from operator import attrgetter

NO_TRUNK = Q(trunk=False) | Q(trunk__isnull=True)

class VlanGraphAnalyzer(object):
    def __init__(self):
        self.vlans = self._build_vlan_router_dict()
        self.layer2 = build_layer2_graph()
        self.ifc_vlan_map = {}

    @staticmethod
    def _build_vlan_router_dict():
        addrs = get_active_addresses_of_routed_vlans()
        return dict((addr.prefix.vlan, addr) for addr in addrs)

    def analyze_all(self):
        """Analyze all VLAN topologies"""
        for vlan in self.vlans:
            self.analyze_vlan(vlan)
        return self.ifc_vlan_map

    def analyze_vlan(self, vlan):
        addr = self.vlans[vlan]
        analyzer = RoutedVlanTopologyAnalyzer(addr, self.layer2)
        topology = analyzer.analyze()
        self._integrate_vlan_topology(vlan, topology)

    def _integrate_vlan_topology(self, vlan, topology):
        for ifc, direction in topology.items():
            if ifc not in self.ifc_vlan_map:
                self.ifc_vlan_map[ifc] = {}
            self.ifc_vlan_map[ifc][vlan] = direction


class RoutedVlanTopologyAnalyzer(object):
    """Analyzer of a single routed VLAN topology.

    Takes a VLAN's root router address (a GwPortPrefix object) and a layer 2
    topology graph as input.

    """
    def __init__(self, address, layer2_graph):
        self.address = address
        self.layer2 = layer2_graph

        self.vlan = address.prefix.vlan
        self.router_port = address.interface
        self.router = self.router_port.netbox

        self.ifc_directions = {}

    def analyze(self):
        if self.router in self.layer2:
            if not self.router_port.to_netbox:
                # likely a GSW, descend on its switch ports by faking an edge
                start_edge = (self.router, self.router, None)
            else:
                start_edge = (self.router, self.router_port.to_netbox,
                              self.router_port)
            self.check_vlan(start_edge)

        return self.ifc_directions

    def check_vlan(self, edge, visited_nodes=None):
        source, dest, ifc = edge

        visited_nodes = visited_nodes or set()
        direction = 'up' if dest in visited_nodes else 'down'
        visited_nodes.add(dest)

        # Decide first on the immediate merits of the edge and the
        # destination netbox
        vlan_is_active = self.is_vlan_active_on_destination(dest, ifc)

        # Recursive depth first search on each outgoing edge
        if direction == 'down':
            for next_edge in self.out_edges_on_vlan(dest):
                sub_active = self.check_vlan(next_edge, visited_nodes)
                vlan_is_active = vlan_is_active or sub_active

        if vlan_is_active and ifc:
            self.ifc_directions[ifc] = direction

        return vlan_is_active

    def is_vlan_active_on_destination(self, dest, ifc):
        if not ifc:
            return False

        if not ifc.trunk:
            return self.ifc_has_vlan(ifc)
        else:
            non_trunks_on_vlan = dest.interface_set.filter(
                vlan=self.vlan.vlan).filter(NO_TRUNK)
            if ifc.to_interface:
                non_trunks_on_vlan = non_trunks_on_vlan.exclude(
                    id=ifc.to_interface.id)

            return non_trunks_on_vlan.count() > 0

    def out_edges_on_vlan(self, node):
        return (
            (u, v, w)
            for u, v, w in self.layer2.out_edges_iter(node, keys=True)
            if self.ifc_has_vlan(w))

    def ifc_has_vlan(self, ifc):
        return ifc.vlan == self.vlan.vlan or self.vlan_allowed_on_trunk(ifc)

    def vlan_allowed_on_trunk(self, ifc):
        return (ifc.trunk and
                ifc.swportallowedvlan and
                self.vlan.vlan in ifc.swportallowedvlan)


def build_layer2_graph():
    """Builds a graph representation of the layer 2 topology stored in the NAV
    database.

    :returns: A MultiDiGraph of Netbox nodes, edges annotated with Interface
              model objects.

    """
    graph = nx.MultiDiGraph(name="Layer 2 topology")
    links = Interface.objects.filter(
        to_netbox__isnull=False).select_related(
        'netbox', 'to_netbox', 'to_interface')

    for link in links:
        dest = link.to_interface.netbox if link.to_interface else link.to_netbox
        graph.add_edge(link.netbox, dest, key=link)

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
    return [group.next() for key, group in grouper]

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


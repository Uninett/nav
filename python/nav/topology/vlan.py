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

    def analyze_vlan(self, vlan):
        address = self.vlans[vlan]
        router_port = address.interface
        router = router_port.netbox

        def vlan_allowed_on_trunk(ifc):
            return (ifc.trunk and
                    ifc.swportallowedvlan and
                    vlan.vlan in ifc.swportallowedvlan)

        def ifc_has_vlan(ifc):
            return ifc.vlan == vlan.vlan or vlan_allowed_on_trunk(ifc)

        def check_vlan(edge, visited_nodes=None):
            source, dest, ifc = edge
            visited_nodes = visited_nodes or set()
            if dest in visited_nodes:
                direction = 'up'
            else:
                direction = 'down'
                visited_nodes.add(dest)

            vlan_is_active_on_edge = False

            # Decide first on the immediate merits of the edge and the
            # destination netbox
            if ifc:
                if not ifc.trunk:
                    vlan_is_active_on_edge = ifc_has_vlan(ifc)
                else:
                    non_trunks_on_vlan = dest.interface_set.filter(
                        vlan=vlan.vlan).filter(NO_TRUNK)
                    if ifc.to_interface:
                        non_trunks_on_vlan = non_trunks_on_vlan.exclude(
                            id=ifc.to_interface.id)

                    vlan_is_active_on_edge = non_trunks_on_vlan.count() > 0

            # Recursive depth first search on each outgoing edge
            if direction == 'down':
                edges_on_vlan = (
                    (u, v, w)
                    for u, v, w in self.layer2.out_edges_iter(dest, keys=True)
                    if ifc_has_vlan(w))
                for next_edge in edges_on_vlan:
                    active = check_vlan(next_edge, visited_nodes)
                    vlan_is_active_on_edge = vlan_is_active_on_edge or active

            if vlan_is_active_on_edge:
                if ifc:
                    if ifc not in self.ifc_vlan_map:
                        self.ifc_vlan_map[ifc] = {}
                    self.ifc_vlan_map[ifc][vlan] = direction
            return vlan_is_active_on_edge

        if router in self.layer2:
            if not router_port.to_netbox:
                # likely a GSW, descend on its switch ports
                check_vlan((router, router, None))
            else:
                check_vlan((router, router_port.to_netbox, router_port))

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


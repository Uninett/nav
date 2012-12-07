#
# Copyright (C) 2012 UNINETT
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
"""Topology evaluation functions for event processing"""

import networkx
from nav.models.manage import SwPortVlan

import logging
_logger = logging.getLogger(__name__)

def is_netbox_reachable(netbox):
    """Returns True if netbox appears to be reachable through the known
    topology.

    """
    prefix = netbox.get_prefix()
    router_port = prefix.get_router_ports()[0]
    router = router_port.interface.netbox
    graph = get_graph_for_vlan(prefix.vlan)
    _logger.debug("reachability check for %s on %s (router: %s)",
                  netbox, prefix, router)

    if netbox not in graph or router not in graph:
        _logger.debug("%s not reachable, router or box not in graph: %r",
                      netbox, graph.edges())
        return False

    path = networkx.shortest_path(graph, netbox, router)
    _logger.debug("path to %s: %r", netbox, path)
    return path

def get_graph_for_vlan(vlan):
    """Builds a simple topology graph of the active netboxes in vlan.

    Any netbox that seems to be down at the moment will not be included in
    the graph.

    :returns: A networkx.Graph object.

    """
    swpvlan = SwPortVlan.objects.filter(vlan=vlan).select_related(
        'interface', 'interface__netbox',  'interface__to_netbox')
    graph = networkx.Graph(name='graph for vlan %s' % vlan)
    for swp in swpvlan:
       source = swp.interface.netbox
       target = swp.interface.to_netbox
       if target and all(x.up==x.UP_UP for x in (source, target)):
           graph.add_edge(source,target)
    return graph

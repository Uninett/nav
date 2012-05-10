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
from nav.topology import vlan

def layer2_graph():
    layer2_graph = vlan.build_layer2_graph()

    netboxes = layer2_graph.nodes()

    connections = []

    for node, neighbours_dict in layer2_graph.adjacency_iter():
        for neighbour, keydict in neighbours_dict.items():
            for key, eattr in keydict.items():
                connections.append([node, neighbour, key]) # [from_netbox, to_netbox, to_interface]

    return (netboxes, connections)
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
from nav.models.manage import Netbox
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

def node_to_json(node):
    """Filter our metadata for a node in JSON-format

    Used for showing metadata in NetMap with D3

    :param node A Netbox model
    :returns: metadata for a node
    """

    last_updated = node.last_updated()
    if last_updated:
        last_updated = last_updated.strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_updated = 'not available'

    return {
        'sysname': str(node.sysname),
        'ip': node.ip,
        'category': str(node.category_id),
        'type': str(node.type),
        'room': str(node.room),
        'up': str(node.up),
        'up_image': get_status_image_link(node.up),
        'ipdevinfo_link': node.get_absolute_url(),
        'last_updated': last_updated,
    }

STATUS_IMAGE_MAP = {
    Netbox.UP_DOWN: 'red.png',
    Netbox.UP_UP: 'green.png',
    Netbox.UP_SHADOW: 'yellow.png',
}


def edge_fetch_uplink(netbox_from, netbox_to):
    def uplinks(uplinks, uplink_node):
        interface_link = None
        if uplinks:
            for uplink in uplinks:
                if uplink['other']:
                    if uplink['other'].netbox == uplink_node:
                        interface_link = {'other': 'N/A', 'thiss': 'N/A'}
                        interface_link['other'] = str(uplink['other'].ifname) + ' at ' + str(uplink['other'].netbox.sysname)
                        if uplink['this']:
                            interface_link['thiss'] = str(uplink['this'].ifname) + ' at ' + str(uplink['this'].netbox.sysname)
                        break
        return interface_link

    interface_link = uplinks(netbox_from.get_uplinks_regarding_of_vlan(), netbox_to)

    if not interface_link:
        # try to fetch uplink from opposite side. (graph is undirected, so might be that the edge is drawn from UPLINK to DOWNLINK.
        interface_link = uplinks(netbox_to.get_uplinks_regarding_of_vlan(), netbox_from)

    return interface_link

def edge_to_json(netbox_from, netbox_to):
    # fetch uplinks
    interface_link = edge_fetch_uplink(netbox_from, netbox_to)






    # jsonify null's.
    if not interface_link:
        interface_link = 'null' # found no uplinks, json null.

    return {
        'uplink': interface_link,
    }


def get_status_image_link(status):
    try:
        return STATUS_IMAGE_MAP[status]
    except:
        return STATUS_IMAGE_MAP[Netbox.UP_DOWN]

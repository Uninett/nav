from nav.netmap.metadata import (
    node_to_json_layer2,
    edge_to_json_layer2,
    node_to_json_layer3,
    edge_to_json_layer3,
    vlan_to_json,
    get_vlan_lookup_json,
)
from nav.netmap.topology import (
    build_netmap_layer3_graph,
    build_netmap_layer2_graph,
    _get_vlans_map_layer2,
    _get_vlans_map_layer3,
)
from nav.topology import vlan


def get_topology_graph(layer=2, load_traffic=False, view=None):

    if layer == 2:
        return _json_layer2(load_traffic, view)
    else:
        return _json_layer3(load_traffic, view)


def _json_layer2(load_traffic=False, view=None):

    topology_without_metadata = vlan.build_layer2_graph(
        (
        'to_interface__netbox', 'to_interface__netbox__room', 'to_netbox__room',
        'netbox__room', 'to_interface__netbox__room__location',
        'to_netbox__room__location', 'netbox__room__location'))

    vlan_by_interface, vlan_by_netbox = _get_vlans_map_layer2(
        topology_without_metadata)

    graph = build_netmap_layer2_graph(topology_without_metadata,
                                      vlan_by_interface, vlan_by_netbox,
                                      load_traffic, view)

    return {
        'vlans': get_vlan_lookup_json(vlan_by_interface),
        'nodes': _get_nodes(node_to_json_layer2, graph),
        'links': [edge_to_json_layer2((node_a, node_b), nx_metadata) for
                  node_a, node_b, nx_metadata in graph.edges_iter(data=True)]
    }


def _json_layer3(load_traffic=False, view=None):

    topology_without_metadata = vlan.build_layer3_graph(
        ('prefix__vlan__net_type', 'gwportprefix__prefix__vlan__net_type',))

    vlans_map = _get_vlans_map_layer3(topology_without_metadata)

    graph = build_netmap_layer3_graph(topology_without_metadata, load_traffic,
                                      view)
    return {
        'vlans': [vlan_to_json(prefix.vlan) for prefix in vlans_map],
        'nodes': _get_nodes(node_to_json_layer3, graph),
        'links': [edge_to_json_layer3((node_a, node_b), nx_metadata) for
                  node_a, node_b, nx_metadata in graph.edges_iter(data=True)]
    }


def _get_nodes(node_to_json_function, graph):
    nodes = {}
    for node, nx_metadata in graph.nodes_iter(data=True):
        nodes.update(node_to_json_function(node, nx_metadata))
    return nodes
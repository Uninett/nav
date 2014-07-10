"""Graph utility functions for Netmap"""

from collections import defaultdict

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
from nav.models.manage import Interface, Prefix, GwPortPrefix
from nav.netmap.traffic import get_traffic_data

from .common import get_traffic_rgb


def get_topology_graph(layer=2, load_traffic=False, view=None):

    if layer == 2:
        return _json_layer2(load_traffic, view)
    else:
        return _json_layer3(load_traffic, view)


def _json_layer2(load_traffic=False, view=None):

    topology_without_metadata = vlan.build_layer2_graph(
        (
            'to_interface__netbox',
            'to_interface__netbox__room',
            'to_netbox__room',
            'netbox__room', 'to_interface__netbox__room__location',
            'to_netbox__room__location',
            'netbox__room__location',
        )
    )

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
        ('prefix__vlan__net_type', 'gwportprefix__prefix__vlan__net_type',)
    )

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


def get_traffic_gradient():

    keys = ('r', 'g', 'b')

    return [
        dict(zip(keys, get_traffic_rgb(percent))) for percent in range(0, 101)
    ]


def get_layer2_traffic():

    interfaces = Interface.objects.filter(
        to_netbox__isnull=False
    ).select_related('netbox', 'to_netbox', 'to_interface__netbox')

    edges = set([
        (
            interface.netbox_id,
            interface.to_netbox_id
        )
        for interface in interfaces
    ])

    traffic = []
    for source, target in edges:
        edge_interfaces = interfaces.filter(
            netbox_id=source,
            to_netbox_id=target
        )
        edge_traffic = []
        for interface in edge_interfaces:
            to_interface = interface.to_interface
            d = get_traffic_data((interface, to_interface)).to_json()
            d.update({
                'source_ifname': interface.ifname if interface else '',
                'target_ifname': to_interface.ifname if to_interface else ''
            })
            edge_traffic.append(d)
        traffic.append({
            'source': source,
            'target': target,
            'edges': edge_traffic,
        })

    return traffic


def get_layer3_traffic():

    prefixes = Prefix.objects.filter(
        vlan__net_type__in=('link', 'elink', 'core')
    ).select_related('vlan__net_type')

    router_ports = GwPortPrefix.objects.filter(
        prefix__in=prefixes,
        interface__netbox__category__in=('GW', 'GSW'),  # Or might be faster
    ).select_related(
        'interface',
        'interface__to_interface',
    )

    router_ports_prefix_map = defaultdict(list)
    for router_port in router_ports:
        router_ports_prefix_map[router_port.prefix].append(router_port)

    interfaces = set()
    traffic = []

    for prefix in prefixes:

        gwport_prefixes = router_ports_prefix_map[prefix]

        if gwport_prefixes and prefix.vlan.net_type.id is not 'elink':

            for gwport_prefix_a in gwport_prefixes:
                for gwport_prefix_b in gwport_prefixes:
                    if gwport_prefix_a is not gwport_prefix_b:
                        interface_a = gwport_prefix_a.interface
                        interface_b = gwport_prefix_b.interface
                        interfaces.add(
                            (
                                interface_a.netbox_id,
                                interface_b.netbox_id,
                                interface_a,
                                interface_b
                            )
                        )
    for source, target, interface, to_interface in interfaces:
        traffic.append({
            'source': source,
            'target': target,
            'source_ifname': interface.ifname,
            'target_ifname': to_interface.ifname,
            'traffic_data': get_traffic_data(
                (interface, to_interface,)
            ).to_json()
        })

    return traffic

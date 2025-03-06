#
# Copyright (C) 2012-2015 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Handles attaching and converting metadata in a netmap networkx toplogy
graph"""

from collections import defaultdict
from django.urls import reverse, NoReverseMatch

from IPy import IP
from nav.netmap.config import NETMAP_CONFIG
from nav.errors import GeneralException
from nav.models.manage import GwPortPrefix, Interface
from nav.netmap import stubs
from nav.web.netmap.common import get_status_image_link


class NetmapException(GeneralException):
    """Generic Netmap Exception"""

    pass


class GraphException(NetmapException):
    """Graph Exception

    This exception is normally thrown if it finds something odd in the graph
     from nav.topology or the metadata contains known errors.
    """

    pass


class Node(object):
    """Node object represent a node in the netmap_graph

    Makes it easier to validate data and convert node to valid json.
    """

    def __init__(self, node, nx_node_metadata=None):
        self.node = node
        if nx_node_metadata and 'metadata' in nx_node_metadata:
            self.metadata = nx_node_metadata['metadata']
        else:
            self.metadata = None

    def __repr__(self):
        return "netmap.Node(metadata={0!r})".format(self.metadata)

    def to_json(self):
        """json presentation of Node"""
        json = {}

        if self.metadata:
            if 'position' in self.metadata:
                json.update(
                    {
                        'position': {
                            'x': self.metadata['position'].x,
                            'y': self.metadata['position'].y,
                        }
                    }
                )
            if 'vlans' in self.metadata:  # Layer2 metadata
                json.update(
                    {
                        'vlans': [
                            nav_vlan_id for nav_vlan_id, _ in self.metadata['vlans']
                        ]
                    }
                )
                if NETMAP_CONFIG.getboolean('API_DEBUG'):
                    json.update(
                        {
                            'd_vlans': [
                                vlan_to_json(swpv.vlan)
                                for _, swpv in self.metadata['vlans']
                            ]
                        }
                    )

        if isinstance(self.node, stubs.Netbox):
            json.update(
                {
                    'id': str(self.node.id),
                    'sysname': self.node.sysname,
                    'category': str(self.node.category_id),
                    'is_elink_node': True,
                }
            )
        else:
            try:
                location = self.node.room.location
                locationid = location.id
                location_descr = location.description
            except AttributeError:
                locationid = ''
                location_descr = ''
            json.update(
                {
                    'id': str(self.node.id),
                    'sysname': str(self.node.sysname),
                    'category': str(self.node.category_id),
                    'ip': self.node.ip,
                    'ipdevinfo_link': reverse(
                        'ipdevinfo-details-by-name', args=[self.node.sysname]
                    ),
                    'up': str(self.node.up),
                    'up_image': get_status_image_link(self.node.up),
                    'roomid': self.node.room.id,
                    'locationid': str(locationid),
                    'location': str(location_descr),
                    'room': str(self.node.room),
                    'is_elink_node': False,
                }
            )
        return {str(self.node.id): json}


class Group(object):
    """Grouping object for representing a Netbox and Interface in a Edge"""

    def __init__(self, netbox=None, interface=None):
        self.netbox = netbox
        self.interface = interface
        self.gw_ip = None
        self.virtual = None
        self.vlans = None

    def __repr__(self):
        return (
            "netmap.Group(netbox={0!r}, interface={1!r}, gw_ip={2!r}"
            ", virtual={3!r}, vlans={4!r})"
        ).format(self.netbox, self.interface, self.gw_ip, self.virtual, self.vlans)

    def __hash__(self):
        return hash(self.netbox) + hash(self.interface)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return self.netbox == other.netbox and self.interface == other.interface

    def to_json(self):
        """json presentation of Group"""
        json = {
            'netbox': str(self.netbox.id),
        }
        if self.interface is not None:
            ipdevinfo_link = None
            if (
                self.netbox.sysname
                and self.interface.ifname
                and self.interface.ifname != '?'
            ):
                kwargs = dict(
                    netbox_sysname=str(self.netbox.sysname),
                    port_name=str(self.interface.ifname),
                )
                try:
                    ipdevinfo_link = reverse(
                        'ipdevinfo-interface-details-by-name', kwargs=kwargs
                    )
                except NoReverseMatch:
                    ipdevinfo_link = None

            json['interface'] = {
                'ifname': str(self.interface.ifname),
                'ipdevinfo_link': ipdevinfo_link,
            }

        if self.gw_ip is not None:
            json['gw_ip'] = self.gw_ip
        if self.virtual is not None:
            json['virtual'] = self.virtual
        if self.vlans is not None:
            json['vlans'] = [swpv.vlan.id for swpv in self.vlans]
        if NETMAP_CONFIG.getboolean('API_DEBUG'):
            json['d_netbox_sysname'] = str(self.netbox.sysname)
            json['d_vlans'] = [vlan_to_json(swpv.vlan) for swpv in self.vlans]

        return json


class Edge(object):
    """Represent either a edge pair in Layer2 or Layer3"""

    link_speed = None
    vlans = None
    layer = None

    @staticmethod
    def _valid_layer2(edge):
        return isinstance(edge, Interface) or isinstance(edge, stubs.Interface)

    @staticmethod
    def _valid_layer3(edge):
        return isinstance(edge, GwPortPrefix) or isinstance(edge, stubs.GwPortPrefix)

    def _get_layer(self, u, v):
        if (self._valid_layer2(u) or u is None) and (
            self._valid_layer2(v) or v is None
        ):
            return 2

        elif (self._valid_layer3(u) or u is None) and (
            self._valid_layer3(v) or v is None
        ):
            return 3
        else:
            raise NetmapException(
                "Could not determine layer for this edge. This should _not_ happend"
            )

    def _same_layer(self, source, target):
        return (self._valid_layer2(source) and self._valid_layer2(target)) or (
            self._valid_layer3(source) and self._valid_layer3(target)
        )

    def __init__(self, nx_edge, meta_edge, traffic=None):
        """

        :param nx_edge: NetworkX edge representing (u,v) in a tuple
                        (they be nav.models.Netbox or nav.netmap.stubs.Netbox).
        :param meta_edge: An edge tuple representing the edge as a pair of
                          either Interface or GwPortPrefix objects.
        :return:
        """
        meta_u, meta_v = meta_edge
        if meta_u is not None and meta_v is not None:
            if not self._same_layer(meta_u, meta_v):
                raise GraphException(
                    "meta_u and meta_v have to be of same type, typically "
                    "Interfaces in layer2 graph or"
                    "GwPortPrefixes in layer3 graph"
                )
        elif meta_u is None and meta_v is None:
            raise GraphException("meta_u and meta_v can't both be None! Bailing!")

        self.errors = []
        self.u = self.v = self.vlan = self.prefix = None
        nx_u, nx_v = nx_edge

        if self._valid_layer2(meta_u):
            self.u = Group(meta_u.netbox, meta_u)
        elif self._valid_layer3(meta_u):
            self.u = Group(meta_u.interface.netbox, meta_u.interface)
            self.u.gw_ip = meta_u.gw_ip
            self.u.virtual = meta_u.virtual

        if self._valid_layer2(meta_v):
            self.v = Group(meta_v.netbox, meta_v)
        elif self._valid_layer3(meta_v):
            self.v = Group(meta_v.interface.netbox, meta_v.interface)
            self.v.gw_ip = meta_v.gw_ip
            self.v.virtual = meta_v.virtual

        # Basic metadata validation, lets copy over Netbox data which is valid
        # as metadata if metadata building didn't manage to fetch it's data.
        # (this is due to Metadata in L2 is built on Interface<->Interface,
        # both sides is not necessary known in the topology graph when building
        # it)
        # This could also be the case for L3, but since the topology method
        # stubs.Netbox and stubs.Interface, we don't really have the same issue
        # in an L3 graph.
        if self.u is None:
            self.u = Group(nx_u)
        if self.v is None:
            self.v = Group(nx_v)

        self.layer = self._get_layer(meta_u, meta_v)

        if self.layer == 3:
            assert meta_u.prefix.vlan.id == meta_v.prefix.vlan.id, (
                "Source and target GwPortPrefix must reside in same VLan for "
                "Prefix! Bailing"
            )

            self.prefix = meta_u.prefix
            self.vlan = meta_u.prefix.vlan

        self.traffic = traffic

        if (self.u and self.u.interface is not None) and (
            self.v and self.v.interface is not None
        ):
            if self.u.interface.speed == self.v.interface.speed:
                self.link_speed = self.u.interface.speed
            else:
                self.errors.append("Mismatch between interface speed")
                if (self.u.interface.speed or 0) < (self.v.interface.speed or 0):
                    self.link_speed = self.u.interface.speed
                else:
                    self.link_speed = self.v.interface.speed
        elif self.u and self.u.interface is not None:
            self.link_speed = self.u.interface.speed
        elif self.v and self.v.interface is not None:
            self.link_speed = self.v.interface.speed

        self.vlans = []

    def __hash__(self):
        return hash(frozenset((self.u, self.v)))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return frozenset((self.u, self.v)) == frozenset((other.u, other.v))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return (
            "netmap.Edge(layer={0!r}, u={1!r}, v={2!r}, "
            "link_speed={3!r}, vlans={4!r}, vlan={5!r}, "
            "prefix={6!r})"
        ).format(
            self.layer,
            self.u,
            self.v,
            self.link_speed,
            self.vlans,
            self.vlan,
            self.prefix,
        )

    def to_json(self):
        """json presentation of Edge"""
        json = {
            'source': self.u.to_json() or 'null',
            'target': self.v.to_json() or 'null',
        }
        if self.layer == 3:
            json.update(
                {
                    'prefix': {
                        'net_address': str(self.prefix.net_address),
                        'report_link': self.prefix.get_absolute_url(),
                    }
                }
            )
            json.update({'vlan': self.prefix.vlan.id})
        elif self.layer == 2:
            json.update({'vlans': [swpv.vlan.id for swpv in self.vlans]})

        json.update({'link_speed': self.link_speed or 'N/A'})
        json.update({'traffic': self.traffic and self.traffic.to_json() or None})

        return json


def vlan_to_json(vlan):
    return {
        'vlan': vlan.vlan,
        'nav_vlan': vlan.id,
        'net_ident': vlan.net_ident,
        'description': vlan.description,
    }


def get_vlan_lookup_json(vlan_by_interface):
    vlan_lookup = {}
    for list_of_swpv in vlan_by_interface.values():
        for swpv in list_of_swpv:
            vlan_lookup[swpv.vlan.id] = vlan_to_json(swpv.vlan)
    return vlan_lookup


def node_to_json_layer2(node, nx_metadata=None):
    """Convert a node to json, for use in a netmap layer2 graph

    :param node A Netbox model
    :param nx_metadata Metadata from networkx graph.
    :return json presentation of a node.
    """
    return Node(node, nx_metadata).to_json()


def node_to_json_layer3(node, nx_metadata=None):
    """Convert a node to json, for use in a netmap layer3 graph

    :param node A Netbox model
    :param nx_metadata Metadata from networkx graph.
    :return json presentation of a node.
    """
    return Node(node, nx_metadata).to_json()


def edge_to_json_layer2(nx_edge, metadata):
    """Convert a edge between A and B in a netmap layer2 graph to JSON

    :param nx_edge: Metadata from netmap networkx graph
    :returns: edge representation in JSON
    """
    source, target = nx_edge
    edges = metadata['metadata']
    metadata_for_edges = []
    all_vlans = set()
    for edge in edges:
        all_vlans = all_vlans | edge.vlans
        metadata_for_edges.append(edge.to_json())

    json = {
        'source': str(source.id),
        'target': str(target.id),
        'vlans': [swpv.vlan.id for swpv in all_vlans],
        'edges': metadata_for_edges,
    }

    if NETMAP_CONFIG.getboolean('API_DEBUG'):
        json.update(
            {
                'd_source_sysname': str(source.sysname),
                'd_target_sysname': str(target.sysname),
                'd_vlans': [vlan_to_json(swpv.vlan) for swpv in all_vlans],
            }
        )
    return json


def edge_to_json_layer3(nx_edge, nx_metadata):
    """Convert a edge between A and B in a netmap layer 3 graph to JSON

    :param nx_metadata: Metadata from netmap networkx graph
    :type nx_metadata: dict
    :return edge representation in JSON
    """
    source, target = nx_edge

    metadata_collection = defaultdict(list)
    for vlan_id, edges in nx_metadata['metadata'].items():
        for edge in edges:
            metadata_collection[vlan_id].append(edge.to_json())

    def prefixaddress(item):
        addr = item.get('prefix', {}).get('net_address')
        return IP(addr) if addr else addr

    # sorting the output based on prefix address
    for value in metadata_collection.values():
        value.sort(key=prefixaddress)

    json = {
        'source': str(source.id),
        'target': str(target.id),
        'edges': metadata_collection,
    }
    if NETMAP_CONFIG.getboolean('API_DEBUG'):
        json.update(
            {
                'd_source_sysname': str(source.sysname),
                'd_target_sysname': str(target.sysname),
            }
        )
    return json


def edge_metadata_layer3(nx_edge, gwportprefix_u, gwportprefix_v, traffic):
    """

    :param nx_edge: tuple describing the edge between two netboxes
      (nav.models.manage.Netbox or nav.netmap.stubs.Netbox)
    :param gwportprefix_u: nav.models.manage.GwPortPrefix
    :param gwportprefix_v: nav.models.manage.GwPortPrefix
    :param traffic: A Traffic() instance for this edge
    :returns: metadata to attach to netmap graph
    """

    # Note about GwPortPrefix and L3 graph: We always have interface.netbox
    # avaiable under L3 topology graph due to stubbing Netboxes etc for
    # elinks.
    edge = Edge(nx_edge, (gwportprefix_u, gwportprefix_v), traffic)
    return edge


def edge_metadata_layer2(nx_edge, meta_u, meta_v, vlans_by_interface, traffic):
    """
    Adds edge meta data with python types for given edge (layer2)

    :param nx_edge tuple containing source and target
      (nav.models.manage.Netbox or nav.netmap.stubs.Netbox)
    :param meta_u nav.models.manage.Interface (from port_pairs nx metadata)
    :param meta_v nav.models.manage.Interface (from port_pairs nx metadata)
    :param vlans_by_interface VLAN dict access for fetching SwPortVlan list

    :returns metadata to attach to netmap graph as metadata.
    """
    edge = Edge(nx_edge, (meta_u, meta_v), traffic)

    source_vlans = target_vlans = []
    if vlans_by_interface and meta_u in vlans_by_interface:
        source_vlans = tuple(vlans_by_interface.get(meta_u))

    if vlans_by_interface and meta_v in vlans_by_interface:
        target_vlans = tuple(vlans_by_interface.get(meta_v))

    edge.u.vlans = set(source_vlans) - set(target_vlans)
    edge.v.vlans = set(target_vlans) - set(source_vlans)
    edge.vlans = set(source_vlans) | set(target_vlans)
    return edge

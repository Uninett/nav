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
"""Handles attaching and converting metadata in a netmap networkx toplogy
graph"""
from collections import defaultdict
import logging
from django.core.urlresolvers import reverse
import operator
from nav.netmap.config import NETMAP_CONFIG
from nav.errors import GeneralException
from nav.models.manage import GwPortPrefix, Interface
from nav.netmap import stubs
from nav.web.netmap.common import get_status_image_link

_LOGGER = logging.getLogger(__name__)

class NetmapException(GeneralException):
    """Generic Netmap Exception"""
    pass

class GraphException(NetmapException):
    """Graph Exception

    This exception is normally thrown if it finds something odd in the graph
     from nav.topology or the metadata contains known errors.
    """
    pass

# Ignore too few methods in class
# pylint: disable=R0903
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
                json.update({
                    'position': {
                        'x': self.metadata['position'].x,
                        'y': self.metadata['position'].y
                    }})
            if 'vlans' in self.metadata: # Layer2 metadata

                json.update({
                    'vlans': [nav_vlan_id for nav_vlan_id, _ in
                              self.metadata['vlans']]
                })
                if NETMAP_CONFIG.getboolean('API_DEBUG'):
                    json.update({
                        'd_vlans': [vlan_to_json(swpv.vlan) for _, swpv in
                                    self.metadata['vlans']]
                    })


        if isinstance(self.node, stubs.Netbox):
            json.update({
                'id': str(self.node.id),
                'sysname': self.node.sysname,
                'category': str(self.node.category_id),
                'is_elink_node': True
            })
        else:
            json.update({
                    'id': str(self.node.id),
                    'sysname': str(self.node.sysname),
                    'category': str(self.node.category_id),
                    'ip': self.node.ip,
                    'ipdevinfo_link': reverse('ipdevinfo-details-by-name',
                                              args=[self.node.sysname]),
                    'up': str(self.node.up),
                    'up_image': get_status_image_link(self.node.up),
                    'roomid': self.node.room.id,
                    'locationid': unicode(self.node.room.location.id),
                    'location': unicode(self.node.room.location.description),
                    'room': unicode(self.node.room),
                    'is_elink_node': False,
                })
        return {unicode(self.node.id) : json}

# Ignore too few methods in class
# pylint: disable=R0903
class Group(object):
    """Grouping object for representing a Netbox and Interface in a Edge"""

    def __init__(self, netbox=None, interface=None):
        self.netbox = netbox
        self.interface = interface
        self.gw_ip = None
        self.virtual = None
        self.vlans = None

    def __repr__(self):
        return ("netmap.Group(netbox={0!r}, interface={1!r}, gw_ip={2!r}"
                ", virtual={3!r}, vlans={4!r})").format(
            self.netbox, self.interface, self.gw_ip, self.virtual, self.vlans)

    def __hash__(self):
        return hash(self.netbox) + hash(self.interface)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return (self.netbox == other.netbox and
                    self.interface == other.interface)

    def to_json(self):
        """json presentation of Group"""
        json = {
            'netbox': unicode(self.netbox.id),
        }
        if self.interface is not None:
            ipdevinfo_link = None
            if self.interface.ifname and self.interface.ifname != '?':
                ipdevinfo_link = reverse(
                    'ipdevinfo-interface-details-by-name',
                    kwargs={'netbox_sysname': unicode(
                        self.netbox.sysname),
                            'port_name': unicode(
                                self.interface.ifname)})
            json.update({'interface': {
                'ifname': unicode(self.interface.ifname),
                'ipdevinfo_link': ipdevinfo_link
            }})



        if self.gw_ip is not None:
            json.update({'gw_ip': self.gw_ip})
        if self.virtual is not None:
            json.update({'virtual': self.virtual})
        if self.vlans is not None:
            json.update({'vlans': [swpv.vlan.id for swpv in self.vlans]})
        if NETMAP_CONFIG.getboolean('API_DEBUG'):
            json.update({'d_netbox_sysname': unicode(self.netbox.sysname)})
            json.update(
                {'d_vlans': [vlan_to_json(swpv.vlan) for swpv in self.vlans]})

        return json


# Ignore too few methods in class
# pylint: disable=R0903
class Edge(object):
    """Represent either a edge pair in Layer2 or Layer3"""

    def _valid_layer2(self, edge):
        return isinstance(edge, Interface) or isinstance(edge, stubs.Interface)

    def _valid_layer3(self, edge):
        return isinstance(edge, GwPortPrefix) or isinstance(edge,
                                                            stubs.GwPortPrefix)

    def _get_layer(self, source, target):
        if (self._valid_layer2(source) or source is None
            and self._valid_layer2(target) or target is None):
            return 2

        elif (self._valid_layer3(source) or source is None
            and self._valid_layer3(target) or target is None):
            return 3
        else:
            raise NetmapException("Could not determine layer for this edge."
                                  " This should _not_ happend")

    def _same_layer(self, source, target):
        return (self._valid_layer2(source) and self._valid_layer2(target)
            or self._valid_layer3(source) and self._valid_layer3(target)
        )

    def __init__(self, nx_edge, source, target, traffic=None):
        """

        :param nx_edge: NetworkX edge representing (source,target) in a tuple
        .(they be nav.models.Netbox or nav.netmap.stubs.Netbox)
        :param source: source, where it is either of type Interface or type
         GwPortPrefix.
        :param target: target, where it is either of type Interface or type
         GwPortPrefix
        :param vlans: List of SwPortVlan on this particular edge pair
        :return:
        """
        if source is not None and target is not None:
            if not self._same_layer(source, target):
                raise GraphException(
                    "Source and target has to be of same type, typically "
                    "Interfaces in layer2 graph or"
                    "GwPortPrefixes in layer3 graph")
        elif source is None and target is None:
            raise GraphException("Source & target can't both be None! Bailing!")

        self.errors = []
        self.source = self.target = self.vlan = self.prefix = None
        nx_source, nx_target = nx_edge

        if self._valid_layer2(source) :
            self.source = Group(source.netbox, source)
        elif self._valid_layer3(source):
            self.source = Group(source.interface.netbox, source.interface)
            self.source.gw_ip = source.gw_ip
            self.source.virtual = source.virtual


        if self._valid_layer2(target):
            self.target = Group(target.netbox, target)
        elif self._valid_layer3(target):
            self.target = Group(target.interface.netbox, target.interface)
            self.target.gw_ip = target.gw_ip
            self.target.virtual = target.virtual

        # Basic metadata validation, lets copy over Netbox data which is valid
        # as metadata if metadata building didn't manage to fetch it's data.
        # (this is due to Metadata in L2 is built on Interface<->Interface,
        # both sides is not necessary known in the topology graph when building
        # it)
        # This could also be the case for L3, but since the topology method
        # stubs.Netbox and stubs.Interface, we don't really have the same issue
        # in an L3 graph.
        if self.source is None: self.source = Group(nx_source)
        if self.target is None: self.target = Group(nx_target)

        # Swap directional metadata to follow nx graph edge.
        if (self.source.netbox.id != nx_source.id) and (
                self.source.netbox.id == nx_target.id):
            tmp = self.source
            self.source = self.target
            self.target = tmp

        self.layer = self._get_layer(source, target)

        if self.layer == 3:
            assert source.prefix.vlan.id == target.prefix.vlan.id, (
                "Source and target GwPortPrefix must reside in same VLan for "
                "Prefix! Bailing")

            self.prefix = source.prefix
            self.vlan = source.prefix.vlan


        self.traffic = traffic

        if (self.source and self.source.interface is not None) and (
            self.target and self.target.interface is not None):
            if self.source.interface.speed == self.target.interface.speed:
                self.link_speed = self.source.interface.speed
            else:
                self.errors.append("Mismatch between interface speed")
                if self.source.interface.speed < self.target.interface.speed:
                    self.link_speed = self.source.interface.speed
                else:
                    self.link_speed = self.target.interface.speed
        elif self.source and self.source.interface is not None:
            self.link_speed = self.source.interface.speed
        elif self.target and self.target.interface is not None:
            self.link_speed = self.target.interface.speed


        self.vlans = []

    def __hash__(self):
        return hash(self.source) + hash(self.target)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return self.source == other.source and self.target == other.target

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return ("netmap.Edge(layer={0!r}, source={1!r}, target={2!r},"
                "link_speed={3!r}, vlans={4!r}, vlan={5!r},"
                "prefix={6!r})").format(self.layer, self.source, self.target,
                                        self.link_speed, self.vlans, self.vlan,
                                        self.prefix)

    def to_json(self):
        """json presentation of Edge"""
        json = {
            'source': self.source.to_json() or 'null',
            'target': self.target.to_json() or 'null',
        }
        if self.layer == 3:
            json.update({'prefix': {
                'net_address': unicode(self.prefix.net_address),
                'report_link': reverse('report-prefix-prefix',
                                       kwargs={'prefix_id': self.prefix.id})
            }})
            json.update({'vlan': self.prefix.vlan.id})
        elif self.layer == 2:
            json.update({'vlans': [swpv.vlan.id for swpv in self.vlans]})

        json.update({'link_speed': self.link_speed or 'N/A'})
        json.update(
            {'traffic': self.traffic and self.traffic.to_json() or None})

        return json


def vlan_to_json(vlan):
    return {'vlan': vlan.vlan,
            'nav_vlan': vlan.id,
            'net_ident': vlan.net_ident,
            'description': vlan.description
    }

def get_vlan_lookup_json(vlan_by_interface):
    vlan_lookup = {}
    for list_of_swpv in vlan_by_interface.itervalues():
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

    :param edge Metadata from netmap networkx graph
    :return edge representation in JSON
    """
    source, target = nx_edge
    edges = metadata['metadata']
    metadata_for_edges = []
    all_vlans = set()
    for edge in edges:
        all_vlans = all_vlans | edge.vlans
        metadata_for_edges.append(edge.to_json())

    json = {
        'source': unicode(source.id),
        'target': unicode(target.id),
        'vlans' : [swpv.vlan.id for swpv in all_vlans],
        'edges': metadata_for_edges
    }

    if NETMAP_CONFIG.getboolean('API_DEBUG'):
        json.update({
            'd_source_sysname': unicode(source.sysname),
            'd_target_sysname': unicode(target.sysname),
            'd_vlans': [vlan_to_json(swpv.vlan) for swpv in all_vlans]
        })
    return json

def edge_to_json_layer3(nx_edge, nx_metadata):
    """Convert a edge between A and B in a netmap layer 3 graph to JSON

    :param nx_metadata: Metadata from netmap networkx graph
    :type nx_metadata: dict
    :return edge representation in JSON
    """
    source, target = nx_edge


    # todo: fix sorted list keyed on prefix :-))
    metadata_collection = defaultdict(list)
    for vlan_id, edges in nx_metadata['metadata'].iteritems():
        for edge in edges:
            metadata_collection[vlan_id].append(edge.to_json())

    for key, value in metadata_collection.iteritems():
        value = sorted(value, key=operator.itemgetter('prefix'))

    json = {
        'source': unicode(source.id),
        'target': unicode(target.id),
        'edges': metadata_collection
    }
    if NETMAP_CONFIG.getboolean('API_DEBUG'):
        json.update({
            'd_source_sysname': unicode(source.sysname),
            'd_target_sysname': unicode(target.sysname),
        })
    return json



def edge_metadata_layer3(nx_edge, source, target, traffic):
    """

    :param nx_edge tuple containing source and target
      (nav.models.manage.Netbox or nav.netmap.stubs.Netbox)
    :param source nav.models.manage.GwPortPrefix
    :param target nav.models.manage.GwPortPrefix
    :param prefixes list of prefixes (Prefix)
    :returns metadata to attach to netmap graph
    """

    # Note about GwPortPrefix and L3 graph: We always have interface.netbox
    # avaiable under L3 topology graph due to stubbing Netboxes etc for
    # elinks.
    edge = Edge((nx_edge), source, target, traffic)
    return edge


    #return metadata


def edge_metadata_layer2(nx_edge, source, target, vlans_by_interface, traffic):
    """
    Adds edge meta data with python types for given edge (layer2)

    :param nx_edge tuple containing source and target
      (nav.models.manage.Netbox or nav.netmap.stubs.Netbox)
    :param source nav.models.manage.Interface (from port_pairs nx metadata)
    :param target nav.models.manage.Interface (from port_pairs nx metadata)
    :param vlans_by_interface VLAN dict access for fetching SwPortVlan list

    :returns metadata to attach to netmap graph as metadata.
    """
    edge = Edge(nx_edge, source, target, traffic)

    source_vlans = target_vlans = []
    if vlans_by_interface and source in vlans_by_interface:
        source_vlans = tuple(vlans_by_interface.get(source))


    if vlans_by_interface and target in vlans_by_interface:
        target_vlans = tuple(vlans_by_interface.get(target))

#key=lambda x: x.vlan.vlan)
    edge.source.vlans = set(source_vlans) - set(target_vlans)
    edge.target.vlans = set(target_vlans) - set(source_vlans)
    edge.vlans = set(source_vlans) | set(target_vlans)
    return edge


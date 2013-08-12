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
import logging
from django.core.urlresolvers import reverse
from nav.errors import GeneralException
from nav.models.manage import GwPortPrefix, Interface
from nav.netmap import stubs
from nav.web.netmap.common import get_status_image_link


_LOGGER = logging.getLogger(__name__)

class NetmapException(GeneralException):
    pass

class GraphException(NetmapException):
    pass


class Group(object):
    """Grouping object for representing a Netbox and Interface in a networkx
    edge"""

    def __init__(self, netbox=None, interface=None):
        self.netbox = netbox
        self.interface = interface
        self.gw_ip = None
        self.virtual = None

    def __hash__(self):
        return hash(self.netbox) + hash(self.interface)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return (self.netbox == other.netbox and
                    self.interface == other.interface)

    def to_json(self):
        json = {
            'netbox': _node_to_json(self.netbox, None),
        }
        if self.interface is not None:
            json.update({'interface': unicode(self.interface.ifname)})
        if self.gw_ip is not None:
            json.update({'gw_ip': self.gw_ip})
        if self.virtual is not None:
            json.update({'virtual': self.virtual})
        return json



class Edge(object):
    """Represent either a edge pair in Layer2 or Layer3"""

    def _valid_layer2(self, edge):
        return isinstance(edge, Interface) or isinstance(edge, stubs.Interface)

    def _valid_layer3(self, edge):
        return isinstance(edge, GwPortPrefix) or isinstance(edge, stubs.GwPortPrefix)

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

    def __init__(self, source, target, vlans=None):
        """

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
                    "Interfaces in layer2 graph or GwPortPrefixes in layer3 graph")
        elif source is None and target is None:
            raise GraphException("Source & target can't both be None! Bailing!")

        self.errors = []
        self.source = self.target = None

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

        self.layer = self._get_layer(source, target)
        if (self.layer == 3):
            #todo: Should we do such a check here? Won't directly work with
            # stubs out of the box...
            #
            #assert source.prefix == target.prefix, "GwPortPrefix should be in " \
            #                                       "the same Prefix group!"
            self.vlan = source.prefix.vlan

        if self.source and self.source.interface is not None and self.target and self.target.interface is not None:
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

        self.vlans = vlans or []
        self.prefixes = []

    def __hash__(self):
        return hash(self.source) + hash(self.target)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            return self.source == other.source and self.target == other.target

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_json(self):
        json = {
            'source': self.source and self.source.to_json() or 'null',
            'target': self.target and self.target.to_json() or 'null',
        }
        if self.layer == 3:
            json.update({'vlan': _vlan_to_json(self.vlan)})
            json.update(
                {'prefixes': [unicode(prefix) for prefix in self.prefixes]}
            )
        elif self.layer == 2:
            json.update({'vlans': [_vlan_to_json(swpv.vlan)
                                   for swpv in self.vlans]})

        json.update({'link_speed': self.link_speed or 'N/A'})
        return json


def _vlan_to_json(vlan):
    return {'vlan': vlan.vlan,
            'nav_vlan': vlan.id,
            'net_ident': unicode(vlan.net_ident)}

def node_to_json_layer2(node, nx_metadata=None):
    """Convert a node to json, for use in a netmap layer2 graph

    :param node A Netbox model
    :param nx_metadata Metadata from networkx graph.
    :return json presentation of a node.
    """
    json = _node_to_json(node, nx_metadata)

    vlans = None
    metadata = nx_metadata['metadata'] if nx_metadata and nx_metadata.has_key(
        'metadata') else None
    if metadata and metadata.has_key('vlans'):
        # nav_vlan_id == swpv.vlan.id
        vlans = [{'vlan': swpv.vlan.vlan, 'nav_vlan': nav_vlan_id,
                  'net_ident': swpv.vlan.net_ident} for nav_vlan_id, swpv in
                 metadata['vlans']]

    json.update({'vlans': vlans})

    return json


def node_to_json_layer3(node, nx_metadata=None):
    """Convert a node to json, for use in a netmap layer3 graph

    :param node A Netbox model
    :param nx_metadata Metadata from networkx graph.
    :return json presentation of a node.
    """
    json = _node_to_json(node, nx_metadata)
    return json


def _node_to_json(node, nx_node):
    """Generic method for converting a node to json, for use in both layer 2
    and layer3 graphs.

    :param node A Netbox model
    :param nx_metadata Metadata from networkx graph.
    :return json presentation of a node.
    """
    position = None
    metadata = nx_node['metadata'] if nx_node and nx_node.has_key(
        'metadata') else None

    if metadata:
        if metadata.has_key('position'):
            position = {'x': metadata['position'].x,
                        'y': metadata['position'].y}

    if isinstance(node, stubs.Netbox):
        return {
            'sysname': node.sysname,
            'category': str(node.category_id),
            'is_elink_node': True
        }
    else:
        return {
            'id': str(node.pk),
            'sysname': str(node.sysname),
            'category': str(node.category_id),
            'ip': node.ip,
            'ipdevinfo_link': reverse('ipdevinfo-details-by-name',
                                      args=[node.sysname]),
            'position': position,
            'up': str(node.up),
            'up_image': get_status_image_link(node.up),
            'roomid': node.room.id,
            'locationid': unicode(node.room.location.id),
            'location': unicode(node.room.location.description),
            'room': unicode(node.room),
            'is_elink_node': False,
        }


def edge_to_json_layer2(metadata):
    """Convert a edge between A and B in a netmap layer2 graph to JSON

    :param edge Metadata from netmap networkx graph
    :return edge representation in JSON
    """
    edges = metadata['metadata']
    metadata_for_edges = []
    for edge in edges:
        metadata_for_edges.append(edge_to_json(edge))

    return metadata_for_edges


def edge_to_json_layer3(vlan_metadata_dict):
    """Convert a edge between A and B in a netmap layer 3 graph to JSON

    :param metadata Metadata from netmap networkx graph
    :return edge representation in JSON
    """
    metadata_collection = []
    for metadata in vlan_metadata_dict.values():
        metadata_collection.append(edge_to_json(metadata))
    return metadata_collection



def edge_to_json(metadata):
    """Generic method for converting a edge bewteen A and B to JSON
    For use in both layer 2 and layer 3 topologies.

    :param networkx_edge_with_data tuple(netbox_a, netbox_b)
    :return JSON presentation of a edge.
    """

    return metadata.to_json()



def edge_metadata_layer3(source, target, prefixes):
    """

    :param source nav.models.manage.GwPortPrefix
    :param target nav.models.manage.GwPortPrefix
    :param prefixes list of prefixes (Prefix)
    :returns metadata to attach to netmap graph
    """



    #prefix = other_gwpp.prefix
    #if this_gwprefix_meta:
    #    metadata['uplink']['thiss'].update(this_gwprefix_meta)
    #if other_gwprefix_meta:
    #    metadata['uplink']['other'].update(other_gwprefix_meta)
    #metadata['uplink'].update({'vlan': prefix.vlan, 'prefixes': prefixes})

    edge = Edge(source, target)
    edge.prefixes = prefixes
    return edge


    #return metadata


def edge_metadata_layer2(source, target, vlans_by_interface):
    """
    Adds edge meta data with python types for given edge (layer2)

    :param source nav.models.manage.Interface
    :param target nav.models.manage.Interface
    :param vlans_by_interface VLAN dict access for fetching SwPortVlan list

    :returns metadata to attach to netmap graph as metadata.
    """

    vlans = []
    if vlans_by_interface and vlans_by_interface.has_key(source):
        vlans = sorted(vlans_by_interface.get(source),
                       key=lambda x: x.vlan.vlan)

    edge = Edge(source, target)
    edge.vlans = vlans
    return edge

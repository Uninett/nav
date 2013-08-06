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

    def __init__(self, source, target, vlans=None):
        """

        :param source: source, where it is either of type Interface or type
         GwPortPrefix.
        :param target: target, where it is either of type Interface or type
         GwPortPrefix
        :param vlans: List of SwPortVlan on this particular edge pair
        :return:
        """

        if type(source) == Interface and type(target) == Interface:
            # Layer 2
            self.source = Group(source.netbox, source)
            self.target = Group(target.netbox, target)
            self._layer = 2
        elif (
                (type(source) == GwPortPrefix or type(
                        source) == stubs.GwPortPrefix) and
                (type(target) == GwPortPrefix or type(
                        target) == stubs.GwPortPrefix)):
            # Layer 3
            self.source = Group(source.interface.netbox, source.interface)
            self.source.gw_ip = source.gw_ip
            self.source.virtual = source.virtual

            self.target = Group(target.interface.netbox, target.interface)
            self.target.gw_ip = target.gw_ip
            self.target.virtual = target.virtual

            assert source.prefix == target.prefix, "GwPortPrefix should be in the same Prefix group!"
            self.vlan = source.prefix.vlan
            self._layer = 3

        else:
            raise GraphException(
                "Source and target has to be of same type, "
                "typically Interfaces in layer2 graph or "
                "GwPortPrefixes in layer3 graph")

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
            'source': self.source.to_json(),
            'target': self.target.to_json(),
        }
        if self._layer == 2:
            pass
        elif self._layer == 3:
            json.update('vlan', self.vlan)
        return json

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


def edge_to_json_layer2(edge, metadata):
    """Convert a edge between A and B in a netmap layer2 graph to JSON

    :param edge Metadata from netmap networkx graph
    :return edge representation in JSON
    """
    metadata = metadata['metadata']
    list_of_directional_metadata_edges = edge_to_json(edge, metadata)

    for index, json in enumerate(list_of_directional_metadata_edges):
        if type(json['uplink']) == dict:
            # Add vlan meta data for layer2
            uplink = json['uplink']
            vlans = None
            if metadata[index]['uplink'].has_key('vlans') and metadata[index]['uplink']['vlans']:
                vlans = [{'vlan': swpv.vlan.vlan, 'nav_vlan': swpv.vlan.id,
                          'net_ident': unicode(swpv.vlan.net_ident)} for swpv in
                         metadata[index][
                             'uplink'][
                             'vlans']]
                uplink['vlans'] = vlans
    return list_of_directional_metadata_edges


def edge_to_json_layer3(edge, vlan_metadata_dict):
    """Convert a edge between A and B in a netmap layer 3 graph to JSON

    :param metadata Metadata from netmap networkx graph
    :return edge representation in JSON
    """
    for metadata in vlan_metadata_dict.values():
        metadata = metadata['metadata']
        collection_of_uplinks = edge_to_json(edge, [metadata])

        for json in collection_of_uplinks:
            if type(json['uplink']) == dict:
                uplink = json['uplink']

                # Add prefix metadata
                vlan = None

                uplink_this = {}
                uplink_other = {}
                #                'net_address': unicode(metadata['uplink'][
                # 'prefix']
                # .net_address),
                if metadata['uplink'].has_key('vlan') and metadata['uplink'][
                    'vlan']:
                    vlan = {
                        'net_ident': unicode(
                            metadata['uplink']['vlan'].net_ident),
                        'description': unicode(
                            metadata['uplink']['vlan'].description)
                    }

                    uplink.update({'prefixes': [x.net_address for x in
                                                metadata['uplink'][
                                                    'prefixes']]})

                    if metadata['uplink']['thiss'].has_key('gw_ip'):
                        uplink_this.update(
                            {'gw_ip': metadata['uplink']['thiss']['gw_ip'],
                             'virtual': metadata['uplink']['thiss']['virtual']})

                    if metadata['uplink']['other'].has_key('gw_ip'):
                        uplink_other.update(
                            {'gw_ip': metadata['uplink']['other']['gw_ip'],
                             'virtual': metadata['uplink']['other']['virtual']})

                uplink['thiss'].update(uplink_this)
                uplink['other'].update(uplink_other)

                uplink['vlan'] = vlan

        return collection_of_uplinks


def edge_to_json(edge, metadata):
    """Generic method for converting a edge bewteen A and B to JSON
    For use in both layer 2 and layer 3 topologies.

    :param networkx_edge_with_data tuple(netbox_a, netbox_b)
    :return JSON presentation of a edge.
    """

    edge_metadata = []
    for directional_metadata_edge in metadata:
        uplink = directional_metadata_edge['uplink']
        link_speed = directional_metadata_edge['link_speed']
        tip_inspect_link = directional_metadata_edge['tip_inspect_link']
        error = directional_metadata_edge['error']

        # jsonify
        if not uplink:
            uplink_json = 'null' # found no uplinks, json null.
        else:
            uplink_json = {}

            if uplink['thiss']['interface']:
                uplink_json.update(
                    {'thiss': {
                        'interface': unicode(
                            uplink['thiss']['interface'].ifname),
                        'netbox': uplink['thiss']['netbox'].sysname,
                        'interface_link': uplink['thiss'][
                            'interface'].get_absolute_url(),
                        'netbox_link': uplink['thiss'][
                            'netbox'].get_absolute_url()
                    }}
                )
            else:
                uplink_json.update(
                    {'thiss': {'interface': 'N/A', 'netbox': 'N/A'}})

            if uplink['other']['interface']:
                uplink_json.update(
                    {'other': {
                        'interface': unicode(
                            uplink['other']['interface'].ifname),
                        'netbox': uplink['other']['netbox'].sysname,
                        'interface_link': uplink['other'][
                            'interface'].get_absolute_url(),
                        'netbox_link': uplink['other'][
                            'netbox'].get_absolute_url()
                    }}
                )
            else:
                uplink_json.update(
                    {'other': {'interface': 'N/A', 'netbox': 'N/A'}})

        if 'link_speed' in error.keys():
            link_speed = error['link_speed']
        elif not link_speed:
            link_speed = "N/A"

        edge_metadata.append(
            {
                'uplink': uplink_json,
                'link_speed': link_speed,
                'tip_inspect_link': tip_inspect_link,
            }
        )
    return edge_metadata


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

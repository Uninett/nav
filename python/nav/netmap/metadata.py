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
from nav.models.manage import GwPortPrefix
from nav.netmap import stubs
from nav.web.netmap.common import get_status_image_link


_LOGGER = logging.getLogger(__name__)


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


def edge_to_json_layer3(metadata):
    """Convert a edge between A and B in a netmap layer 3 graph to JSON

    :param metadata Metadata from netmap networkx graph
    :return edge representation in JSON
    """
    metadata = metadata['metadata']
    json = edge_to_json(metadata)

    if type(json['uplink']) == dict:
        uplink = json['uplink']

        # Add prefix metadata
        vlan = None

        uplink_this = {}
        uplink_other = {}
        #                'net_address': unicode(metadata['uplink']['prefix']
        # .net_address),
        if metadata['uplink'].has_key('vlan') and metadata['uplink']['vlan']:
            vlan = {
                'net_ident': unicode(metadata['uplink']['vlan'].net_ident),
                'description': unicode(metadata['uplink']['vlan'].description)
            }

            uplink.update({'prefixes': [x.net_address for x in
                                        metadata['uplink']['prefixes']]})

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

    return json


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
                        'interface': unicode(uplink['thiss']['interface'].ifname),
                        'netbox': uplink['thiss']['netbox'].sysname,
                        'interface_link': uplink['thiss'][
                                          'interface'].get_absolute_url(),
                        'netbox_link': uplink['thiss']['netbox'].get_absolute_url()
                    }}
                )
            else:
                uplink_json.update({'thiss': {'interface': 'N/A', 'netbox': 'N/A'}})

            if uplink['other']['interface']:
                uplink_json.update(
                        {'other': {
                        'interface': unicode(uplink['other']['interface'].ifname),
                        'netbox': uplink['other']['netbox'].sysname,
                        'interface_link': uplink['other'][
                                          'interface'].get_absolute_url(),
                        'netbox_link': uplink['other']['netbox'].get_absolute_url()
                    }}
                )
            else:
                uplink_json.update({'other': {'interface': 'N/A', 'netbox': 'N/A'}})

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


def edge_metadata_layer3(thiss_gwpp, other_gwpp, prefixes):
    """
    Adds edge meta data with python types for given edge (layer3)

    :param thiss_gwpp This netbox's GwPortPrefix
    :param other_gwpp Other netbox's GwPortPrefix
    :param prefixes list of prefixes (Prefix)
    :returns metadata to attach to your netmap networkx graph
    """

    prefix = None
    this_gwprefix_meta = None
    other_gwprefix_meta = None

    if thiss_gwpp:
        prefix = thiss_gwpp.prefix

        if isinstance(thiss_gwpp, GwPortPrefix):
            this_gwprefix_meta = {'gw_ip': thiss_gwpp.gw_ip,
                                  'virtual': thiss_gwpp.virtual}
    if other_gwpp:
        if not prefix:
            prefix = other_gwpp.prefix

        if isinstance(other_gwpp, GwPortPrefix):
            other_gwprefix_meta = {'gw_ip': other_gwpp.gw_ip,
                                   'virtual': other_gwpp.virtual}

    metadata = edge_metadata(thiss_gwpp.interface.netbox, thiss_gwpp.interface,
        other_gwpp.interface.netbox, other_gwpp.interface)

    if this_gwprefix_meta:
        metadata['uplink']['thiss'].update(this_gwprefix_meta)
    if other_gwprefix_meta:
        metadata['uplink']['other'].update(other_gwprefix_meta)
    metadata['uplink'].update({'vlan': prefix.vlan, 'prefixes': prefixes})

    return metadata


def edge_metadata_layer2(thiss_netbox, thiss_interface, other_netbox,
                         other_interface, vlans_by_interface):
    """
    Adds edge meta data with python types for given edge (layer2)

    :param thiss_netbox This netbox (edge from)
    :param thiss_interface This netbox's interface (edge from)
    :param other_netbox Other netbox (edge_to)
    :param other_interface Other netbox's interface (edge_to)
    :returns metadata to attach to your netmap networkx graph
    """

    metadata = edge_metadata(thiss_netbox, thiss_interface, other_netbox,
        other_interface)

    vlans = None
    if vlans_by_interface and vlans_by_interface.has_key(thiss_interface):
        vlans = sorted(vlans_by_interface.get(thiss_interface),
            key=lambda x: x.vlan.vlan)

    metadata['uplink'].update({'vlans': vlans})
    # add check against other_interface vlans?

    return metadata


def edge_metadata(thiss_netbox, thiss_interface, other_netbox, other_interface):
    """
    Adds edge meta data with python types for given edge
    For use in both layer 2 and layer 3 topologies.

    :param thiss_netbox This netbox (edge from)
    :param thiss_interface This netbox's interface (edge from)
    :param other_netbox Other netbox (edge_to)
    :param other_interface Other netbox's interface (edge_to)
    :returns metadata to attach to your netmap networkx graph
    """
    error = {}
    tip_inspect_link = False

    uplink = {'thiss': {'netbox': thiss_netbox, 'interface': thiss_interface},
              'other': {'netbox': other_netbox,
                        'interface': other_interface}}

    if thiss_interface and other_interface and \
       thiss_interface.speed != other_interface.speed:
        if thiss_netbox.category_id is not 'elink' and \
           other_netbox.category_id is not 'elink':

            tip_inspect_link = True
            link_speed = None
            error[
            'link_speed'] = 'Interface link speed not the same between the ' \
                            'nodes'
        else:
            link_speed = None

    else:
        if thiss_interface and thiss_interface.speed:
            link_speed = thiss_interface.speed
        elif other_interface and other_interface.speed:
            link_speed = other_interface.speed
        else:
            link_speed = None

    return {
        'uplink': uplink,
        'tip_inspect_link': tip_inspect_link,
        'link_speed': link_speed,
        'error': error,
        }
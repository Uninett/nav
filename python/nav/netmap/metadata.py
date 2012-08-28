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
import logging
from django.core.urlresolvers import reverse
from nav.models.manage import GwPortPrefix
from nav.netmap.stubs import Netbox
from nav.web.netmapdev.common import get_status_image_link


_LOGGER = logging.getLogger(__name__)


def node_to_json_layer2(node, nx_metadata=None):
    json = _node_to_json(node, nx_metadata)

    vlans = None
    metadata = nx_metadata['metadata'] if nx_metadata and nx_metadata.has_key('metadata') else None
    if metadata and metadata.has_key('vlans'):
        # nav_vlan_id == swpv.vlan.id
        vlans = [{'vlan': swpv.vlan.vlan, 'nav_vlan': nav_vlan_id, 'net_ident': swpv.vlan.net_ident} for nav_vlan_id, swpv in metadata['vlans']]

    json.update({'vlans': vlans})

    return json

def node_to_json_layer3(node, nx_metadata=None):
    json = _node_to_json(node, nx_metadata)
    return json


def _node_to_json(node, nx_metadata=None):
    """Filter our metadata for a node in JSON-format

    Used for showing metadata in NetMap with D3

    :param node A Netbox model
    :returns: metadata for a node
    """
    position = None
    metadata = nx_metadata['metadata'] if nx_metadata and nx_metadata.has_key('metadata') else None

    if metadata:
        if metadata.has_key('position'):
            position = {'x': metadata['position'].x, 'y': metadata['position'].y}

    if isinstance(node, Netbox):
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
            'is_elink_node': False,
            #'roomid': 'fooo',
        }


def edge_to_json_layer2(metadata):
    json = edge_to_json(metadata)

    if type(json['uplink']) == dict:
        # Add vlan meta data for layer2
        uplink = json['uplink']
        vlans = None
        if metadata['uplink'].has_key('vlans') and metadata['uplink']['vlans']:
            vlans = [{'vlan': swpv.vlan.vlan, 'nav_vlan': swpv.vlan.id, 'net_ident': unicode(swpv.vlan.net_ident)} for swpv in metadata['uplink']['vlans']]
            uplink['vlans'] = vlans
    return json


def edge_to_json_layer3(metadata):
    json = edge_to_json(metadata)

    if type(json['uplink']) == dict:
        uplink = json['uplink']

        # Add prefix metadata
        prefix = None

        uplink_this = {}
        uplink_other = {}

        if metadata['uplink'].has_key('prefix') and metadata['uplink']['prefix']:
            #prefix = unicode(metadata['uplink']['prefix'].vlan.net_ident)
            prefix = unicode(metadata['uplink']['prefix'])
            if metadata['uplink']['thiss'].has_key('gw_ip'):
                uplink_this.update(
                        {'gw_ip': metadata['uplink']['thiss']['gw_ip'],
                         'hsrp': metadata['uplink']['thiss']['hsrp']})

            if metadata['uplink']['other'].has_key('gw_ip'):
                uplink_other.update(
                        {'gw_ip': metadata['uplink']['other']['gw_ip'],
                         'hsrp': metadata['uplink']['other']['hsrp']})

        uplink['thiss'].update(uplink_this)
        uplink['other'].update(uplink_other)
        uplink['prefix'] = prefix

    return json

def edge_to_json(metadata):
    """converts edge information to json"""

    uplink = metadata['uplink']
    link_speed = metadata['link_speed']
    tip_inspect_link = metadata['tip_inspect_link']
    error = metadata['error']

    # jsonify
    if not uplink:
        uplink_json = 'null' # found no uplinks, json null.
    else:
        uplink_json = {}

        if uplink['thiss']['interface']:
            uplink_json.update(
                    {'thiss': {'interface': "{0} at {1}".format(
                    str(uplink['thiss']['interface'].ifname),
                    str(uplink['thiss']['interface'].netbox.sysname)
                ), 'netbox': uplink['thiss']['netbox'].sysname,
                              }}
            )
        else:
            uplink_json.update({'thiss': {'interface': 'N/A', 'netbox': 'N/A'}})

        if uplink['other']['interface']:
            uplink_json.update(
                    {'other': {'interface': "{0} at {1}".format(
                    str(uplink['other']['interface'].ifname),
                    str(uplink['other']['interface'].netbox.sysname)
                ), 'netbox': uplink['other']['netbox'].sysname}}
            )
        else:
            uplink_json.update({'other': {'interface': 'N/A', 'netbox': 'N/A'}})

    if 'link_speed' in error.keys():
        link_speed = error['link_speed']
    elif not link_speed:
        link_speed = "N/A"

    return {
        'uplink': uplink_json,
        'link_speed': link_speed,
        'tip_inspect_link': tip_inspect_link,
        }


def edge_metadata_layer3(thiss_gwpp, other_gwpp):
    """
    Adds edge meta data with python types for given edge (layer3)

    :param thiss_gwpp This netbox's GwPortPrefix
    :param other_gwpp Other netbox's GwPortPrefix
    """

    net_ident = None
    this_gwprefix_meta = None
    other_gwprefix_meta = None

    if thiss_gwpp:
        net_ident = thiss_gwpp.prefix

        if isinstance(thiss_gwpp, GwPortPrefix):
            this_gwprefix_meta = { 'gw_ip': thiss_gwpp.gw_ip, 'hsrp': thiss_gwpp.hsrp }
    if other_gwpp:
        net_ident = other_gwpp.prefix

        if isinstance(other_gwpp, GwPortPrefix):
            other_gwprefix_meta = { 'gw_ip': other_gwpp.gw_ip, 'hsrp': other_gwpp.hsrp }

    metadata = edge_metadata(thiss_gwpp.interface.netbox, thiss_gwpp.interface, other_gwpp.interface.netbox, other_gwpp.interface)

    if this_gwprefix_meta:
        metadata['uplink']['thiss'].update(this_gwprefix_meta)
    if other_gwprefix_meta:
        metadata['uplink']['other'].update(other_gwprefix_meta)
    metadata['uplink'].update({'prefix': net_ident})

    return metadata



def edge_metadata_layer2(thiss_netbox, thiss_interface, other_netbox, other_interface, vlans_by_interface):
    """
    Adds edge meta data with python types for given edge (layer2)

    :param thiss_netbox This netbox (edge from)
    :param thiss_interface This netbox's interface (edge from)
    :param other_netbox Other netbox (edge_to)
    :param other_interface Other netbox's interface (edge_to)
    """

    metadata = edge_metadata(thiss_netbox, thiss_interface, other_netbox, other_interface)

    vlans = None
    if vlans_by_interface and vlans_by_interface.has_key(thiss_interface):
        vlans = sorted(vlans_by_interface.get(thiss_interface), key=lambda x:x.vlan.vlan)

    metadata['uplink'].update({'vlans': vlans})
    # add check against other_interface vlans?

    return metadata


def edge_metadata(thiss_netbox, thiss_interface, other_netbox, other_interface):
    """
    Adds edge meta data with python types for given edge (layer2)

    :param thiss_netbox This netbox (edge from)
    :param thiss_interface This netbox's interface (edge from)
    :param other_netbox Other netbox (edge_to)
    :param other_interface Other netbox's interface (edge_to)
    """
    error = {}
    tip_inspect_link = False

    uplink = {'thiss': {'netbox': thiss_netbox, 'interface': thiss_interface},
              'other': {'netbox': other_netbox,
                        'interface': other_interface}}

    if thiss_interface and other_interface and thiss_interface.speed !=\
                                               other_interface.speed:
        tip_inspect_link = True
        link_speed = None
        error[
        'link_speed'] = 'Interface link speed not the same between the nodes'
    else:
        if thiss_interface and thiss_interface.speed:
            link_speed = thiss_interface.speed
        else:
            link_speed = other_interface.speed


    return {
        'uplink': uplink,
        'tip_inspect_link': tip_inspect_link,
        'link_speed': link_speed,
        'error': error,
        }
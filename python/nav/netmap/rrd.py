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
from nav.netmap import stubs
from nav.rrd2 import presenter
from nav.web.netmapdev.common import get_traffic_rgb

_LOGGER = logging.getLogger(__name__)


def _get_datasources(interfaces):
    from nav.models.rrd import RrdDataSource
    return RrdDataSource.objects.filter(
        rrd_file__key='interface').select_related('rrd_file').filter(
        rrd_file__value__in=interfaces)


def _get_datasource_lookup(graph):
    edges_iter = graph.edges_iter(data=True)

    interfaces = set()
    for _, _, w in edges_iter:
        w = w['metadata'] if 'metadata' in w else {}
        if 'uplink' in w:
            if w['uplink']['thiss']['interface']:
                interfaces.add(w['uplink']['thiss']['interface'].pk)

            if w['uplink']['other']['interface']:
                interfaces.add(w['uplink']['other']['interface'].pk)

    _LOGGER.debug(
        "netmap:attach_rrd_data_to_edges() datasource id filter list done")

    datasources = _get_datasources(interfaces)

    _LOGGER.debug("netmap:attach_rrd_data_to_edges() Datasources fetched done")

    lookup_dict = {}
    for data in datasources:
        interface = int(data.rrd_file.value)
        if interface in lookup_dict:
            lookup_dict[interface].append(data)
        else:
            lookup_dict.update({interface: [data]})

    _LOGGER.debug(
        "netmap:attach_rrd_data_to_edges() Datasources rearranged in dict")

    return lookup_dict


def rrd_info(source):
    # todo : what to do if rrd source is not where it should be? Will return 0
    # if it can't find RRD file for example
    a = presenter.Presentation()
    a.add_datasource(source)
    return {'name': source.name, 'description': source.description,
            'raw': a.average()[0]}


def attach_rrd_data_to_edges(graph, json=None, debug=False):
    """ called from d3_js to attach rrd_data after it has attached other
    edge metadata by using edge_to_json

    todo: update doc, shouldn't really be here either as we want RRD
    data to be updated by client code using ajax.

    :param graph A network x graph matching d3_js graph format
    """
    node_labels = [(b, a) for (a, b) in graph.node_labels.items()]
    node_labels.sort()

    datasource_lookup = _get_datasource_lookup(graph)

    # , u'ifInErrors', u'ifInUcastPkts', u'ifOutErrors', u'ifOutUcastPkts'
    valid_traffic_sources = (
        u'ifHCInOctets', u'ifHCOutOctets', u'ifInOctets', u'ifOutOctets')

    edges_iter = graph.edges_iter(data=True)
    for j, k, w in edges_iter:
        traffic = {}
        traffic['inOctets'] = None
        traffic['outOctets'] = None

        if 'metadata' in w:
            metadata = w['metadata']

            if not isinstance(metadata['uplink']['thiss']['netbox'], stubs.Netbox):
                if metadata['uplink']['thiss']['interface'].pk in datasource_lookup:
                    datasources_for_interface = datasource_lookup[
                                                metadata['uplink']['thiss'][
                                                'interface'].pk]
                    for rrd_source in datasources_for_interface:
                        if rrd_source.description in valid_traffic_sources and\
                           rrd_source.description not in traffic:
                            if debug:
                                traffic[rrd_source.description] = rrd_info(
                                    rrd_source)


            if 'ifInOctets' in traffic:
                traffic['inOctets'] = traffic['ifInOctets']
            if 'ifOutOctets' in traffic:
                traffic['outOctets'] = traffic['ifOutOctets']

            # Overwrite traffic inOctets and outOctets
            # if 64 bit counters are present
            if 'ifHCInOctets' in traffic:
                traffic['inOctets'] = traffic['ifHCInOctets']

            if 'ifHCOutOctets' in traffic:
                traffic['outOctets'] = traffic['ifHCOutOctets']


        unknown_speed_css = (211,211,211) # light grey

        traffic['inOctets_css'] = get_traffic_rgb(traffic['inOctets']['raw'],
            metadata['link_speed']) if traffic['inOctets'] and\
                                       traffic['inOctets']['raw'] else unknown_speed_css
        traffic['outOctets_css'] = get_traffic_rgb(traffic['outOctets']['raw'],
            metadata['link_speed']) if traffic['outOctets'] and\
                                       traffic['inOctets']['raw'] else unknown_speed_css


        for json_edge in json:

            if json_edge['source'] == node_labels[j][1].sysname and json_edge['target'] == node_labels[k][1].sysname:
                json_edge['data'].update({'traffic':traffic})
                break
    return json
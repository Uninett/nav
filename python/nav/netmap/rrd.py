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
"""Netmap functions for attaching RRD/traffic metadata to netmap"""
import logging
from nav.models.manage import Interface
from nav.netmap import stubs
from nav.rrd2 import presenter
from nav.web.netmapdev.common import get_traffic_rgb, \
    get_traffic_load_in_percent

_LOGGER = logging.getLogger(__name__)


def _get_datasources(interfaces):
    from nav.models.rrd import RrdDataSource
    return RrdDataSource.objects.filter(
        rrd_file__key='interface').select_related('rrd_file').filter(
        rrd_file__value__in=interfaces)


def _get_datasource_lookup(graph):
    edges_iter = graph.edges_iter(data=True)

    interfaces = set()
    for _, _, meta in edges_iter:
        meta = meta['metadata'] if 'metadata' in meta else {}
        if 'uplink' in meta:
            if meta['uplink']['thiss']['interface'] and \
               isinstance(meta['uplink']['thiss']['interface'], Interface):
                interfaces.add(meta['uplink']['thiss']['interface'].pk)

            if meta['uplink']['other']['interface'] and \
               isinstance(meta['uplink']['other']['interface'], Interface):
                interfaces.add(meta['uplink']['other']['interface'].pk)

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
    """fetches RRD info using presenter.Presentation
    :param source RrdDataSource model from nav.rrd2
    :returns dict of name, description and raw value on data source lookup
    """

    # todo : what to do if rrd source is not where it should be? Will return 0
    # if it can't find RRD file for example
    presentation = presenter.Presentation()
    presentation.add_datasource(source)
    return {'name': source.name, 'description': source.description,
            'raw': presentation.average()[0]}


def attach_rrd_data_to_edges(graph, json=None):
    """ called from d3_js to attach rrd_data after it has attached other
    edge metadata by using edge_to_json

    todo: update doc, shouldn't really be here either as we want RRD
    data to be updated by client code using ajax.

    :param graph A network x graph matching d3_js graph format
    """
    node_labels = [(b, a) for (a, b) in graph.node_labels.items()]
    node_labels.sort()

    datasource_lookup = _get_datasource_lookup(graph)

    def _fetch_rrd(uplink):
        traffic = {}
        if uplink['interface'] and not isinstance(
            uplink['interface'], stubs.Interface):
            if uplink['interface'].pk in datasource_lookup:
                datasources_for_interface = datasource_lookup[
                                            uplink[
                                            'interface'].pk]
                for rrd_source in datasources_for_interface:
                    if rrd_source.description in valid_traffic_sources and\
                       rrd_source.description not in traffic:
                        traffic[rrd_source.description] = rrd_info(
                            rrd_source)
        return traffic


    # , u'ifInErrors', u'ifInUcastPkts', u'ifOutErrors', u'ifOutUcastPkts'
    valid_traffic_sources = (
        u'ifHCInOctets', u'ifHCOutOctets', u'ifInOctets', u'ifOutOctets')

    edges_iter = graph.edges_iter(data=True)
    for j, k, meta in edges_iter:
        traffic = {}
        traffic['inOctets'] = None
        traffic['outOctets'] = None

        if 'metadata' in meta:
            metadata = meta['metadata']
            direction = 'thiss'
            traffic.update(_fetch_rrd(metadata['uplink'][direction]))

            if not any(source in traffic for source in valid_traffic_sources):
                direction = 'other'
                traffic.update(_fetch_rrd(metadata['uplink'][direction]))



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

            # swap
            if direction == 'other':
                tmp = traffic['inOctets']
                traffic['inOctets'] = traffic['outOctets']
                traffic['outOctets'] = tmp

        unknown_speed_css = (211, 211, 211) # light grey

        in_octets_percent = get_traffic_load_in_percent(
            traffic['inOctets']['raw'],
            metadata['link_speed']) if traffic['inOctets'] and \
                                       traffic['inOctets']['raw'] else None
        out_octets_percent = get_traffic_load_in_percent(
            traffic['outOctets']['raw'],
            metadata['link_speed']) if traffic['outOctets'] and \
                                       traffic['outOctets']['raw'] else None

        traffic['inOctets_css'] = get_traffic_rgb(in_octets_percent) if in_octets_percent else unknown_speed_css
        traffic['outOctets_css'] = get_traffic_rgb(out_octets_percent) if out_octets_percent else unknown_speed_css
        traffic['inOctetsPercentBySpeed'] = "%.2f" % in_octets_percent if in_octets_percent else None
        traffic['outOctetsPercentBySpeed'] = "%.2f" % out_octets_percent if out_octets_percent else None

        for json_edge in json:

            if json_edge['source'] == node_labels[j][1].sysname and \
               json_edge['target'] == node_labels[k][1].sysname:
                json_edge['data'].update({'traffic':traffic})
                break
    return json
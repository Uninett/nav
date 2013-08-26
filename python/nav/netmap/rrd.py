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
from nav.web.netmap.common import get_traffic_rgb, \
    get_traffic_load_in_percent

_LOGGER = logging.getLogger(__name__)


def _get_datasources(interfaces):
    from nav.models.rrd import RrdDataSource
    return RrdDataSource.objects.filter(
        rrd_file__key='interface').select_related('rrd_file').filter(
        rrd_file__value__in=interfaces)


def _get_datasource_lookup(interfaces):

    datasources = _get_datasources([isinstance(interface, Interface) and interface.pk for interface in interfaces])
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


class Source(object):
    def __init__(self, rrd_datasource):
        # todo : what to do if rrd source is not where it should be? Will return 0
        # if it can't find RRD file for example
        self.source = rrd_datasource
        presentation = presenter.Presentation()
        presentation.add_datasource(self.source)
        self.raw = presentation.average()[0]


    def to_json(self):
        return {
            'name': self.source.name,
            'description': self.source.description,
            'raw': self.raw
        }

class Octets(object):
    CSS_UNKNOWN_SPEED = (211, 211, 211) # light grey

    def __init__(self, name, source, link_speed):
        self.name = name
        self.source = source
        raw = source.raw

        self.load_in_percent = get_traffic_load_in_percent(raw, link_speed)
        if self.load_in_percent is not None:
            self.css = get_traffic_rgb(self.load_in_percent)
            self.octets_percent_by_speed = "%.2f" % self.load_in_percent
        else:
            self.css = self.CSS_UNKNOWN_SPEED
            self.octets_percent_by_speed = None

    def __repr__(self):
        return ("netmap.Octets(name={0!r}, source={1!r}, load_in_percent={2!r},"
                "octets_percent_by_speed={3!r}, css={4!r})").format(self.name, self.source, self.load_in_percent,
                                                                    self.octets_percent_by_speed, self.css)

    def to_json(self):
        return {
            'rrd': self.source.to_json(),
            'css': self.css,
            'percent_by_speed': self.octets_percent_by_speed,
            'load_in_percent': self.load_in_percent,
            'name': self.name
        }




class Traffic(object):


    def __init__(self):
        self.source = None
        self.target = None
        self.has_swapped = False
        #self.in_octets = Octets('inOctets', Source('ds1', 'ifHCInOctets', 809.399562), 100)
        #self.out_octets = Octets('outOctets', Source('ds1', 'ifHCOutOctets', 55809.399562), 100)

    def __repr__(self):
        return "netmap.Traffic(in={0!r}, out={1!r}, swapped={2!r})".format(
            self.source, self.target,self.has_swapped)

    def swap(self):
        tmp = self.source
        self.source = self.target
        self.target = tmp
        self.has_swapped = not self.has_swapped


    def to_json(self):
        return {
            'source': self.source and self.source.to_json() or None,
            'target': self.target and self.target.to_json() or None
        }

def get_rrd_data(cache, port_pair):
    """
    :param cache: dict arriving from _get_datasource_lookup hopefully...
    :param port_pair: tuple containing (source, target)
    :type cache: dict
    :type port_pair: tuple(Interface)
    """

    # , u'ifInErrors', u'ifInUcastPkts', u'ifOutErrors', u'ifOutUcastPkts'
    valid_traffic_sources = (
        u'ifHCInOctets', u'ifHCOutOctets', u'ifInOctets', u'ifOutOctets')
    datasource_lookup = cache

    def _fetch_rrd(interface):
        traffic = {}
        if isinstance(interface, Interface):
            if interface.pk in datasource_lookup:
                datasources_for_interface = datasource_lookup[interface.pk]
                for rrd_source in datasources_for_interface:
                    if (rrd_source.description in valid_traffic_sources
                        and rrd_source.description not in traffic):
                        traffic[rrd_source.description] = Octets(
                            rrd_source.description,
                            Source(rrd_source),
                            interface.speed)
        return traffic



    traffic = Traffic()
    source_port = port_pair[0]
    target_port = port_pair[1]

    should_swap_direction = False
    rrd_sources = _fetch_rrd(source_port)

    if not any(source in rrd_sources for source in valid_traffic_sources):
        should_swap_direction = True
        rrd_sources = _fetch_rrd(target_port)

    if 'ifInOctets' in rrd_sources:
        traffic.source = rrd_sources['ifInOctets']
    if 'ifOutOctets' in rrd_sources:
        traffic.target = rrd_sources['ifOutOctets']

    # Overwrite traffic inOctets and outOctets
    # if 64 bit counters are present
    if 'ifHCInOctets' in rrd_sources:
        traffic.source = rrd_sources['ifHCInOctets']

    if 'ifHCOutOctets' in rrd_sources:
        traffic.target = rrd_sources['ifHCOutOctets']

    # swap
    if should_swap_direction:
        traffic.swap()

    return traffic
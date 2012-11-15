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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""View definitions for info/vlan"""

import logging
from IPy import IP
from os.path import exists
from operator import methodcaller

from django.shortcuts import render_to_response
from django.template.context import RequestContext

from nav.models.manage import Prefix, Vlan
from nav.models.rrd import RrdFile
from nav.rrd2.presenter import Graph

LOGGER = logging.getLogger('nav.web.info.vlan')


def index(request):
    """Render all graphs for prefixes"""
    prefixes = Prefix.objects.exclude(vlan__net_type='loopback')
    images = []
    for prefix in prefixes:
        try:
            rrdfile = RrdFile.objects.get(key='prefix', value=prefix.id)
        except RrdFile.DoesNotExist:
            continue

        if exists(rrdfile.get_file_path()):
            graph = create_prefix_graph(prefix, rrdfile)
            images.append(graph.get_url())

    return render_to_response("info/vlan/base.html",
                              {'images': images},
                              context_instance=RequestContext(request))


def vlan_details(request, vlanid):
    """Render details for a vlan"""
    vlan = Vlan.objects.select_related(depth=1).get(pk=vlanid)
    prefixes = sorted(vlan.prefix_set.all(),
                      key=methodcaller('get_prefix_size'),
                      reverse=True)

    # Create graph for the prefixes
    ipv4_prefixes = []
    for prefix in prefixes:
        try:
            rrdfile = RrdFile.objects.get(key='prefix', value=prefix.id)
        except RrdFile.DoesNotExist:
            LOGGER.error('rrdfile-object for %s did not exist' % prefix)
            continue

        if exists(rrdfile.get_file_path()):
            LOGGER.info('file for %s did exist' % rrdfile)
            prefix.graph = create_prefix_graph(prefix, rrdfile)

            if is_ipv4(prefix):
                ipv4_prefixes.append(prefix)

    if prefixes:
        vlan.graph = create_vlan_graph(vlan, ipv4_prefixes)

    return render_to_response('info/vlan/vlandetails.html',
                              {'vlan': vlan,
                               'prefixes': prefixes},
                              context_instance=RequestContext(request))


def create_prefix_graph(prefix, rrdfile):
    """Create graph based on prefix and rrdfile"""
    datasources = rrdfile.rrddatasource_set.all()

    options = {'-l': '0', '-v': 'IP-addresses', '-w': 300, '-h': 100}
    graph = Graph(title=prefix.net_address, opts=options)
    for datasource in datasources:
        if datasource.name == 'ip_count':
            vname = graph.add_datasource(datasource, 'AREA', 'IP-addresses ')
            add_graph_text(graph, vname)
        if datasource.name == 'mac_count':
            vname = graph.add_datasource(datasource, 'LINE2', 'MAC-addresses')
            add_graph_text(graph, vname)
        if datasource.name == 'ip_range':
            if add_max(prefix):
                vname = graph.add_datasource(datasource, 'LINE2',
                                             'Max addresses')
                add_graph_text(graph, vname)
            else:
                graph.add_argument("COMMENT:   ")

    return graph


def create_vlan_graph(vlan, prefixes):
    """Create graph for this vlan"""

    options = {'-v': 'IP-addresses', '-l': '0'}
    graph = Graph(title='Vlan %s' % vlan, opts=options)

    stack = False
    vnames = []
    for prefix in prefixes:
        rrdfile = RrdFile.objects.get(key='prefix', value=prefix.id)
        ipcount = rrdfile.rrddatasource_set.get(name='ip_count')
        graph.add_datasource(ipcount, 'AREA', prefix.net_address, stack)

        iprange = rrdfile.rrddatasource_set.get(name='ip_range')
        vnames.append(graph.add_def(iprange))

        stack = True  # Stack all ip_counts after the first

    graph.add_cdef('iprange', rpn_sum(vnames))
    graph.add_graph_element('iprange', draw_as='LINE2')

    LOGGER.debug("%r" % graph)

    return graph


def rpn_sum(vnames):
    """Create rpn for adding all vnames"""
    if len(vnames) == 1:
        return vnames[0]
    elif len(vnames) > 1:
        first = vnames.pop(0)
        return ",".join([first] + [",".join((x, '+')) for x in vnames])


def add_max(prefix):
    """Check if we should create max-values for this datasource"""
    return is_ipv4(prefix) and not is_scope(prefix)


def is_scope(prefix):
    """Check if this prefix is a scope-prefix"""
    return prefix.vlan.net_type.id == 'scope'


def is_ipv4(prefix):
    """Check if prefix netaddress is of type 4"""
    return IP(prefix.net_address).version() == 4


def add_graph_text(graph, vname):
    """Add text below graph indicating last, average and max values"""
    graph.add_argument("VDEF:cur_%s=%s,LAST" % (vname, vname))
    graph.add_argument("GPRINT:cur_%s:%s" % (vname, r'Now\: %-6.0lf'))
    graph.add_argument("VDEF:avg_%s=%s,AVERAGE" % (vname, vname))
    graph.add_argument("GPRINT:avg_%s:%s" % (vname, r'Avg\: %-6.0lf'))
    graph.add_argument("VDEF:max_%s=%s,MAXIMUM" % (vname, vname))
    graph.add_argument("GPRINT:max_%s:%s" % (vname, r'Max\: %-6.0lf\l'))

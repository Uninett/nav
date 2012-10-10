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

from IPy import IP
from os.path import exists

from django.shortcuts import render_to_response
from django.template.context import RequestContext

from nav.models.manage import Prefix
from nav.models.rrd import RrdFile
from nav.rrd2.presenter import Graph

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
            graph = create_graph(prefix, rrdfile)
            images.append(graph.get_url())

    return render_to_response("info/vlan/base.html",
                              {'images': images},
                              context_instance=RequestContext(request))


def create_graph(prefix, rrdfile):
    """Create graph based on prefix and rrdfile"""
    datasources = rrdfile.rrddatasource_set.all()

    options = {'-l': '0', '-v': 'IP-addresses'}
    graph = Graph(title=prefix.net_address, opts=options)
    for datasource in datasources:
        if datasource.name == 'ip_count':
            graph.add_datasource(datasource, 'AREA', 'IP-addresses ')
            add_graph_lines(graph, datasource.id, 'ipcount')
        if datasource.name == 'mac_count':
            graph.add_datasource(datasource, 'LINE2', 'MAC-addresses')
            add_graph_lines(graph, datasource.id, 'maccount')
        if is_add_max(datasource, prefix):
            graph.add_datasource(datasource, 'LINE2', 'Max addresses')
            add_graph_lines(graph, datasource.id, 'iprange')

    return graph

def is_add_max(datasource, prefix):
    """Check if we should create max-values for this datasource"""
    return datasource.name == 'ip_range' and \
           is_ipv4(prefix) and \
           not is_scope(prefix)

def is_scope(prefix):
    """Check if this prefix is a scope-prefix"""
    return prefix.vlan.net_type.id == 'scope'

def is_ipv4(prefix):
    """Check if prefix netaddress is of type 4"""
    return IP(prefix.net_address).version() == 4

def add_graph_lines(graph, dsid, variable):
    """Add lines to graph based on dsid and variable"""
    graph.add_argument("VDEF:cur_%s=%s,LAST" % (variable, dsid))
    graph.add_argument("GPRINT:cur_%s:%s" % (variable, 'Now\: %-6.0lf'))
    graph.add_argument("VDEF:avg_%s=%s,AVERAGE" % (variable, dsid))
    graph.add_argument("GPRINT:avg_%s:%s" % (variable, 'Avg\: %-6.0lf'))
    graph.add_argument("VDEF:max_%s=%s,MAXIMUM" % (variable, dsid))
    graph.add_argument("GPRINT:max_%s:%s" % (variable, 'Max\: %-6.0lf\l'))

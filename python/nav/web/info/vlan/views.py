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

from django.shortcuts import render_to_response
from django.template.context import RequestContext

from nav.models.manage import Prefix
from nav.models.rrd import RrdFile
from nav.rrd2.presenter import Presentation, Graph

def index(request):
    prefixes = Prefix.objects.all()[0:50]
    images = []
    for prefix in prefixes:
        try:
            rrdfile = RrdFile.objects.get(key='prefix', value=prefix.id)
        except RrdFile.DoesNotExist:
            continue

        datasources = rrdfile.rrddatasource_set.all()
        pres = Presentation()
        for datasource in datasources:
            pres.add_datasource(datasource)

        graph = Graph(pres, prefix.net_address, params=['-l0', '-v IP-addresses'])
        for datasource in datasources:
            if datasource.name == 'ip_count':
                graph.add_datasource(datasource, 'AREA', 'IP-addresses ')
                add_graph_info(graph, datasource.id, 'ipcount')
            if datasource.name == 'mac_count':
                graph.add_datasource(datasource, 'LINE2', 'MAC-addresses')
                add_graph_info(graph, datasource.id, 'maccount')
            if datasource.name == 'ip_range' and IP(prefix.net_address).version() == 4:
                graph.add_datasource(datasource, 'LINE2', 'Max addresses')
                add_graph_info(graph, datasource.id, 'iprange')

        images.append(graph.get_url())

    return render_to_response("info/vlan/base.html",
                              {'images': images},
                              context_instance=RequestContext(request))


def add_graph_info(graph, dsid, variable):
    graph.add_parameter("VDEF:cur_%s=%s,LAST" % (variable, dsid))
    graph.add_parameter("GPRINT:cur_%s:%s" % (variable, 'Now\: %-6.0lf'))
    graph.add_parameter("VDEF:avg_%s=%s,AVERAGE" % (variable, dsid))
    graph.add_parameter("GPRINT:avg_%s:%s" % (variable, 'Avg\: %-6.0lf'))
    graph.add_parameter("VDEF:max_%s=%s,MAXIMUM" % (variable, dsid))
    graph.add_parameter("GPRINT:max_%s:%s" % (variable, 'Max\: %-6.0lf\l'))

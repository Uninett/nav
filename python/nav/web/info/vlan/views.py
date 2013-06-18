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
from operator import methodcaller, attrgetter
import simplejson

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponse

from nav.models.manage import Prefix, Vlan
from nav.models.rrd import RrdFile
from nav.rrd2.presenter import Graph
from nav.web.utils import create_title
from nav.web.info.vlan.forms import SearchForm

LOGGER = logging.getLogger('nav.web.info.vlan')
ADDRESS_RESERVED_SPACE = 18


def get_path(extra=None):
    """Return breadcrumb list"""
    if not extra:
        extra = []
    return [('Home', '/'), ('Info', reverse('info-search')),
            ('Vlan', reverse('vlan-index'))] + extra


def index(request):
    """Controller for vlan landing page and search"""
    vlans = Vlan.objects.none()

    navpath = get_path()
    if "query" in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            navpath = get_path([('Search for "%s"' % request.GET['query'], )])
            vlans = process_searchform(searchform)
    else:
        searchform = SearchForm()

    LOGGER.debug(vlans)

    return render_to_response("info/vlan/base.html",
                              {'navpath': navpath,
                               'title': create_title(navpath),
                               'form': searchform,
                               'vlans': vlans},
                              context_instance=RequestContext(request))


def process_searchform(form):
    """Find and return vlans based on searchform"""
    query = form.cleaned_data['query']
    LOGGER.debug('Processing searchform for vlans with query: %s' % query)
    if query is None:
        return Vlan.objects.all()
    else:
        return Vlan.objects.filter(
            Q(vlan__icontains=query) |
            Q(net_type__description__icontains=query) |
            Q(description__icontains=query) |
            Q(net_ident__icontains=query)
        ).order_by("vlan")


def vlan_details(request, vlanid):
    """Render details for a vlan"""
    vlan = Vlan.objects.select_related(depth=1).get(pk=vlanid)
    prefixes = sorted(vlan.prefix_set.all(),
                      key=methodcaller('get_prefix_size'))

    navpath = get_path([(str(vlan), '')])

    return render_to_response('info/vlan/vlandetails.html',
                              {'vlan': vlan,
                               'prefixes': prefixes,
                               'gwportprefixes': find_gwportprefixes(vlan),
                               'navpath': navpath,
                               'title': create_title(navpath)},
                              context_instance=RequestContext(request))


def create_prefix_graph(request, prefixid):
    """Create graph based on prefix and rrdfile"""

    try:
        prefix = Prefix.objects.get(pk=prefixid)
        rrdfile = RrdFile.objects.get(key='prefix', value=prefix.id)
    except (Prefix.DoesNotExist, RrdFile.DoesNotExist):
        return HttpResponse(status=500)

    timeframe = request.GET.get('timeframe', 'day')

    datasources = rrdfile.rrddatasource_set.all()

    options = {'-l': '0', '-v': 'IP-addresses', '-w': 300, '-h': 100}
    graph = Graph(title=prefix.net_address, time_frame=timeframe, opts=options)

    add_ip_count(graph, datasources.get(name='ip_count'))
    add_mac_count(graph, datasources.get(name='mac_count'))
    add_ip_range(graph, prefix, datasources.get(name='ip_range'))

    graphurl = graph.get_url()
    if graphurl:
        json = simplejson.dumps({'url': graphurl})
        return HttpResponse(json, mimetype='application/json')
    else:
        return HttpResponse(status=500)


def add_ip_count(graph, datasource):
    """Add ip count to graph"""
    vname = graph.add_datasource(datasource, 'AREA', 'IP-addresses ')
    add_graph_text(graph, vname)


def add_mac_count(graph, datasource):
    """Add mac count to graph"""
    vname = graph.add_datasource(datasource, 'LINE2', 'MAC-addresses')
    add_graph_text(graph, vname)


def add_ip_range(graph, prefix, datasource):
    """Add ip range to graph if not ipv6 address or scope"""
    if add_max(prefix):
        vname = graph.add_datasource(datasource, 'LINE2',
                                     'Max addresses')
        add_graph_text(graph, vname)
    else:
        # Add an empty comment so that the graphs with and without
        # max are equal in size
        graph.add_argument("COMMENT:   ")


def create_vlan_graph(request, vlanid, family=4):
    """Create graph for this vlan"""

    try:
        vlan = Vlan.objects.get(pk=vlanid)
    except Vlan.DoesNotExist:
        return None

    try:
        family = int(family)
    except ValueError:
        family = 4

    timeframe = request.GET.get('timeframe', 'day')

    extra = {'where': ['family(netaddr) = %s' % family]}
    prefixes = sorted(vlan.prefix_set.all().extra(**extra),
                      key=methodcaller('get_prefix_size'),
                      reverse=True)

    if not prefixes:
        return HttpResponse(status=503)

    options = {'-v': 'IP-addresses', '-l': '0'}
    graph = Graph(title='Total IPv%s addresses on vlan %s' % (family, vlan),
                  time_frame=timeframe, opts=options)

    stack = False
    ipranges = []
    vnames = []
    for prefix in prefixes:
        rrdfile = RrdFile.objects.get(key='prefix', value=prefix.id)
        ipcount = rrdfile.rrddatasource_set.get(name='ip_count')

        vname = graph.add_datasource(
            ipcount, 'AREA',
            prefix.net_address.ljust(ADDRESS_RESERVED_SPACE), stack)
        add_graph_text(graph, vname)
        vnames.append(vname)

        iprange = rrdfile.rrddatasource_set.get(name='ip_range')
        ipranges.append(graph.add_def(iprange))

        stack = True  # Stack all ip_counts after the first

    if len(prefixes) > 1:
        add_total_text(graph, vnames)

    if family == 4:
        graph.add_cdef('iprange', rpn_sum(ipranges))
        graph.add_graph_element('iprange', draw_as='LINE2')

    graphurl = graph.get_url()
    if graphurl:
        json = simplejson.dumps({'url': graphurl})
        return HttpResponse(json, mimetype='application/json')
    else:
        return HttpResponse(status=500)


def find_gwportprefixes(vlan):
    """Find routers that defines this vlan"""
    gwportprefixes = []
    for prefix in vlan.prefix_set.all():
        gwportprefixes.extend(prefix.gwportprefix_set.filter(
            interface__netbox__category__id__in=['GSW', 'GW']))
    return sorted(gwportprefixes, key=attrgetter('gw_ip'))


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


def add_total_text(graph, vnames):
    """Total all values for all prefixes and print them"""
    graph.add_cdef('total', rpn_sum(vnames))

    # Add 2 to padding to compensate for legend image
    graph.add_argument("COMMENT:%s" %
                       'Total'.ljust(ADDRESS_RESERVED_SPACE + 2))
    graph.add_argument("GPRINT:total:LAST:%s" % r'Now\: %-6.0lf')
    graph.add_argument("GPRINT:total:AVERAGE:%s" % r'Avg\: %-6.0lf')
    graph.add_argument("GPRINT:total:MAX:%s" % r'Max\: %-6.0lf\l')

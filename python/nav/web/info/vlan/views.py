#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
from operator import methodcaller, attrgetter
from functools import partial

from IPy import IP

from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse

from nav.models.manage import Prefix, Vlan
from nav.web.utils import create_title
from nav.metrics.graphs import get_simple_graph_url
from nav.metrics.names import join_series
from nav.metrics.templates import metric_path_for_prefix
from ..forms import SearchForm

_logger = logging.getLogger(__name__)
ADDRESS_RESERVED_SPACE = 18


class VlanSearchForm(SearchForm):
    """Searchform for vlans"""

    def __init__(self, *args, **kwargs):
        super(VlanSearchForm, self).__init__(
            *args, form_action='vlan-index', placeholder='Vlan', **kwargs
        )


def get_path(extra=None):
    """Return breadcrumb list"""
    if not extra:
        extra = []
    return [
        ('Home', '/'),
        ('Search', reverse('info-search')),
        ('Vlan', reverse('vlan-index')),
    ] + extra


def index(request):
    """Controller for vlan landing page and search"""
    vlans = Vlan.objects.none()

    navpath = get_path()
    if "query" in request.GET:
        searchform = VlanSearchForm(request.GET)
        if searchform.is_valid():
            navpath = get_path([('Search for "%s"' % request.GET['query'],)])
            vlans = process_searchform(searchform)
    else:
        searchform = VlanSearchForm()

    _logger.debug(vlans)

    return render(
        request,
        "info/vlan/base.html",
        {
            'navpath': navpath,
            'title': create_title(navpath),
            'form': searchform,
            'vlans': vlans,
        },
    )


def process_searchform(form):
    """Find and return vlans based on searchform"""
    query = form.cleaned_data['query']
    _logger.debug('Processing searchform for vlans with query: %s', query)
    if query is None:
        return Vlan.objects.all()
    else:
        return Vlan.objects.filter(
            Q(vlan__icontains=query)
            | Q(net_type__description__icontains=query)
            | Q(description__icontains=query)
            | Q(net_ident__icontains=query)
        ).order_by("vlan")


def vlan_details(request, vlanid):
    """Render details for a vlan"""
    vlan = get_object_or_404(Vlan, pk=vlanid)
    prefixes = sorted(vlan.prefixes.all(), key=methodcaller('get_prefix_size'))

    has_v6 = False
    has_v4 = False
    for prefix in prefixes:
        version = IP(prefix.net_address).version()
        if version == 6:
            has_v6 = True
        elif version == 4:
            has_v4 = True

    navpath = get_path([(str(vlan), '')])

    return render(
        request,
        'info/vlan/vlandetails.html',
        {
            'vlan': vlan,
            'prefixes': prefixes,
            'gwportprefixes': find_gwportprefixes(vlan),
            'navpath': navpath,
            'has_v4': has_v4,
            'has_v6': has_v6,
            'title': create_title(navpath),
        },
    )


def create_prefix_graph(request, prefixid):
    """Returns a Graphite graph render URL for this prefix"""
    prefix = get_object_or_404(Prefix, pk=prefixid)

    path = partial(metric_path_for_prefix, prefix.net_address)
    ip_count = (
        'alpha(color(cactiStyle(alias(stacked({0}), "IP addresses ")), "green"),0.8)'
    ).format(path('ip_count'))
    ip_range = 'color(cactiStyle(alias({0}, "Max addresses")), "red")'.format(
        path('ip_range')
    )
    mac_count = 'color(cactiStyle(alias({0}, "MAC addresses")), "blue")'.format(
        path('mac_count')
    )

    metrics = [ip_count, mac_count]
    if IP(prefix.net_address).version() == 4:
        metrics.append(ip_range)

    timeframe = "1" + request.GET.get('timeframe', 'day')
    url = get_simple_graph_url(
        metrics, timeframe, title=prefix.net_address, width=397, height=201
    )
    if url:
        return redirect(url)
    else:
        return HttpResponse(status=500)


def create_vlan_graph(request, vlanid, family=4):
    """Returns a JSON response containing a Graphite graph render URL for this
    VLAN.
    """
    timeframe = request.GET.get('timeframe', 'day')
    url = get_vlan_graph_url(vlanid, family, timeframe)

    if url:
        return redirect(url)
    else:
        return HttpResponse(status=500)


def get_vlan_graph_url(vlanid, family=4, timeframe="day"):
    """Returns a Graphite graph render URL for a VLAN"""
    vlan = get_object_or_404(Vlan, pk=vlanid)
    try:
        family = int(family)
    except ValueError:
        family = 4

    extra = {'where': ['family(netaddr) = %s' % family]}
    prefixes = sorted(
        vlan.prefixes.all().extra(**extra),
        key=methodcaller('get_prefix_size'),
        reverse=True,
    )
    if not prefixes:
        return None

    metrics = _vlan_metrics_from_prefixes(prefixes, family)
    return get_simple_graph_url(
        metrics,
        "1" + timeframe,
        title="Total IPv{0} addresses on VLAN {1}".format(family, vlan),
        width=597,
        height=251,
    )


def _vlan_metrics_from_prefixes(prefixes, ip_version):
    metrics = []
    ip_ranges = []
    ip_counts = []
    for prefix in prefixes:
        ip_count = metric_path_for_prefix(prefix.net_address, 'ip_count')
        ip_range = metric_path_for_prefix(prefix.net_address, 'ip_range')
        ip_counts.append(ip_count)
        ip_ranges.append(ip_range)
        series = 'alpha(stacked(cactiStyle(alias({0}, "{1}"))),0.8)'.format(
            ip_count, prefix.net_address
        )
        series = (
            r'aliasSub(aliasSub(aliasSub({0},"stacked",""),' r'"\(",""),"\)","")'
        ).format(series)
        metrics.append(series)

    if ip_version == 4:
        series = 'alias(color(sumSeries({0}), "red"), "MAX")'.format(
            join_series(ip_ranges)
        )
        metrics.append(series)

    if len(prefixes) > 1:
        series = 'color(cactiStyle(alias(sumSeries({0}), "Total")), "00000000")'
        series = series.format(join_series(ip_counts))
        metrics.append(series)

    return metrics


def find_gwportprefixes(vlan):
    """Find routers that defines this vlan"""
    gwportprefixes = []
    for prefix in vlan.prefixes.all():
        gwportprefixes.extend(
            prefix.gwport_prefixes.filter(
                interface__netbox__category__id__in=['GSW', 'GW']
            )
        )
    return sorted(gwportprefixes, key=attrgetter('gw_ip'))

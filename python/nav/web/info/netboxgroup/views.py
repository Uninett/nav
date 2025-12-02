#
# Copyright (C) 2013-2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Views for the netbox groups"""

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.urls import reverse

from nav.web.info.forms import SearchForm
from nav.web.info.views import get_path
from nav.web.utils import create_title
from nav.models.manage import NetboxGroup, Netbox, NetboxCategory
from nav.metrics.data import get_netboxes_availability
from nav.metrics.errors import GraphiteUnreachableError


class NetboxGroupForm(SearchForm):
    """Form for searching for netbox groups"""

    def __init__(self, *args, **kwargs):
        super(NetboxGroupForm, self).__init__(
            *args, form_action='netbox-group', placeholder='Device group', **kwargs
        )


def get_netboxgroup_path(other=None):
    """Get path for this page

    :param other: more paths to append
    :type other: list

    """
    navpath = get_path() + [('Device Groups', reverse('netbox-group'))]
    if other:
        navpath += other
    return navpath


def index(request):
    """Renders the default view for the netbox group page

    :param request:
    :type request: django.http.HttpRequest

    """

    navpath = get_netboxgroup_path()
    groups = NetboxGroup.objects.none()

    if request.method == 'GET' and 'query' in request.GET:
        form = NetboxGroupForm(request.GET)
        if form.is_valid():
            query = request.GET['query']
            id_filter = Q(pk__icontains=query)
            netbox_filter = Q(netboxes__sysname__icontains=query)
            description_filter = Q(description__icontains=query)
            groups = (
                NetboxGroup.objects.filter(
                    id_filter | netbox_filter | description_filter
                )
                .distinct()
                .order_by('id')
            )
    else:
        form = NetboxGroupForm()
        groups = NetboxGroup.objects.all()

    if request.htmx:
        return render(
            request,
            'info/netboxgroup/_search_results.html',
            {'netboxgroups': groups, 'searchform': form},
        )

    return render(
        request,
        'info/netboxgroup/list_groups.html',
        {
            'netboxgroups': groups,
            'searchform': form,
            'navpath': navpath,
            'title': create_title(navpath),
        },
    )


def group_detail(request, groupid):
    """Renders the view for group detail

    :param request:
    :type request: django.http.HttpRequest

    """
    group = get_object_or_404(NetboxGroup, pk=groupid)
    netboxes = group.netboxes.select_related('organization', 'category', 'type')
    availabilities = {}
    graphite_error = False

    try:
        availabilities = get_netboxes_availability(
            netboxes, data_sources=['availability'], time_frames=['week', 'month']
        )
    except GraphiteUnreachableError:
        graphite_error = True

    navpath = get_netboxgroup_path([(group.pk,)])

    return render(
        request,
        'info/netboxgroup/group_detail.html',
        {
            'netboxgroup': group,
            'netboxes': netboxes,
            'availabilities': availabilities,
            'navpath': navpath,
            'title': create_title(navpath),
            'graphite_error': graphite_error,
        },
    )


def group_edit(request, groupid):
    """Renders the view for editing device groups

    :param request:
    :type request: django.http.HttpRequest

    """

    group = get_object_or_404(NetboxGroup, pk=groupid)
    navpath = get_netboxgroup_path([(group.pk,), ('edit',)])

    if request.method == 'POST':
        return handle_edit_request(request, group)

    netboxes = Netbox.objects.exclude(
        pk__in=group.netboxes.all().values_list('id', flat=True)
    )

    return render(
        request,
        'info/netboxgroup/group_edit.html',
        {
            'netboxgroup': group,
            'netboxes': netboxes,
            'navpath': navpath,
            'title': create_title(navpath),
        },
    )


def handle_edit_request(request, group):
    """Store new netbox categories and remove old ones

    :param group:
    :type group: nav.models.manage.NetboxGroup

    :param request:
    :type request: django.http.HttpRequest

    """
    netboxids = [int(x) for x in request.POST.getlist('netboxes')]

    # Delete existing netboxcategories that are not in request
    NetboxCategory.objects.filter(category=group).exclude(
        netbox__pk__in=netboxids
    ).delete()

    # Add new netboxcategories that are in request
    for netboxid in netboxids:
        try:
            NetboxCategory.objects.get(category=group, netbox__pk=netboxid)
        except NetboxCategory.DoesNotExist:
            netbox = Netbox.objects.get(pk=netboxid)
            NetboxCategory.objects.create(category=group, netbox=netbox)

    return redirect('netbox-group')

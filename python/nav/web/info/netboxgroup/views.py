#
# Copyright (C) 2013 UNINETT AS
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
"""Views for the netbox groups"""

from django.shortcuts import render, redirect
from django.db.models import Q

from nav.web.info.netboxgroup.forms import NetboxGroupForm
from nav.models.manage import NetboxGroup, Netbox, NetboxCategory


def index(request):
    """Renders the default view for the netbox group page

    :param request:
    :type request: django.http.HttpRequest

    """

    groups = NetboxGroup.objects.none()

    if request.method == 'GET' and 'query' in request.GET:
        form = NetboxGroupForm(request.GET)
        if form.is_valid():
            query = request.GET['query']
            id_filter = Q(pk__icontains=query)
            netbox_filter = Q(netbox__sysname__icontains=query)
            groups = NetboxGroup.objects.filter(
                id_filter | netbox_filter).distinct().order_by('id')
    else:
        form = NetboxGroupForm()
        groups = NetboxGroup.objects.all()

    return render(request, 'info/netboxgroup/list_groups.html',
                  {'netboxgroups': groups,
                   'searchform': form})


def edit_group(request, groupid):
    """Renders the view for editing device groups

    :param request:
    :type request: django.http.HttpRequest

    """
    group = NetboxGroup.objects.get(pk=groupid)

    if request.method == 'POST':
        return handle_edit_request(request, group)

    netboxes = Netbox.objects.exclude(
        pk__in=group.netbox_set.all().values_list('id', flat=True))

    return render(request, 'info/netboxgroup/edit_group.html',
                  {'netboxgroup': group, 'netboxes': netboxes})


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
        netbox__pk__in=netboxids).delete()

    # Add new netboxcategories that are in request
    for netboxid in netboxids:
        try:
            NetboxCategory.objects.get(category=group, netbox__pk=netboxid)
        except NetboxCategory.DoesNotExist:
            netbox = Netbox.objects.get(pk=netboxid)
            NetboxCategory.objects.create(category=group, netbox=netbox)

    return redirect('netbox-group')

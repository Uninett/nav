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

from django.shortcuts import render
from django.db.models import Q

from nav.web.info.netboxgroup.forms import NetboxGroupForm, NetboxSelectForm
from nav.models.manage import NetboxGroup, Netbox


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
    group = NetboxGroup.objects.get(pk=groupid)
    netboxform = NetboxSelectForm()
    netboxform.fields['netboxes'].choices = [(x.pk, x.sysname) for x in
                                             Netbox.objects.all()]
    netboxform.fields['netboxes'].initial = [x.pk for x in
                                             group.netbox_set.all()]

    return render(request, 'info/netboxgroup/edit_group.html',
                  {'netboxgroup': group, 'netboxform': netboxform})

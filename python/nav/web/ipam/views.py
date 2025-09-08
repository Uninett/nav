# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Uninett AS
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

from django.shortcuts import render
from nav.models.manage import NetType, Organization, Usage, Prefix
from nav.web.modals import render_modal

NAVBAR = [('Home', '/'), ('IPAM', None)]
DEFAULT_VALUES = {'title': "IPAM", 'navpath': NAVBAR}


def index(request):
    ctx = generate_context()
    return render(request, "ipam/index.html", ctx)


def matrix(request):
    ctx = {}
    return render(request, "ipam/matrix.html", ctx)


def subnet_allocator_help_modal(request):
    """Render a modal with help information about the subnet allocator."""
    return render_modal(
        request,
        "ipam/includes/_subnet_diagram_help_modal.html",
        modal_id="allocator-help-modal",
        size="large",
    )


def generate_context():
    scopes = Prefix.objects.filter(vlan__net_type='scope')
    ctx = {
        "net_types": NetType.objects.exclude(vlans__net_type__in=["scope", "reserved"]),
        "organizations": Organization.objects.all,
        "usages": Usage.objects.all,
        "has_registered_scopes": scopes.count() > 0,
    }
    ctx.update(DEFAULT_VALUES)
    return ctx

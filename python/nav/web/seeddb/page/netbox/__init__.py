# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Controllers for the netbox part of seedDB"""
import datetime
from django.db import transaction
from django.contrib.postgres.aggregates import ArrayAgg

from nav.models.manage import Netbox
from nav.bulkparse import NetboxBulkParser
from nav.bulkimport import NetboxImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.move import move
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.page.netbox.forms import NetboxFilterForm, NetboxMoveForm


class NetboxInfo(SeeddbInfo):
    """Variable container"""
    active = {'netbox': True}
    caption = 'IP Devices'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'IP Devices'
    verbose_name = Netbox._meta.verbose_name
    _navpath = [('IP Devices', reverse_lazy('seeddb-netbox'))]
    delete_url = reverse_lazy('seeddb-netbox')
    back_url = reverse_lazy('seeddb-netbox')
    add_url = reverse_lazy('seeddb-netbox-edit')
    bulk_url = reverse_lazy('seeddb-netbox-bulk')


def netbox(request):
    """Controller for landing page for netboxes"""
    return view_switcher(request, list_view=netbox_list,
                         move_view=netbox_move, delete_view=netbox_delete)


def netbox_list(request):
    """Controller for showing all netboxes"""
    info = NetboxInfo()
    query = (
        Netbox.objects.select_related("room", "category", "type", "organization")
        .prefetch_related("profiles")
        .annotate(profile=ArrayAgg("profiles__name"))
    )
    filter_form = NetboxFilterForm(request.GET)
    value_list = ('sysname', 'room', 'ip', 'category', 'organization', 'profile',
                  'type__name')
    return render_list(request, query, value_list, 'seeddb-netbox-edit',
                       edit_url_attr='pk',
                       filter_form=filter_form,
                       template='seeddb/list_netbox.html',
                       extra_context=info.template_context)


def netbox_delete(request):
    """Controller for handling a request for deleting a netbox"""
    info = NetboxInfo()
    return render_delete(request, Netbox, 'seeddb-netbox',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context,
                         pre_delete_operation=netbox_pre_deletion_mark,
                         delete_operation=None)


@transaction.atomic
def netbox_pre_deletion_mark(queryset):
    """Marks all netboxes in a queryset as undergoing deletion.

    :type queryset: django.db.models.QuerySet
    """
    queryset.update(deleted_at=datetime.datetime.now(), up_to_date=False)


def netbox_move(request):
    """Controller for handling a move request"""
    info = NetboxInfo()
    return move(request, Netbox, NetboxMoveForm, 'seeddb-netbox',
                title_attr='sysname', extra_context=info.template_context)


def netbox_bulk(request):
    """Controller for bulk importing netboxes"""
    info = NetboxInfo()
    return render_bulkimport(request, NetboxBulkParser, NetboxImporter,
                             'seeddb-netbox',
                             extra_context=info.template_context)

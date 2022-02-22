#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Module comment"""
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
# Copyright (C) 2022 Sikt
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

import logging
from django.http import JsonResponse
from nav.models.manage import NetboxGroup, Netbox
from nav.bulkparse import NetboxGroupBulkParser
from nav.bulkimport import NetboxGroupImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.forms import DeviceGroupForm

_logger = logging.getLogger(__name__)


class NetboxGroupInfo(SeeddbInfo):
    active = {'netboxgroup': True}
    caption = 'Device Groups'
    verbose_name = NetboxGroup._meta.verbose_name
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Device Groups'
    _navpath = [('Device Groups', reverse_lazy('seeddb-netboxgroup'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-netboxgroup')
    delete_url_name = 'seeddb-netboxgroup-delete'
    back_url = reverse_lazy('seeddb-netboxgroup')
    add_url = reverse_lazy('seeddb-netboxgroup-edit')
    bulk_url = reverse_lazy('seeddb-netboxgroup-bulk')


def netboxgroup(request):
    return view_switcher(
        request,
        list_view=netboxgroup_list,
        move_view=not_implemented,
        delete_view=netboxgroup_delete,
    )


def netboxgroup_list(request):
    info = NetboxGroupInfo()
    query = NetboxGroup.objects.all()
    value_list = ('id', 'description')
    return render_list(
        request,
        query,
        value_list,
        'seeddb-netboxgroup-edit',
        extra_context=info.template_context,
    )


def netboxgroup_delete(request, object_id=None):
    info = NetboxGroupInfo()
    return render_delete(
        request,
        NetboxGroup,
        'seeddb-netboxgroup',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context,
        object_id=object_id,
    )


def netboxgroup_edit(request, netboxgroup_id=None):
    if netboxgroup_id:
        detail_page_url = reverse_lazy(
            'netbox-group-detail', kwargs={'groupid': netboxgroup_id}
        )
    else:
        detail_page_url = ""
    info = NetboxGroupInfo()
    extra_context = {
        'detail_page_url': detail_page_url,
    }
    extra_context.update(info.template_context)
    return render_edit(
        request,
        NetboxGroup,
        DeviceGroupForm,
        netboxgroup_id,
        'seeddb-netboxgroup-edit',
        template='seeddb/edit_device_group.html',
        extra_context=extra_context,
    )


def netboxgroup_bulk(request):
    info = NetboxGroupInfo()
    return render_bulkimport(
        request,
        NetboxGroupBulkParser,
        NetboxGroupImporter,
        'seeddb-netboxgroup',
        extra_context=info.template_context,
    )

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

from nav.models.service import Service
from nav.bulkparse import ServiceBulkParser
from nav.bulkimport import ServiceImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.bulk import render_bulkimport


class ServiceInfo(SeeddbInfo):
    active = {'service': True}
    caption = 'Services'
    tab_template = 'seeddb/tabs_generic.html'
    verbose_name = Service._meta.verbose_name
    _title = 'Services'
    _navpath = [('Services', reverse_lazy('seeddb-service'))]
    delete_url = reverse_lazy('seeddb-service')
    delete_url_name = 'seeddb-service-delete'
    back_url = reverse_lazy('seeddb-service')
    add_url = reverse_lazy('seeddb-service-edit')
    bulk_url = reverse_lazy('seeddb-service-bulk')
    hide_move = True


def service(request):
    return view_switcher(request,
                         list_view=service_list,
                         move_view=not_implemented,
                         delete_view=service_delete)


def service_list(request):
    info = ServiceInfo()
    query = Service.objects.all()
    value_list = ('netbox__sysname', 'handler', 'version')
    return render_list(request, query, value_list, 'seeddb-service-edit',
                       extra_context=info.template_context,
                       add_descriptions=True)


def service_delete(request, object_id=None):
    info = ServiceInfo()
    return render_delete(request, Service, 'seeddb-service',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context,
                         object_id=object_id)


def service_bulk(request):
    info = ServiceInfo()
    return render_bulkimport(
        request, ServiceBulkParser, ServiceImporter,
        'seeddb-service',
        extra_context=info.template_context)

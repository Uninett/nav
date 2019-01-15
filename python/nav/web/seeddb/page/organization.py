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

from django.shortcuts import render

from nav.models.manage import Organization
from nav.bulkparse import OrgBulkParser
from nav.bulkimport import OrgImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.move import move

from ..forms import OrganizationForm, OrganizationMoveForm


class OrganizationInfo(SeeddbInfo):
    active_page = 'organization'
    active = {active_page: True}
    caption = "{}s".format(active_page.capitalize())
    _title = caption
    tab_template = 'seeddb/tabs_generic.html'
    verbose_name = Organization._meta.verbose_name
    _navpath = [('Organizations', reverse_lazy('seeddb-organization'))]
    delete_url = reverse_lazy('seeddb-organization')
    back_url = reverse_lazy('seeddb-organization')
    add_url = reverse_lazy('seeddb-organization-edit')
    bulk_url = reverse_lazy('seeddb-organization-bulk')


def organization(request):
    return view_switcher(request,
                         list_view=organization_list,
                         move_view=organization_move,
                         delete_view=organization_delete)


def organization_list(request):
    info = OrganizationInfo()
    context = info.template_context
    context.update({
        'roots': Organization.objects.filter(parent=None).order_by('id'),
        'edit_url_name': 'seeddb-organization-edit'
    })
    return render(request, 'seeddb/list_tree.html', context)


def organization_move(request):
    info = OrganizationInfo()
    return move(request, Organization, OrganizationMoveForm,
                'seeddb-organization',
                extra_context=info.template_context)


def organization_delete(request):
    info = OrganizationInfo()
    return render_delete(request, Organization, 'seeddb-organization',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context)


def organization_edit(request, organization_id=None):
    info = OrganizationInfo()
    return render_edit(request, Organization, OrganizationForm,
                       organization_id, 'seeddb-organization-edit',
                       extra_context=info.template_context)


def organization_bulk(request):
    info = OrganizationInfo()
    return render_bulkimport(
        request, OrgBulkParser, OrgImporter,
        'seeddb-organization',
        extra_context=info.template_context)

# -*- coding: utf-8 -*-
#
# Copyright (C) 2017, 2019 UNINETT AS
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
"""Forms and view functions for SeedDB's Management Profile view"""
from ..forms import ManagementProfileForm, ManagementProfileFilterForm

from nav.models.manage import ManagementProfile
from nav.bulkparse import ManagementProfileBulkParser
from nav.bulkimport import ManagementProfileImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.bulk import render_bulkimport


class ManagementProfileInfo(SeeddbInfo):
    """Management Profile info object"""
    active = {'management_profile': True}
    caption = 'Management Profile'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Management Profiles'
    verbose_name = ManagementProfile._meta.verbose_name
    _navpath = [('Management Profiles',
                 reverse_lazy('seeddb-management-profile'))]
    delete_url = reverse_lazy('seeddb-management-profile')
    back_url = reverse_lazy('seeddb-management-profile')
    add_url = reverse_lazy('seeddb-management-profile-edit')
    bulk_url = reverse_lazy('seeddb-management-profile-bulk')
    hide_move = True


def management_profile(request):
    """Controller for listing, moving and deleting management profiles"""
    return view_switcher(request,
                         list_view=management_profile_list,
                         delete_view=management_profile_delete)


def management_profile_list(request):
    """Controller for listing management profiles. Used in
    management_profile()"""
    info = ManagementProfileInfo()
    value_list = (
        'name', 'description', 'get_protocol_display')
    query = ManagementProfile.objects.all()
    filter_form = ManagementProfileFilterForm(request.GET)
    return render_list(request, query, value_list,
                       'seeddb-management-profile-edit',
                       filter_form=filter_form,
                       extra_context=info.template_context)


def management_profile_delete(request):
    """Controller for deleting management profiles. Used in
    management_profile()"""
    info = ManagementProfileInfo()
    return render_delete(request, ManagementProfile,
                         'seeddb-management-profile',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context)


def management_profile_edit(request, management_profile_id=None):
    """Controller for editing a management profile"""
    info = ManagementProfileInfo()
    return render_edit(request, ManagementProfile, ManagementProfileForm,
                       management_profile_id,
                       'seeddb-management-profile-edit',
                       extra_context=info.template_context)


def management_profile_bulk(request):
    """Controller for bulk editing management profiles"""
    info = ManagementProfileInfo()
    return render_bulkimport(
        request, ManagementProfileBulkParser, ManagementProfileImporter,
        'seeddb-management-profile',
        extra_context=info.template_context)

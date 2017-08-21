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
"""Forms and view functions for SeedDB's Connection Profile view"""
from ..forms import ConnectionProfileForm, ConnectionProfileFilterForm

from nav.models.manage import ConnectionProfile
from nav.bulkparse import ConnectionProfileBulkParser
from nav.bulkimport import ConnectionProfileImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.bulk import render_bulkimport


class ConnectionProfileInfo(SeeddbInfo):
    """Connection Profile info object"""
    active = {'connection_profile': True}
    caption = 'Connection Profile'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Connection Profiles'
    verbose_name = ConnectionProfile._meta.verbose_name
    _navpath = [('Connection Profiles',
                 reverse_lazy('seeddb-connection-profile'))]
    delete_url = reverse_lazy('seeddb-connection-profile')
    back_url = reverse_lazy('seeddb-connection-profile')
    add_url = reverse_lazy('seeddb-connection-profile-edit')
    bulk_url = reverse_lazy('seeddb-connection-profile-bulk')
    hide_move = True


def connection_profile(request):
    """Controller for listing, moving and deleting connection profiles"""
    return view_switcher(request,
                         list_view=connection_profile_list,
                         delete_view=connection_profile_delete)


def connection_profile_list(request):
    """Controller for listing connection_profiles. Used in
    connection_profile()"""
    info = ConnectionProfileInfo()
    value_list = (
        'name', 'description', 'get_protocol_display')
    query = ConnectionProfile.objects.all()
    filter_form = ConnectionProfileFilterForm(request.GET)
    return render_list(request, query, value_list,
                       'seeddb-connection-profile-edit',
                       filter_form=filter_form,
                       extra_context=info.template_context)


def connection_profile_delete(request):
    """Controller for deleting connection profiles. Used in
    connection_profile()"""
    info = ConnectionProfileInfo()
    return render_delete(request, ConnectionProfile,
                         'seeddb-connection-profile',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context)


def connection_profile_edit(request, connection_profile_id=None):
    """Controller for editing a connection profile"""
    info = ConnectionProfileInfo()
    return render_edit(request, ConnectionProfile, ConnectionProfileForm,
                       connection_profile_id,
                       'seeddb-connection-profile-edit',
                       extra_context=info.template_context)


def connection_profile_bulk(request):
    """Controller for bulk editing connection profiles"""
    info = ConnectionProfileInfo()
    return render_bulkimport(
        request, ConnectionProfileBulkParser, ConnectionProfileImporter,
        'seeddb-connection-profile',
        extra_context=info.template_context)

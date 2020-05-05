# -*- coding: utf-8 -*-
#
# Copyright (C) 2017, 2019 Uninett AS
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
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from nav.models.manage import ManagementProfile
from nav.bulkparse import ManagementProfileBulkParser
from nav.bulkimport import ManagementProfileImporter
from nav.web.message import new_message, Messages

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.bulk import render_bulkimport

from nav.web.seeddb.page.management_profile.forms import (
    ManagementProfileFilterForm,
    ManagementProfileForm,
)


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
    delete_url_name = 'seeddb-management-profile-delete'
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
                       edit_url='seeddb-management-profile-edit',
                       filter_form=filter_form,
                       extra_context=info.template_context)


def management_profile_delete(request, object_id=None):
    """Controller for deleting management profiles. Used in
    management_profile()"""
    info = ManagementProfileInfo()
    return render_delete(request, ManagementProfile,
                         redirect='seeddb-management-profile',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context,
                         object_id=object_id)


def management_profile_edit(request, management_profile_id=None):
    """Controller for editing a management profile.

    The basic profile details are handled by the ManagementProfileForm. Protocol
    specific configuration is stored in a JSONField, and the responsibility of
    constructing this JSON structure is delegated to protocol-specific sub-forms.

    Because of the more complicated handling of forms in this view, the standard
    render_edit() function of SeedDB is eschewed. This leads to some redundancies
    that can potentially be factored out whenever the mess that is SeedDB is
    refactored or rewritten.

    """
    try:
        profile = ManagementProfile.objects.get(id=management_profile_id)
    except ManagementProfile.DoesNotExist:
        profile = None

    verbose_name = ManagementProfile._meta.verbose_name

    if request.method == 'POST':
        form = ManagementProfileForm(request.POST, instance=profile)
        if form.is_valid():
            protocol_form = form.get_protocol_form_class()(
                request.POST,
                instance=form.instance,
            )
            if protocol_form.is_valid():
                profile = form.save()

                new_message(
                    request,
                    "Saved %s %s" % (verbose_name, profile),
                    Messages.SUCCESS
                )
                return HttpResponseRedirect(
                    reverse('seeddb-management-profile-edit', args=(profile.pk,))
                )
        protocol_forms = [
            f(request.POST, instance=profile)
            for f in form.get_protocol_forms()
        ]
    else:
        form = ManagementProfileForm(instance=profile)
        protocol_forms = [f(instance=profile) for f in form.get_protocol_forms()]

    context = {
        'object': profile,
        'form': form,
        'protocol_forms': protocol_forms,
        'title': 'Add new %s' % verbose_name,
        'verbose_name': verbose_name,
        'sub_active': {'add': True},
    }
    if profile and profile.pk:
        context.update({
            'title': 'Edit %s "%s"' % (verbose_name, profile),
            'sub_active': {'edit': True},
        })

    template_context = ManagementProfileInfo().template_context
    template_context.update(context)
    return render(request, 'seeddb/management-profile/edit.html', template_context)


def management_profile_bulk(request):
    """Controller for bulk editing management profiles"""
    info = ManagementProfileInfo()
    return render_bulkimport(
        request, ManagementProfileBulkParser, ManagementProfileImporter,
        redirect='seeddb-management-profile',
        extra_context=info.template_context)

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
"""Module containing everything regarding patches in SeedDB"""

import logging

from django import forms
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from nav.models.cabling import Patch, Cabling
from nav.models.manage import Netbox, Interface, Room
from nav.bulkparse import PatchBulkParser
from nav.bulkimport import PatchImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete


_logger = logging.getLogger(__name__)


class PatchInfo(SeeddbInfo):
    """Class for storing meta information related to patches in SeedDB"""
    active = {'patch': True}
    active_page = 'patch'
    documentation_url = '/doc/reference/cabling_and_patch.html'
    caption = 'Patch'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Patch'
    verbose_name = Patch._meta.verbose_name
    _navpath = [('Patch', reverse_lazy('seeddb-patch'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-patch')
    delete_url_name = 'seeddb-patch-delete'
    back_url = reverse_lazy('seeddb-patch')
    add_url = reverse_lazy('seeddb-patch-edit')
    bulk_url = reverse_lazy('seeddb-patch-bulk')


class PatchForm(forms.ModelForm):
    """Form for editing and creating patches"""

    class Meta(object):
        model = Patch
        fields = '__all__'


def patch(request):
    """Creates a view switcher containing the appropriate views"""
    return view_switcher(request,
                         list_view=patch_list,
                         move_view=not_implemented,
                         delete_view=patch_delete)


def patch_list(request):
    """The view used when listing all patches"""
    query = Patch.objects.none()
    info = PatchInfo()
    value_list = (
        'cabling__room', 'interface__netbox__sysname', 'interface__ifname',
        'interface__ifalias', 'cabling__jack', 'split')

    context = info.template_context
    context.update({
        'rooms': Room.objects.all(),
        'netboxes': Netbox.objects.all()
    })
    return render_list(request, query, value_list, 'seeddb-patch-edit',
                       template='seeddb/list_patches.html',
                       extra_context=context)


def patch_delete(request, object_id=None):
    """The view used when deleting patches"""
    info = PatchInfo()
    return render_delete(request, Patch, 'seeddb-patch',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context,
                         object_id=object_id)


def patch_edit(request):
    """Renders gui for editing patches"""
    context = PatchInfo().template_context

    try:
        netbox = Netbox.objects.get(pk=request.GET.get('netboxid'))
    except (ValueError, Netbox.DoesNotExist):
        netbox = Netbox.objects.none()
        cables = Cabling.objects.none()
    else:
        cables = Cabling.objects.filter(room=netbox.room)

    context.update({
        'netboxes': Netbox.objects.all(),
        'netbox': netbox,
        'cables': cables
    })

    return render(request, 'seeddb/edit_patch.html', context)


@require_POST
def patch_save(request):
    """Save a patch"""
    interface = get_object_or_404(Interface, pk=request.POST.get('interfaceid'))
    cable = get_object_or_404(Cabling, pk=request.POST.get('cableid'))
    split = request.POST.get('split', '')
    _logger.debug('Creating patch for interface %s and cable %s',
                  interface, cable)

    try:
        Patch.objects.create(interface=interface, cabling=cable, split=split)
    except Exception as error:
        _logger.debug(error)
        return HttpResponse(error, status=500)

    return HttpResponse()


@require_POST
def patch_remove(request):
    """Remove all patches from an interface"""
    interface = get_object_or_404(Interface, pk=request.POST.get('interfaceid'))
    Patch.objects.filter(interface=interface).delete()
    return HttpResponse()


def patch_bulk(request):
    """The view used when bulk importing patches"""
    info = PatchInfo()
    return render_bulkimport(
        request, PatchBulkParser, PatchImporter,
        'seeddb-patch',
        extra_context=info.template_context)


def load_cell(request):
    """Renders patches for an interface"""
    interface = Interface.objects.get(pk=request.GET.get('interfaceid'))
    return render(request, 'seeddb/fragments/patches.html', {
        'interface': interface
    })

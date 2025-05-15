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
"""Module for handling bulk import requests"""

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from nav.bulkimport import reset_object_foreignkeys
from nav.bulkparse import BulkParseError
from nav.web.message import Messages
from nav.web.seeddb.forms.bulk import BulkImportForm


def render_bulkimport(request, parser_cls, importer_cls, redirect, extra_context=None):
    """Renders the bulkimport interface"""
    extra_context = extra_context or {}
    processed = []
    if request.method == 'POST':
        form = BulkImportForm(parser_cls, request.POST, request.FILES)
        if form.is_valid():
            confirm = request.POST.get('confirm', False)
            parser = form.get_parser()
            importer = importer_cls(parser)

            if confirm:
                saved = bulk_save(importer)
                post_save_message(request, saved)
                return HttpResponseRedirect(reverse(redirect))
            else:
                processed = form.bulk_process_check(importer)
    else:
        form = BulkImportForm(parser_cls)

    info_dict = {
        'form': form,
        'processed_objects': processed,
        'sub_active': {'bulk': True},
    }
    info_dict.update(extra_context)
    return render(request, 'seeddb/bulk_import.html', info_dict)


def bulk_save(importer):
    """Saves the bulk data stored in the importer"""
    saved = []
    for _, objects in importer:
        if not isinstance(objects, BulkParseError):
            for obj in objects:
                reset_object_foreignkeys(obj)
                obj.save()
            saved.append(objects)
    return saved


def post_save_message(request, saved):
    """Displays information to the user about what was imported"""
    messages = Messages(request)
    for objects in saved:
        for obj in objects:
            msg = "Saved %s %s " % (obj._meta.verbose_name, obj)
            messages.append({'message': msg, 'type': Messages.SUCCESS})
    messages.save()

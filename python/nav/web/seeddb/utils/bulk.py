# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from nav.bulkimport import reset_object_foreignkeys
from nav.bulkparse import BulkParseError
from nav.web.message import Messages

def render_bulkimport(request, parser_cls, importer_cls, redirect, extra_context=None):
    extra_context = extra_context or {}
    data = None
    processed = []
    if request.method == 'POST':
        confirm = request.POST.get('confirm', False)
        data = bulk_post_data(request)
        parser = parser_cls(data)
        importer = importer_cls(parser)

        if confirm:
            saved = bulk_save(importer)
            post_save_message(request, saved)
            return HttpResponseRedirect(reverse(redirect))
        else:
            processed = bulk_process_check(importer)

    info_dict = {
        'bulk_data': data,
        'import_header': parser_cls.get_header(),
        'processed_objects': processed,
        'sub_active': {'bulk': True},
    }
    info_dict.update(extra_context)
    return render_to_response(
        'seeddb/bulk_import.html',
        info_dict,
        RequestContext(request)
    )

def bulk_post_data(request):
    data = request.POST.get('bulk_data')
    if isinstance(data, unicode):
        data = data.encode('utf-8')
    return data

def bulk_process_check(importer):
    processed = []
    for line_num, objects in importer:
        if isinstance(objects, BulkParseError):
            processed.append({
                'type': 'error',
                'line_number': line_num,
                'message': [objects],
            })
        else:
            processed.append({
                'type': 'ok',
                'line_number': line_num,
                'message': ["%s: %s" % (obj._meta.verbose_name, obj) for obj in objects],
            })
    return processed

def bulk_save(importer):
    saved = []
    for line_num, objects in importer:
        if not isinstance(objects, BulkParseError):
            for obj in objects:
                reset_object_foreignkeys(obj)
                obj.save()
            saved.append(objects)
    return saved

def post_save_message(request, saved):
    messages = Messages(request._req)
    for objects in saved:
        for obj in objects:
            msg = "Saved %s %s " % (obj._meta.verbose_name, obj)
            messages.append({'message': msg, 'type': Messages.SUCCESS})
    messages.save()

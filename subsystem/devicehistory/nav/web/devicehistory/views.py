# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

import time
from datetime import date
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from nav.django.shortcuts import render_to_response, object_list
from nav.models.manage import Room, Location, Netbox, Module
from nav.models.event import AlertHistory, AlertHistoryVariable, AlertType, EventType
from nav.web.templates.DeviceHistoryTemplate import DeviceHistoryTemplate
from nav.web.quickselect import QuickSelect

from nav.web.devicehistory.utils.history import History
from nav.web.devicehistory.utils.error import RegisterEvent

DeviceQuickSelect_kwargs = {
    'button': 'View %s history',
    'module': True,
    'netbox_multiple': False,
    'module_multiple': False,
    'netbox_label': '%(sysname)s [%(ip)s - %(device__serial)s]',
}
DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_kwargs)

def devicehistory_search(request):
    info_dict = {
        'active': {'devicehistory': True},
        'quickselect': DeviceQuickSelect,
    }
    return render_to_response(
       DeviceHistoryTemplate,
       'devicehistory/history_search.html',
       info_dict,
   );

def devicehistory_view(request):
    if not request.method == 'POST':
        pass

    from_date = request.POST.get('from_date', date.fromtimestamp(time.time() - 7 * 24 * 60 * 60))
    to_date = request.POST.get('to_date', date.today())
    type = request.POST.get('type', None)

    # FIXME check that date is a valid "yyyy-mm-dd" string

    selection = DeviceQuickSelect.handle_post(request)
    params = {
        'selection': selection,
        'start_time': from_date,
        'end_time': to_date,
        'types': [type],
    }
    history = History(**params)

    info_dict = {
        'active': {'devicehistory': True},
        'history': history.history,
        'selection': selection,
        'selected_type': type,
        'event_type': EventType.objects.all().order_by('id'),
        'from_date': from_date,
        'to_date': to_date,
    }
    return render_to_response(
        DeviceHistoryTemplate,
        'devicehistory/history_view.html',
        info_dict,
    )

def error_form(request):
    if request.method == 'POST':
        return register_error(request)

    info_dict = {
        'active': {'error': True},
        'quickselect': DeviceQuickSelect,
    }
    return render_to_response(
        DeviceHistoryTemplate,
        'devicehistory/register_error.html',
        info_dict,
    );

def register_error(request):
    selection = DeviceQuickSelect.handle_post(request)
    error_comment = request.POST.get('error_comment', None)

    events = RegisterError(selection=selection, comment=error_comment)

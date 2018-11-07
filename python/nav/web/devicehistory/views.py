#
# Copyright (C) 2008-2013 Uninett AS
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
"""Device history UI view functions"""

from operator import attrgetter

from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.models.fields import INFINITY
from nav.models.manage import Netbox, Module
from nav.models.event import AlertHistory
from nav.web.message import new_message, Messages
from nav.web.quickselect import QuickSelect
from nav.web.devicehistory.utils.history import (
    fetch_history, get_messages_for_history, group_history_and_messages,
    describe_search_params, add_descendants)
from nav.web.devicehistory.utils.error import register_error_events
from nav.web.devicehistory.forms import DeviceHistoryViewFilter

DEVICEQUICKSELECT_VIEW_HISTORY_KWARGS = {
    'button': 'View %s history',
    'module': True,
    'netbox_label': '%(sysname)s [%(ip)s - %(device__serial)s]',
}
DEVICEQUICKSELECT_POST_ERROR_KWARGS = {
    'button': 'Add %s error event',
    'location': False,
    'room': False,
    'module': True,
    'netbox_label': '%(sysname)s [%(ip)s - %(device__serial)s]',
}


# Often used timelimits, in seconds:
ONE_DAY = 24 * 3600
ONE_WEEK = 7 * ONE_DAY

HISTORY_PER_PAGE = 100
ORPHANS = 10

_ = lambda a: a


def devicehistory_search(request):
    """Implements the device history landing page / search form"""
    device_quickselect = QuickSelect(**DEVICEQUICKSELECT_VIEW_HISTORY_KWARGS)

    if 'from_date' in request.GET:
        form = DeviceHistoryViewFilter(request.GET)
        if form.is_valid():
            return devicehistory_view(request)
    else:
        form = DeviceHistoryViewFilter()

    info_dict = {
        'active': {'device': True},
        'quickselect': device_quickselect,
        'navpath': [('Home', '/'), ('Device History', '')],
        'title': 'NAV - Device History',
        'form': form
    }
    return render_to_response(
        'devicehistory/history_search.html',
        info_dict,
        RequestContext(request)
    )


def devicehistory_view(request):
    """Device history search results view"""

    selection = {
        'organization': request.GET.getlist('org'),
        'category': request.GET.getlist('cat'),
        'room__location': request.GET.getlist('loc'),
        'room': request.GET.getlist('room'),
        'netbox': request.GET.getlist('netbox'),
        'groups': request.GET.getlist('netboxgroup'),
        'module': request.GET.getlist('module'),
        'mode': request.GET.getlist('mode')
    }

    grouped_history = None
    valid_params = ['to_date', 'from_date', 'eventtype', 'group_by',
                    'netbox', 'room']
    if len(set(valid_params) & set(request.GET.keys())) >= 1:
        form = DeviceHistoryViewFilter(request.GET)
    else:
        form = DeviceHistoryViewFilter()
    if form.is_valid():
        # We need to handle locations as they are tree-based
        selection['room__location'] = add_descendants(
            selection['room__location'])

        alert_history = fetch_history(selection, form)
        grouped_history = group_history_and_messages(
            alert_history,
            get_messages_for_history(alert_history),
            form.cleaned_data['group_by']
        )

        # Quickselect expects 'loc' and not 'location'
        selection['loc'] = selection['room__location']
        del selection['room__location']

    info_dict = {
        'active': {'device': True},
        'search_description': describe_search_params(selection),
        'selection': selection,
        'history': grouped_history,
        'title': 'NAV - Device History',
        'navpath': [
            ('Home', '/'),
            ('Device History', reverse('devicehistory-search')),
        ],
        'form': form
    }
    return render_to_response(
        'devicehistory/history_view.html',
        info_dict,
        RequestContext(request)
    )


def error_form(request):
    """Implements the 'register error event' form"""
    device_quickselect = QuickSelect(**DEVICEQUICKSELECT_POST_ERROR_KWARGS)
    error_comment = request.POST.get('error_comment', "")

    return render_to_response(
        'devicehistory/register_error.html',
        {
            'active': {'error': True},
            'confirm': False,
            'quickselect': device_quickselect,
            'error_comment': error_comment,
            'title': 'NAV - Device History - Register error',
            'navpath': [
                ('Home', '/'),
                ('Register error event', ''),
            ]
        },
        RequestContext(request)
    )


def confirm_error_form(request):
    """Implements confirmation form for device error event registration"""
    selection = {
        'netbox': request.POST.getlist('netbox'),
        'module': request.POST.getlist('module'),
    }

    netbox = Netbox.objects.select_related(
        'netbox'
    ).filter(id__in=selection['netbox'])
    module = Module.objects.filter(id__in=selection['module'])

    return render_to_response(
        'devicehistory/confirm_error.html',
        {
            'active': {'error': True},
            'confirm': True,
            'netbox': netbox,
            'module': module,
            'title': 'NAV - Device History - Confirm error event',
            'navpath': [
                ('Home', '/'),
                ('Register error event',
                 reverse('devicehistory-registererror')),
            ],
        },
        RequestContext(request)
    )


def register_error(request):
    """Registers a device error event posted from a form"""
    selection = {
        'netbox': request.POST.getlist('netbox'),
        'module': request.POST.getlist('module'),
    }
    error_comment = request.POST.get('error_comment', None)
    confirmed = request.POST.get('confirm', False)

    if not selection['netbox'] and not selection['module']:
        new_message(request, _("No devices selected."), Messages.WARNING)
        return error_form(request)
    if not error_comment and not confirmed:
        new_message(request, _("There's no error message supplied. Are you "
                               "sure you want to continue?"),
                    Messages.WARNING)
        return confirm_error_form(request)

    register_error_events(request, selection=selection, comment=error_comment)

    return HttpResponseRedirect(reverse('devicehistory-registererror'))


def delete_module(request):
    """Displays a list of modules that are down, offering to delete selected
    ones from the database.

    Also implements a "confirm deletion" version of the page for the posted
    form.

    """
    if request.method == 'POST':
        module_ids = request.POST.getlist('module')
        history = _get_unresolved_module_states(module_ids)
        confirm_deletion = True
    else:
        confirm_deletion = False
        history = _get_unresolved_module_states()

    result = []
    for alert in history:
        if alert.module:
            result.append({
                'sysname': alert.netbox.sysname,
                'moduleid': alert.module.id,
                'name': alert.module.name,
                'module_number': alert.module.module_number,
                'descr': alert.module.description,
                'start_time': alert.start_time,
            })

    info_dict = {
        'active': {'module': True},
        'confirm_delete': confirm_deletion,
        'modules': result,
        'title': 'NAV - Device History - Delete module',
        'navpath': [('Home', '/'), ('Delete module', '')],
    }
    return render_to_response(
        'devicehistory/delete_module.html',
        info_dict,
        RequestContext(request)
    )


@transaction.atomic()
def do_delete_module(request):
    """Executes an actual database deletion after deletion was confirmed by
    the delete_module() view.

    """
    confirm_delete = request.POST.get('confirm_delete', False)
    if request.method != 'POST' or not confirm_delete:
        return HttpResponseRedirect(reverse('devicehistory-module'))

    module_ids = request.POST.getlist('module')
    history = _get_unresolved_module_states(module_ids)

    if not history:
        new_message(request, _('No modules selected'), Messages.NOTICE)
        return HttpResponseRedirect(reverse('devicehistory-module'))

    new_message(request, _('Deleted selected modules.'), Messages.SUCCESS)

    cursor = connection.cursor()
    module_ids = tuple(h.module.id for h in history)
    # Delete modules using raw sql to avoid Django's simulated cascading.
    # AlertHistory entries will be closed by a database trigger.
    cursor.execute("DELETE FROM module WHERE moduleid IN %s", (module_ids,))

    # Delete the entities representing these modules
    for hist in history:
        cursor.execute(
            "DELETE FROM netboxentity WHERE netboxid = %s and deviceid = %s",
            [hist.module.netbox.id, hist.module.device.id])

    return HttpResponseRedirect(reverse('devicehistory-module'))


def _get_unresolved_module_states(limit_to=None):
    """Returns AlertHistory objects for all modules that are currently down.

    Each AlertHistory object will have an extra module attribute,
    which will be the referenced Module instance.

    """
    history = AlertHistory.objects.select_related(
        'device', 'netbox'
    ).filter(
        event_type__id='moduleState',
        alert_type__name='moduleDown',
        end_time__gte=INFINITY
    ).exclude(
        subid=''
    ).extra(
        select={'module': 'NULL'}
    )

    if limit_to:
        history = history.filter(subid__in=limit_to)

    history = dict((int(h.subid), h) for h in history)
    for module in Module.objects.filter(id__in=history.keys()):
        history[module.id].module = module

    return sorted(history.values(),
                  key=attrgetter('start_time'))

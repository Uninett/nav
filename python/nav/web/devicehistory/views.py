#
# Copyright (C) 2008-2013 Uninett AS
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
"""Device history UI view functions"""

from operator import attrgetter

from django.db import connection, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from nav.event2 import EventFactory
from nav.models.fields import INFINITY
from nav.models.manage import Netbox, Module, Room, Location, NetboxGroup
from nav.models.event import AlertHistory
from nav.web.message import new_message, Messages
from nav.web.devicehistory.utils.history import (
    fetch_history,
    get_messages_for_history,
    group_history_and_messages,
    describe_search_params,
    add_descendants,
)
from nav.web.devicehistory.utils.componentsearch import get_component_search_results
from nav.web.devicehistory.utils.error import register_error_events
from nav.web.devicehistory.forms import DeviceHistoryViewFilter

device_event = EventFactory('ipdevpoll', 'eventEngine', 'deviceState')

# Often used timelimits, in seconds:
ONE_DAY = 24 * 3600
ONE_WEEK = 7 * ONE_DAY

HISTORY_PER_PAGE = 100
ORPHANS = 10

_ = lambda a: a


def devicehistory_search(request):
    """Implements the device history landing page / search form"""
    if 'from_date' in request.GET:
        form = DeviceHistoryViewFilter(request.GET)
        if form.is_valid():
            return devicehistory_view(request)
    else:
        form = DeviceHistoryViewFilter()

    info_dict = {
        'active': {'device': True},
        'navpath': [('Home', '/'), ('Device History', '')],
        'title': 'NAV - Device History',
        'form': form,
    }
    return render(request, 'devicehistory/history_search.html', info_dict)


@require_http_methods(["POST"])
def devicehistory_component_search(request):
    """HTMX endpoint for component searches from device history form"""
    raw_search = request.POST.get("search")
    search = raw_search.strip() if raw_search else ''
    if not search:
        return render(
            request, 'devicehistory/_component-search-results.html', {'results': {}}
        )

    results = get_component_search_results(search, "View %s history")
    return render(
        request, 'devicehistory/_component-search-results.html', {'results': results}
    )


def devicehistory_view_location(request, location_id):
    url = reverse('devicehistory-view')
    return redirect(url + '?loc=%s' % location_id)


def devicehistory_view_netbox(request, netbox_id):
    url = reverse('devicehistory-view')
    return redirect(url + '?netbox=%s' % netbox_id)


def devicehistory_view_room(request, room_id):
    url = reverse('devicehistory-view')
    return redirect(url + '?room=%s' % room_id)


def devicehistory_view(request, **_):
    """Device history search results view"""

    selection = {
        'organization': request.GET.getlist('org'),
        'category': request.GET.getlist('cat'),
        'room__location': request.GET.getlist('loc'),
        'room': request.GET.getlist('room'),
        'netbox': request.GET.getlist('netbox'),
        'groups': request.GET.getlist('netboxgroup'),
        'modules': request.GET.getlist('module'),
        'mode': request.GET.getlist('mode'),
    }

    grouped_history = None
    valid_params = ['to_date', 'from_date', 'eventtype', 'group_by', 'netbox', 'room']
    if len(set(valid_params) & set(request.GET.keys())) >= 1:
        form = DeviceHistoryViewFilter(request.GET)
    else:
        form = DeviceHistoryViewFilter(DeviceHistoryViewFilter.get_initial())
    if form.is_valid():
        # We need to handle locations as they are tree-based
        selection['room__location'] = add_descendants(selection['room__location'])

        alert_history = fetch_history(selection, form)
        grouped_history = group_history_and_messages(
            alert_history,
            get_messages_for_history(alert_history),
            form.cleaned_data['group_by'],
        )

        # Use 'loc' instead of 'location' to avoid noscript XSS protection issues
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
        'form': form,
    }
    return render(request, 'devicehistory/history_view.html', info_dict)


def error_form(request):
    """Implements the 'register error event' form"""
    error_comment = request.POST.get('error_comment', "")

    return render(
        request,
        'devicehistory/register_error.html',
        {
            'active': {'error': True},
            'confirm': False,
            'error_comment': error_comment,
            'title': 'NAV - Device History - Register error',
            'navpath': [
                ('Home', '/'),
                ('Register error event', ''),
            ],
        },
    )


@require_http_methods(["POST"])
def registererror_component_search(request):
    """HTMX endpoint for component searches from device history form"""
    raw_search = request.POST.get("search")
    search = raw_search.strip() if raw_search else ''
    if not search:
        return render(
            request, 'devicehistory/_component-search-results.html', {'results': {}}
        )

    results = get_component_search_results(
        search, 'Add %s error event', [Room, Location, NetboxGroup]
    )
    return render(
        request, 'devicehistory/_component-search-results.html', {'results': results}
    )


def confirm_error_form(request):
    """Implements confirmation form for device error event registration"""
    selection = {
        'netbox': request.POST.getlist('netbox'),
        'module': request.POST.getlist('module'),
    }

    netbox = Netbox.objects.filter(id__in=selection['netbox'])
    module = Module.objects.select_related('netbox').filter(id__in=selection['module'])

    return render(
        request,
        'devicehistory/confirm_error.html',
        {
            'active': {'error': True},
            'confirm': True,
            'netbox': netbox,
            'module': module,
            'title': 'NAV - Device History - Confirm error event',
            'navpath': [
                ('Home', '/'),
                ('Register error event', reverse('devicehistory-registererror')),
            ],
        },
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
        new_message(
            request,
            _("There's no error message supplied. Are you sure you want to continue?"),
            Messages.WARNING,
        )
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
            result.append(
                {
                    'sysname': alert.netbox.sysname,
                    'moduleid': alert.module.id,
                    'name': alert.module.name,
                    'module_number': alert.module.module_number,
                    'descr': alert.module.description,
                    'start_time': alert.start_time,
                }
            )

    info_dict = {
        'active': {'module': True},
        'confirm_delete': confirm_deletion,
        'modules': result,
        'title': 'NAV - Device History - Delete module',
        'navpath': [('Home', '/'), ('Delete module', '')],
    }
    return render(request, 'devicehistory/delete_module.html', info_dict)


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

    for hist in history:
        # Delete the entity representing the module
        cursor.execute(
            "DELETE FROM netboxentity WHERE netboxid = %s and deviceid = %s",
            [hist.module.netbox.id, hist.module.device.id],
        )
        # Create event for deleted module
        device_event.notify(
            device=hist.module.device,
            netbox=hist.module.netbox,
            alert_type="deviceDeletedModule",
        ).save()

    return HttpResponseRedirect(reverse('devicehistory-module'))


def _get_unresolved_module_states(limit_to=None):
    """Returns AlertHistory objects for all modules that are currently down.

    Each AlertHistory object will have an extra module attribute,
    which will be the referenced Module instance.

    """
    history = (
        AlertHistory.objects.select_related('device', 'netbox')
        .filter(
            event_type__id='moduleState',
            alert_type__name='moduleDown',
            end_time__gte=INFINITY,
        )
        .exclude(subid='')
        .extra(select={'module': 'NULL'})
    )

    if limit_to:
        history = history.filter(subid__in=limit_to)

    history = dict((int(h.subid), h) for h in history)
    for module in Module.objects.filter(id__in=history.keys()):
        history[module.id].module = module

    return sorted(history.values(), key=attrgetter('start_time'))

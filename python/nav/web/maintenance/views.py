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

import nav.maintenance

from datetime import datetime, date

from django.core.urlresolvers import reverse
from django.db.models import Count
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.utils.safestring import mark_safe

from nav.django.utils import get_account
from nav.models.manage import Netbox, Room, Location
from nav.models.service import Service
from nav.models.msgmaint import MaintenanceTask, MaintenanceComponent
from nav.web.message import new_message, Messages
from nav.web.quickselect import QuickSelect

from nav.web.maintenance.utils import components_for_keys, task_component_trails
from nav.web.maintenance.utils import get_component_keys_from_post, PRIMARY_KEY_INTEGER
from nav.web.maintenance.utils import MaintenanceCalendar
from nav.web.maintenance.forms import MaintenanceTaskForm


def calendar(request, year=None, month=None):
    if not year:
        year = date.today().year
    if not month:
        month = date.today().month
    this_month = date(year, month, 1)
    next_month = date(year, month + 1, 1)
    tasks = MaintenanceTask.objects.filter(
        start_time__gt=this_month,
        start_time__lt=next_month
    )
    calendar = MaintenanceCalendar(tasks).formatmonth(year, month)
    return render_to_response(
        'maintenance/calendar.html',
        {
            'active': {'calendar': True},
            'calendar': mark_safe(calendar),
        },
        RequestContext(request)
    )

def active(request):
    tasks = MaintenanceTask.objects.filter(
        start_time__lt=datetime.now(),
        end_time__gt=datetime.now()
    ).annotate(component_count=Count('maintenancecomponent'))
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'active': True},
            'tasks': tasks,
        },
        RequestContext(request)
    )

def planned(request):
    tasks = nav.maintenance.getTasks('maint_start > now() AND maint_end > NOW()')
    tasks = MaintenanceTask.objects.filter(
        start_time__gt=datetime.now(),
        end_time__gt=datetime.now()
    ).annotate(component_count=Count('maintenancecomponent'))
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'planned': True},
            'tasks': tasks,
        },
        RequestContext(request)
    )

def historic(request):
    tasks = MaintenanceTask.objects.filter(
        end_time__lt=datetime.now()
    ).annotate(component_count=Count('maintenancecomponent'))
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'historic': True},
            'tasks': tasks,
        },
        RequestContext(request)
    )

def view(request, task_id):
    task = get_object_or_404(MaintenanceTask, pk=task_id)

    maint_components = MaintenanceComponent.objects.filter(
        maintenance_task=task.id).values_list('key', 'value')

    component_keys = {'service': [], 'netbox': [], 'room': [], 'location': []}
    for key, value in maint_components:
        if key in PRIMARY_KEY_INTEGER:
            value = int(value)
        component_keys[key].append(value)

    component_data = components_for_keys(component_keys)
    components = {}
    for key in component_data:
        for component in component_data[key]:
            pkey = component['id']
            if key not in components:
                components[key] = {}
            components[key][pkey] = component

    component_trail = task_component_trails(component_keys, components)
    return render_to_response(
        'maintenance/details.html',
        {
            'task': task,
            'components': component_trail,
        },
        RequestContext(request)
    )

def cancel(request, task_id):
    account = get_account(request)
    if account.is_default_account():
        #FIXME redirect
        raise Exception("Oh noes")

    task = get_object_or_404(MaintenanceTask, pk=task_id)
    if request.method == 'POST':
        task.state = 'canceled'
        task.save()
        new_message(request._req,
            "This task is now cancelled.", Messages.SUCCESS)
        url = reverse('maintenance-view', args=[task_id])
        return HttpResponseRedirect(reverse('maintenance-view', args=[task_id]))
    else:
        return render_to_response(
            'maintenance/cancel.html',
            {
                'task': task,
            },
            RequestContext(request)
        )

def new_task(request):
    quickselect = QuickSelect(service=True)
    component_trail = None
    component_keys = None
    task_form = None
    if request.method == 'POST':
        if 'form' in request.POST:
            task_form = MaintenanceTaskForm()
        if 'save' in request.POST:
            task_form = MaintenanceTaskForm(request.POST)

        component_keys = get_component_keys_from_post(request.POST)
        component_data = components_for_keys(component_keys)
        components = {}
        for key in component_data:
            for component in component_data[key]:
                pkey = component['id']
                if key not in components:
                    components[key] = {}
                components[key][pkey] = component

        component_trail = task_component_trails(component_keys, components)
    return render_to_response(
        'maintenance/new_task.html',
        {
            'task_form': task_form,
            'quickselect': mark_safe(quickselect),
            'components': component_trail,
            'selected': component_keys,
        },
        RequestContext(request)
    )

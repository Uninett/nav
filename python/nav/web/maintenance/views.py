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

from datetime import datetime, date, timedelta

from django.core.urlresolvers import reverse
from django.db import transaction, connection
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
from nav.web.maintenance.utils import get_component_keys, PRIMARY_KEY_INTEGER
from nav.web.maintenance.utils import structure_component_data, infodict_by_state
from nav.web.maintenance.utils import MaintenanceCalendar, NAVPATH, TITLE
from nav.web.maintenance.forms import MaintenanceTaskForm

def calendar(request, year=None, month=None):
    try:
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
        this_month_start = date(year, month, 1)
    except (TypeError, ValueError):
        year = date.today().year
        month = date.today().month
        this_month_start = date(year, month, 1)

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_year = year + 1
        next_month = 1

    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_year = year - 1
        prev_month = 12

    prev_month_start = date(prev_year, prev_month, 1)
    next_month_start = date(next_year, next_month, 1)
    tasks = MaintenanceTask.objects.filter(
        start_time__gt=this_month_start,
        start_time__lt=next_month_start,
    )
    calendar = MaintenanceCalendar(tasks).formatmonth(year, month)
    return render_to_response(
        'maintenance/calendar.html',
        {
            'active': {'calendar': True},
            'navpath': NAVPATH,
            'title': TITLE,
            'calendar': mark_safe(calendar),
            'prev_month': prev_month_start,
            'this_month': this_month_start,
            'next_month': next_month_start,
            'curr_month': datetime.today(),
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
            'navpath': NAVPATH + [('Active tasks', '')],
            'title': TITLE + " - Active tasks",
            'tasks': tasks,
        },
        RequestContext(request)
    )

def planned(request):
    tasks = MaintenanceTask.objects.filter(
        start_time__gt=datetime.now(),
        end_time__gt=datetime.now()
    ).annotate(component_count=Count('maintenancecomponent'))
    return render_to_response(
        'maintenance/list.html',
        {
            'active': {'planned': True},
            'navpath': NAVPATH + [('Planned tasks', '')],
            'title': TITLE + " - Planned tasks",
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
            'navpath': NAVPATH + [('Historic tasks', '')],
            'title': TITLE + " - Historic tasks",
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
    components = structure_component_data(component_data)
    component_trail = task_component_trails(component_keys, components)

    infodict = infodict_by_state(task)
    return render_to_response(
        'maintenance/details.html',
        {
            'active': infodict['active'],
            'navpath': infodict['navpath'],
            'title': TITLE + " - Task \"%s\"" % task.description,
            'task': task,
            'components': component_trail,
        },
        RequestContext(request)
    )

def cancel(request, task_id):
    account = get_account(request)
    task = get_object_or_404(MaintenanceTask, pk=task_id)
    if request.method == 'POST':
        task.state = 'canceled'
        task.save()
        new_message(request._req,
            "This task is now cancelled.", Messages.SUCCESS)
        url = reverse('maintenance-view', args=[task_id])
        return HttpResponseRedirect(reverse('maintenance-view', args=[task_id]))
    else:
        infodict = infodict_by_state(task)
        return render_to_response(
            'maintenance/cancel.html',
            {
                'active': infodict['active'],
                'navpath': infodict['navpath'],
                'title': TITLE + " - Cancel task",
                'task': task,
            },
            RequestContext(request)
        )

@transaction.commit_on_success()
def new_task(request, task_id=None):
    account = get_account(request)
    quickselect = QuickSelect(service=True)
    component_trail = None
    component_keys = None
    task = None
    num_components = 0

    if task_id:
        task = get_object_or_404(MaintenanceTask, pk=task_id)
        initial = {
            'start_time': task.start_time,
            'end_time': task.end_time,
            'description': task.description,
        }
    else:
        initial = {
            'start_time': datetime.today().strftime("%Y-%m-%d %H:%M"),
            'end_time': (datetime.today() + timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M")
        }
    task_form = MaintenanceTaskForm(initial=initial)

    if request.method == 'POST':
        component_keys = get_component_keys(request.POST)
    elif task:
        component_keys = {'service': [], 'netbox': [], 'room': [], 'location': []}
        for key, value in task.maintenancecomponent_set.values_list('key', 'value'):
            if key in PRIMARY_KEY_INTEGER:
                value = int(value)
            component_keys[key].append(value)

    if component_keys:
        component_data = components_for_keys(component_keys)
        components = structure_component_data(component_data)
        component_trail = task_component_trails(component_keys, components)
        num_components += len(component_data['service']) + len(component_data['netbox'])
        num_components += len(component_data['room']) + len(component_data['location'])

    if request.method == 'POST':
        if 'save' in request.POST:
            task_form = MaintenanceTaskForm(request.POST)
            if task_form.is_valid() and num_components > 0:
                start_time = task_form.cleaned_data['start_time']
                end_time = task_form.cleaned_data['end_time']
                state = MaintenanceTask.STATE_SCHEDULED
                if start_time < datetime.now() and end_time <= datetime.now():
                    state = MaintenanceTask.STATE_SCHEDULED

                new_task = MaintenanceTask()
                new_task.start_time = task_form.cleaned_data['start_time']
                new_task.end_time = task_form.cleaned_data['end_time']
                new_task.description = task_form.cleaned_data['description']
                new_task.state = state
                new_task.author = account.login
                if task:
                    new_task.id = task.id
                new_task.save()

                if task:
                    cursor = connection.cursor()
                    cursor.execute("DELETE FROM maint_component WHERE maint_taskid = %s", (new_task.id,))
                    transaction.commit_unless_managed()
                for key in component_data:
                    for component in component_data[key]:
                        task_component = MaintenanceComponent(
                            maintenance_task=new_task,
                            key=key,
                            value="%s" % component['id'])
                        task_component.save()
                return HttpResponseRedirect(reverse('maintenance-view', args=[new_task.id]))
            if num_components <= 0:
                new_message(request._req,
                    "No components selected.", Messages.ERROR)
        else:
            task_form = MaintenanceTaskForm(initial=request.POST)

    if task:
        navpath = NAVPATH + [('Edit', '')]
        title = TITLE + " - Editing \"%s\"" % task.description
    else:
        navpath = NAVPATH + [('New', '')]
        title = TITLE + " - New task"
    return render_to_response(
        'maintenance/new_task.html',
        {
            'active': {'new': True},
            'navpath': navpath,
            'title': title,
            'task_form': task_form,
            'task_id': task_id,
            'quickselect': mark_safe(quickselect),
            'components': component_trail,
            'selected': component_keys,
        },
        RequestContext(request)
    )

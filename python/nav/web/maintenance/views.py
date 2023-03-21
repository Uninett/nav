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

import logging

import time
from datetime import datetime, date

from django.db import transaction, connection
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from nav.django.utils import get_account
from nav.models.manage import Netbox
from nav.models.msgmaint import MaintenanceTask, MaintenanceComponent
from nav.web.message import new_message, Messages
from nav.web.quickselect import QuickSelect

from nav.web.maintenance.utils import components_for_keys
from nav.web.maintenance.utils import task_component_trails
from nav.web.maintenance.utils import get_component_keys, PRIMARY_KEY_INTEGER
from nav.web.maintenance.utils import structure_component_data
from nav.web.maintenance.utils import task_form_initial, infodict_by_state
from nav.web.maintenance.utils import MaintenanceCalendar, NAVPATH, TITLE
from nav.web.maintenance.forms import MaintenanceTaskForm, MaintenanceCalendarForm
from nav.web.maintenance.forms import MaintenanceAddSingleNetbox
import nav.maintengine

INFINITY = datetime.max

_logger = logging.getLogger(__name__)


def redirect_to_calendar(_request):
    """Redirect to main page for this tool"""
    return redirect(reverse('maintenance'))


def calendar(request, year=None, month=None):
    # If the form was used to get here, redirect to the appropriate page
    if "year" in request.GET and "month" in request.GET:
        form = MaintenanceCalendarForm(data=request.GET.dict())
        if form.is_valid():
            return redirect(
                "maintenance-calendar",
                year=request.GET.get("year"),
                month=request.GET.get("month"),
            )
    elif year and month:
        form = MaintenanceCalendarForm(
            data={'year': year, 'month': month},
        )
    else:
        form = MaintenanceCalendarForm()

    tasks = (
        MaintenanceTask.objects.filter(
            start_time__lt=form.next_month_start, end_time__gt=form.this_month_start
        )
        .exclude(state=MaintenanceTask.STATE_CANCELED)
        .order_by('start_time')
    )
    cal = MaintenanceCalendar(tasks).formatmonth(form.cleaned_year, form.cleaned_month)
    return render(
        request,
        'maintenance/calendar.html',
        {
            'active': {'calendar': True},
            'calendarform': form,
            'navpath': NAVPATH,
            'title': TITLE,
            'heading': "Maintenance schedule",
            'calendar': mark_safe(cal),
            'prev_month': form.previous_month_start,
            'this_month': form.this_month_start,
            'next_month': form.next_month_start,
            'curr_month': datetime.today(),
        },
    )


def active(request):
    heading = "Active tasks"
    tasks = (
        MaintenanceTask.objects.filter(
            start_time__lt=datetime.now(),
            end_time__gt=datetime.now(),
            state__in=(MaintenanceTask.STATE_SCHEDULED, MaintenanceTask.STATE_ACTIVE),
        )
        .order_by('-start_time', '-end_time')
        .annotate(component_count=Count('maintenance_components'))
    )
    for task in tasks:
        # Tasks that have only one component should show a link
        # directly to the device instead of a number.
        if task.component_count == 1:
            maint_components = MaintenanceComponent.objects.filter(
                maintenance_task=task, key='netbox'
            )
            if len(maint_components) == 1:
                netbox = None
                netbox_id = maint_components[0].value
                try:
                    netbox = Netbox.objects.get(pk=int(netbox_id))
                except Exception as error:
                    _logger.error(
                        'Get netbox %s failed; Exception = %s', netbox_id, error
                    )
                    continue
                task.netbox = netbox

    return render(
        request,
        'maintenance/list.html',
        {
            'active': {'active': True},
            'navpath': NAVPATH + [(heading, '')],
            'title': TITLE + " - " + heading,
            'heading': heading,
            'tasks': tasks,
        },
    )


def planned(request):
    heading = "Scheduled tasks"
    tasks = (
        MaintenanceTask.objects.filter(
            start_time__gt=datetime.now(),
            end_time__gt=datetime.now(),
            state__in=(MaintenanceTask.STATE_SCHEDULED, MaintenanceTask.STATE_ACTIVE),
        )
        .order_by('-start_time', '-end_time')
        .annotate(component_count=Count('maintenance_components'))
    )
    return render(
        request,
        'maintenance/list.html',
        {
            'active': {'planned': True},
            'navpath': NAVPATH + [(heading, '')],
            'title': TITLE + " - " + heading,
            'heading': heading,
            'tasks': tasks,
        },
    )


def historic(request):
    heading = "Archived tasks"
    tasks = (
        MaintenanceTask.objects.filter(
            Q(end_time__lt=datetime.now())
            | Q(
                state__in=(MaintenanceTask.STATE_CANCELED, MaintenanceTask.STATE_PASSED)
            )
        )
        .order_by('-start_time', '-end_time')
        .annotate(component_count=Count('maintenance_components'))
    )
    return render(
        request,
        'maintenance/list.html',
        {
            'active': {'historic': True},
            'navpath': NAVPATH + [('Historic tasks', '')],
            'title': TITLE + " - " + heading,
            'heading': heading,
            'tasks': tasks,
        },
    )


def view(request, task_id):
    task = get_object_or_404(MaintenanceTask, pk=task_id)
    maint_components = MaintenanceComponent.objects.filter(
        maintenance_task=task.id
    ).values_list('key', 'value')

    component_keys = {
        'service': [],
        'netbox': [],
        'room': [],
        'location': [],
        'netboxgroup': [],
    }
    for key, value in maint_components:
        if key in PRIMARY_KEY_INTEGER:
            value = int(value)
        component_keys[key].append(value)

    component_data = components_for_keys(component_keys)
    components = structure_component_data(component_data)
    component_trail = task_component_trails(component_keys, components)

    heading = 'Task "%s"' % task.description
    infodict = infodict_by_state(task)
    return render(
        request,
        'maintenance/details.html',
        {
            'active': infodict['active'],
            'navpath': infodict['navpath'],
            'title': TITLE + " - " + heading,
            'heading': heading,
            'task': task,
            'components': component_trail,
        },
    )


def cancel(request, task_id):
    task = get_object_or_404(MaintenanceTask, pk=task_id)
    heading = 'Cancel task'
    if request.method == 'POST':
        task.state = 'canceled'
        task.save()
        new_message(request, "This task is now cancelled.", Messages.SUCCESS)
        return HttpResponseRedirect(reverse('maintenance-view', args=[task_id]))
    else:
        infodict = infodict_by_state(task)
        return render(
            request,
            'maintenance/cancel.html',
            {
                'active': infodict['active'],
                'navpath': infodict['navpath'],
                'title': TITLE + " - " + heading,
                'heading': heading,
                'task': task,
            },
        )


@transaction.atomic()
def edit(request, task_id=None, start_time=None, **_):
    account = get_account(request)
    quickselect = QuickSelect(service=True)
    component_trail = None
    component_keys = None
    task = None

    if task_id:
        task = get_object_or_404(MaintenanceTask, pk=task_id)
    task_form = MaintenanceTaskForm(initial=task_form_initial(task, start_time))

    if request.method == 'POST':
        component_keys = get_component_keys(request.POST)
    elif task:
        component_keys = {
            'service': [],
            'netbox': [],
            'room': [],
            'location': [],
            'netboxgroup': [],
        }
        for key, value in task.maintenance_components.values_list('key', 'value'):
            if key in PRIMARY_KEY_INTEGER:
                value = int(value)
            component_keys[key].append(value)
    else:
        component_keys = get_component_keys(request.GET)

    if component_keys:
        component_data = components_for_keys(component_keys)
        components = structure_component_data(component_data)
        component_trail = task_component_trails(component_keys, components)

    if request.method == 'POST':
        if 'save' in request.POST:
            task_form = MaintenanceTaskForm(request.POST)
            if not any(component_data.values()):
                new_message(request, "No components selected.", Messages.ERROR)
            elif task_form.is_valid():
                start_time = task_form.cleaned_data['start_time']
                end_time = task_form.cleaned_data['end_time']
                no_end_time = task_form.cleaned_data['no_end_time']
                state = MaintenanceTask.STATE_SCHEDULED
                if (
                    start_time < datetime.now()
                    and end_time
                    and end_time <= datetime.now()
                ):
                    state = MaintenanceTask.STATE_SCHEDULED

                new_task = MaintenanceTask()
                new_task.start_time = task_form.cleaned_data['start_time']
                if no_end_time:
                    new_task.end_time = INFINITY
                elif not no_end_time and end_time:
                    new_task.end_time = task_form.cleaned_data['end_time']
                new_task.description = task_form.cleaned_data['description']
                new_task.state = state
                new_task.author = account.login
                if task:
                    new_task.id = task.id
                new_task.save()

                if task:
                    cursor = connection.cursor()
                    sql = """DELETE FROM maint_component
                                WHERE maint_taskid = %s"""
                    cursor.execute(sql, (new_task.id,))
                for key in component_data:
                    for component in component_data[key]:
                        task_component = MaintenanceComponent(
                            maintenance_task=new_task,
                            key=key,
                            value="%s" % component['id'],
                        )
                        task_component.save()
                new_message(
                    request, "Saved task %s" % new_task.description, Messages.SUCCESS
                )
                return HttpResponseRedirect(
                    reverse('maintenance-view', args=[new_task.id])
                )
        else:
            task_form = MaintenanceTaskForm(initial=request.POST)

    if task:
        navpath = NAVPATH + [('Edit', '')]
        heading = 'Editing "%s"' % task.description
        title = TITLE + " - " + heading
    else:
        navpath = NAVPATH + [('New', '')]
        heading = 'New task'
        title = TITLE + " - " + heading
    return render(
        request,
        'maintenance/new_task.html',
        {
            'active': {'new': True},
            'navpath': navpath,
            'title': title,
            'heading': heading,
            'task_form': task_form,
            'task_id': task_id,
            'quickselect': mark_safe(quickselect),
            'components': component_trail,
            'selected': component_keys,
        },
    )


def add_box_to_maintenance(request):
    """
    This view puts a Netbox on immediate, indefinite maintenance and
    redirects the user to the status page. It implements the functionality
    behind the "Put on maintenance" button present in the Status page's "IP
    Devices down" items.

    The maintenance engine will close the maintenance task automatically when
    the Netbox has been consistently up for a period of time.

    """
    before = time.time()
    account = get_account(request)
    if request.method == 'POST':
        netboxid_form = MaintenanceAddSingleNetbox(request.POST)
        if netboxid_form.is_valid():
            netbox_id = netboxid_form.cleaned_data['netboxid']
            netbox = get_object_or_404(Netbox, pk=netbox_id)

            # Check if device is already on maintenance
            already_on_maint = MaintenanceComponent.objects.filter(
                key='netbox',
                value=str(netbox.id),
                maintenance_task__state=MaintenanceTask.STATE_ACTIVE,
                maintenance_task__end_time=datetime.max,
            )
            if not already_on_maint:
                # Box is not on maintenance
                _add_neverending_maintenance_task(account, netbox)

                _logger.debug('Run maintenance checker')
                nav.maintengine.check_devices_on_maintenance()
                _logger.debug('Maintenance checker finished')

                _logger.debug(
                    'Add netbox to maintenance finished in %.3fs', time.time() - before
                )
            else:
                # What should we do here?
                _logger.error(
                    'Netbox %s (id=%d) is already on maintenance',
                    netbox.sysname,
                    netbox.id,
                )
    return HttpResponseRedirect(reverse('status-index'))


@transaction.atomic()
def _add_neverending_maintenance_task(owner, netbox):
    _logger.debug('Adding maintenance task...')
    maint_task = MaintenanceTask()
    maint_task.start_time = datetime.now()
    maint_task.end_time = INFINITY
    descr = (
        "On maintenance till up again; set "
        + "from status page by user %s" % owner.login
    )
    maint_task.description = descr
    maint_task.author = owner.login
    maint_task.state = MaintenanceTask.STATE_SCHEDULED
    maint_task.save()
    _logger.debug(
        "Maintenance task %d; Adding component %s (id=%d)",
        maint_task.id,
        netbox.sysname,
        netbox.id,
    )
    maint_component = MaintenanceComponent()
    maint_component.maintenance_task = maint_task
    maint_component.key = 'netbox'
    maint_component.value = '%d' % netbox.id
    maint_component.save()

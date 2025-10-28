#
# Copyright (C) 2011 Uninett AS
# Copyright (C) 2024 Sikt
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
from datetime import datetime
from typing import Optional

from django.db import connection, transaction
from django.db.models import Count, Model, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods

import nav.maintengine
from nav.web.auth.utils import get_account
from nav.models.manage import Location, Netbox, NetboxGroup, Room
from nav.models.msgmaint import MaintenanceComponent, MaintenanceTask
from nav.models.service import Service
from nav.web.maintenance.forms import (
    MaintenanceAddSingleNetbox,
    MaintenanceCalendarForm,
    MaintenanceTaskForm,
)
from nav.web.maintenance.utils import (
    NAVPATH,
    COMPONENTS_WITH_INTEGER_PK,
    TITLE,
    MaintenanceCalendar,
    component_to_trail,
    get_component_keys,
    get_component_name,
    get_components,
    get_components_from_keydict,
    prefetch_and_group_components,
    infodict_by_state,
    task_form_initial,
)
from nav.web.message import Messages, new_message

INFINITY = datetime.max

_logger = logging.getLogger(__name__)


def redirect_to_calendar(_request):
    """Redirect to main page for this tool"""
    return redirect(reverse('maintenance-calendar'))


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
                except Netbox.DoesNotExist as error:
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
    components = get_components(task)
    component_trail = [component_to_trail(c) for c in components]

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
    components = task = None
    component_keys_errors = []
    component_keys = {}

    if task_id:
        task = get_object_or_404(MaintenanceTask, pk=task_id)
    task_form = MaintenanceTaskForm(initial=task_form_initial(task, start_time))

    if request.method == 'POST':
        component_keys, component_keys_errors = get_component_keys(request.POST)
    elif task:
        components = get_components(task)
    else:
        component_keys, component_keys_errors = get_component_keys(request.GET)

    if component_keys:
        components, component_data_errors = get_components_from_keydict(component_keys)
        for error in component_data_errors:
            new_message(request, error, Messages.ERROR)

    component_trail = [component_to_trail(c) for c in components]

    for error in component_keys_errors:
        new_message(request, error, Messages.ERROR)

    if request.method == 'POST':
        if 'save' in request.POST:
            task_form = MaintenanceTaskForm(request.POST)
            if component_keys and not components:
                new_message(request, "No components selected.", Messages.ERROR)
            elif not component_keys_errors and task_form.is_valid():
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
                for component in components:
                    table = component._meta.db_table
                    descr = (
                        str(component) if table in COMPONENTS_WITH_INTEGER_PK else None
                    )
                    task_component = MaintenanceComponent(
                        maintenance_task=new_task,
                        key=table,
                        value=component.pk,
                        description=descr,
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
            'components': component_trail,
            'selected': component_keys,
        },
    )


@require_http_methods(["POST"])
def component_search(request):
    """HTMX endpoint for component searches from maintenance task form"""
    raw_search = request.POST.get("search")
    search = raw_search.strip() if raw_search else ''
    if not search:
        return render(
            request, 'maintenance/_component-search-results.html', {'results': {}}
        )

    results = {}
    searches: list[tuple[type[Model], Q, Optional[Model]]] = [
        (Location, Q(id__icontains=search), None),
        (Room, Q(id__icontains=search), Location),
        (Netbox, Q(sysname__icontains=search), Room),
        (NetboxGroup, Q(id__icontains=search), None),
        (
            Service,
            Q(handler__icontains=search) | Q(netbox__sysname__icontains=search),
            Netbox,
        ),
    ]

    for component_type, query, group_by in searches:
        component_results = component_type.objects.filter(query)
        grouped_results = prefetch_and_group_components(
            component_type, component_results, group_by
        )

        if component_results:
            component_title = get_component_name(component_type)
            results[component_title] = {
                'label': component_type._meta.verbose_name.title(),
                'values': grouped_results,
                'has_grouping': group_by is not None,
            }

    return render(
        request, 'maintenance/_component-search-results.html', {'results': results}
    )


@require_http_methods(["POST"])
def component_select(request):
    """HTMX endpoint for component selection from maintenance task form"""
    component_keys, component_keys_errors = get_component_keys(request.POST)
    for error in component_keys_errors:
        new_message(request, error, Messages.ERROR)

    components, components_errors = get_components_from_keydict(component_keys)
    for error in components_errors:
        new_message(request, error, Messages.ERROR)

    component_trail = [component_to_trail(c) for c in components]

    return render(
        request,
        'maintenance/_selected-components-list.html',
        {'components': component_trail, 'selected': component_keys},
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

# -*- coding: utf-8 -*-
# Copyright (C) 2012-2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
NAV Maintenance Engine.

This module deals with enforcing the maintenance schedule by transitioning
the state of registered maintenance tasks and dispatching maintenance events
to the event queue.

"""

import datetime
import logging

from django.db import transaction
from django.db.models import Q

from nav.models import manage, service
from nav.models.event import EventQueue as Event, AlertHistory
from nav.models.msgmaint import MaintenanceTask

INFINITY = datetime.datetime.max

# The devices must have been up for at least this time before
# ending a maintenance task without a specified end.
MINIMUM_UPTIME = datetime.timedelta(minutes=60)

_logger = logging.getLogger('nav.maintengine')


@transaction.atomic()
def schedule():
    """Changes invalid task states to 'scheduled'"""
    tasks = MaintenanceTask.objects.filter(
        Q(state__isnull=True) | ~Q(state__in=[s[0] for s in MaintenanceTask.STATES])
    )
    tasks.update(state=MaintenanceTask.STATE_SCHEDULED)


@transaction.atomic()
def check_tasks_without_end():
    """
    Ends all endless maintenance tasks whose event subjects have all been up
    for longer than the set minimum time.
    """
    for task in MaintenanceTask.objects.endless().filter(
        state=MaintenanceTask.STATE_ACTIVE
    ):
        currently_or_too_recently_down = []
        threshold = datetime.datetime.now() - MINIMUM_UPTIME
        for subject in task.get_event_subjects():
            end_time = subject.last_downtime_ended() if subject else None
            if end_time and end_time > threshold:
                currently_or_too_recently_down.append(subject)

        if currently_or_too_recently_down:
            _logger.debug(
                "Endless maintenance task %d: Things that haven't been up "
                "longer than the threshold: %r",
                task.id,
                currently_or_too_recently_down,
            )
        else:
            now = datetime.datetime.now()
            _logger.debug(
                "Endless maintenance task %d: All components have been up "
                "longer than the threshold, setting end time to %s",
                task.id,
                now,
            )
            task.end_time = now
            task.save()


@transaction.atomic()
def do_state_transitions():
    """Finds active or scheduled tasks that have run out and sets them as passed,
    and finds scheduled tasks in the current window and sets them as active.
    """
    tasks = MaintenanceTask.objects.past().filter(
        state__in=[MaintenanceTask.STATE_ACTIVE, MaintenanceTask.STATE_SCHEDULED]
    )
    tasks.update(state=MaintenanceTask.STATE_PASSED)

    _logger.debug("Tasks transitioned to passed state: %r", tasks)

    tasks = MaintenanceTask.objects.current().filter(
        state=MaintenanceTask.STATE_SCHEDULED
    )
    tasks.update(state=MaintenanceTask.STATE_ACTIVE)

    _logger.debug("Tasks transitioned to active state: %r", tasks)

    cancel_tasks_without_components()


def cancel_tasks_without_components():
    """Cancels active tasks where all components are missing"""
    tasks = MaintenanceTask.objects.filter(
        state=MaintenanceTask.STATE_ACTIVE
    ).prefetch_related('maintenance_components')
    for task in tasks:
        if not any(task.get_components()):
            task.state = MaintenanceTask.STATE_CANCELED
            task.save()
            _logger.debug("Task %r canceled because all components were missing", task)


def check_state_differences():
    """
    Checks what should have been on maintenance from MaintenanceTask against
    what actually is on maintenance from AlertHistory, then creates events
    based on this.
    """
    # Find out what should have been on maintenance
    should_be_on_maintenance = set()
    task_subject_mapper = {}

    for task in MaintenanceTask.objects.filter(state=MaintenanceTask.STATE_ACTIVE):
        for subject in task.get_event_subjects():
            task_subject_mapper[subject] = task.id
            should_be_on_maintenance.add(subject)

    # Find out what is on maintenance
    is_on_maintenance = set()

    for alert in AlertHistory.objects.unresolved('maintenanceState'):
        subject = alert.get_subject()
        is_on_maintenance.add(subject)

    # Set on maintenance that which is not and should be
    to_be_put_on_maintenance = should_be_on_maintenance - is_on_maintenance
    _logger.debug(
        "Subjects that should be on maintenance but weren't: %r",
        to_be_put_on_maintenance,
    )

    for subject in to_be_put_on_maintenance:
        create_event(
            subject,
            state=Event.STATE_START,
            value=100,
            taskid=task_subject_mapper[subject],
        )

    # Set off maintenance that which is and should not be
    to_be_taken_off_maintenance = is_on_maintenance - should_be_on_maintenance
    _logger.debug(
        "Subjects that should not be on maintenance but were: %r",
        to_be_taken_off_maintenance,
    )

    for subject in to_be_taken_off_maintenance:
        create_event(subject, state=Event.STATE_END, value=0)


@transaction.atomic()
def create_event(subject, state, value, taskid=None):
    """
    Adds events to the EventQueue that starts or ends maintenance tasks based
    on a given subject and state.
    """
    target = 'eventEngine'
    subsystem = 'maintenance'
    source = subsystem
    severity = 5
    eventtype = 'maintenanceState'

    event = Event(state=state, value=value, severity=severity)

    varmap = {}

    event.event_type_id = eventtype
    event.target_id = target
    event.source_id = source

    if isinstance(subject, manage.Netbox):
        event.netbox = subject
        event.device = subject.device

        varmap['netbox'] = subject.sysname

    elif isinstance(subject, service.Service):
        event.subid = subject.id
        event.netbox = subject.netbox
        event.device = subject.netbox.device

        varmap['service'] = subject.handler
        varmap['servicename'] = subject.handler

    if taskid:
        varmap['maint_taskid'] = taskid

    event.save()
    event.varmap = varmap

    _logger.debug("Event posted: %r", event)


def check_devices_on_maintenance():
    """Start the main logic for checking maintenance tasks."""
    schedule()
    check_tasks_without_end()
    do_state_transitions()
    check_state_differences()

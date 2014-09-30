# -*- coding: UTF-8 -*-
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
A library for checking maintenance tasks.
"""
import datetime
import logging

import nav.db
import nav.logs
import nav.event

from django.db.transaction import commit_on_success
from django.db.models import Q

INFINITY = datetime.datetime.max

# The devices must have been up for at least this time before
# ending a maintenance task without a specified end.
MINIMUM_UPTIME = datetime.timedelta(minutes=60)

db_conn = None
_logger = logging.getLogger('nav.maintengine')


def _get_dbconn():
    """Get and cache a database-connection."""
    global db_conn
    if not db_conn:
        db_conn = nav.db.getConnection('eventEngine', 'manage')
        # Make sure isolation level is "read committed", not "serialized"
        db_conn.set_isolation_level(1)
    return db_conn


def _get_db():
    """Get a database-cursor."""
    return _get_dbconn().cursor()


def init_logging(log_file=None, log_format=None):
    """Initializes logging setup for maintenance engine"""
    root = logging.getLogger('')
    formatter = None
    if log_format:
        formatter = logging.Formatter(log_format)
    handler = None
    try:
        if log_file:
            handler = logging.FileHandler(log_file)
    except IOError, io_err:
        # Most likely, we were denied access to the log file.
        # We silently ignore it and log nothing :-P
        pass
    else:
        if handler:
            if formatter:
                handler.setFormatter(formatter)
            root.addHandler(handler)
        nav.logs.set_log_levels()
    return _logger


@commit_on_success
def schedule():
    """Changes invalid task states to 'scheduled'"""
    tasks = MaintenanceTask.objects.filter(
        Q(state__isnull=True) |
        ~Q(state__in=[s[0] for s in MaintenanceTask.STATES]))
    tasks.update(state=MaintenanceTask.STATE_SCHEDULED)


def get_boxids_by_key(key, value):
    """Select boxes by key-type and key-value"""
    db = _get_db()
    netbox_ids = []
    if key in ('room', 'location'):
        if key == 'location':
            sql = """SELECT netboxid
                        FROM netbox
                            INNER JOIN room USING (roomid)
                        WHERE locationid = %s"""
        if key == 'room':
            sql = """SELECT netboxid
                        FROM netbox
                        WHERE roomid = %s"""
        db.execute(sql, (value,))
        netbox_ids = [box_id for (box_id,) in db.fetchall()]
    if key == 'service':
        sql = "SELECT netboxid FROM service WHERE serviceid = %s"
        db.execute(sql, (int(value),))
        result = db.fetchone()
        if result:
            (box_id,) = result
            netbox_ids.append(box_id)
    if key == 'netbox':
        netbox_ids.append(int(value))
    return netbox_ids


def get_tasks_and_boxes_without_end():
    """Collect all netboxes from maintenance tasks that do not have a defined
        end time.  Place them in a dictionary with maintenance identity as key
        and a list of affected netboxes for each task."""
    db = _get_db()
    #  Select all affected components for every task.
    sql = """SELECT maint_taskid, key, value
                FROM maint_task
                    INNER JOIN maint_component USING (maint_taskid)
                WHERE state = 'active' AND
                    maint_end >= %s"""
    db.execute(sql, (INFINITY,))
    tasks_and_boxes = {}
    for (maint_id, key, value) in db.fetchall():
        # Collect affected boxes for each maintenance task.
        netbox_ids = get_boxids_by_key(key, value)
        # Use maintenance key as key for netboxes that are affected by
        # the maintenance task.
        if maint_id in tasks_and_boxes:
            tasks_and_boxes[maint_id].extend(netbox_ids)
        else:
            tasks_and_boxes[maint_id] = netbox_ids
    return tasks_and_boxes


@commit_on_success
def check_tasks_without_end():
    """
    Ends all endless maintenance tasks whose event subjects have all been up
    for longer than the set minimum time.
    """
    db = _get_db()
    for task in MaintenanceTask.objects.endless().filter(
            state=MaintenanceTask.STATE_ACTIVE
    ):
        currently_or_too_recently_down = []
        threshold = datetime.datetime.now() - MINIMUM_UPTIME
        for subject in task.get_event_subjects():
            end_time = subject.last_downtime_ended()
            if end_time > threshold:
                currently_or_too_recently_down.append(subject)

        if currently_or_too_recently_down:
            _logger.debug(
                "Endless maintenance task %d: Things that haven't been up "
                "longer than the threshold: %r",
                task.id, currently_or_too_recently_down)
        else:
            now = datetime.datetime.now()
            _logger.debug(
                "Endless maintenance task %d: All components have been up "
                "longer than the threshold, setting end time to %s",
                task.id, now)
            task.end_time = now
            task.save()


def check_state(events, maxdate_boxes):
    """
    Checks if there are some maintenance tasks to be set active or passed.
    """
    time_now = datetime.datetime.now()

    db = _get_db()
    sql = """SELECT maint_taskid FROM maint_task
        WHERE maint_start < %s AND state = 'scheduled'"""
    db.execute(sql, (time_now,))
    for (taskid,) in db.fetchall():
        sched_event = {}
        sched_event['type'] = 'active'
        sched_event['taskid'] = taskid
        events.append(sched_event)

    sql = """SELECT maint_taskid, maint_end FROM maint_task
        WHERE maint_end < %s AND state = 'active'"""
    db.execute(sql, (time_now,))
    for (taskid, maint_end) in db.fetchall():
        active_event = {}
        active_event['type'] = 'passed'
        active_event['taskid'] = taskid
        active_event['maint_end'] = maint_end
        events.append(active_event)

    # Get boxes that should still stay on maintenance
    sql = """SELECT max(maint_end) AS maint_end, key, value
        FROM maint_task INNER JOIN maint_component USING (maint_taskid)
        WHERE state = 'active' AND maint_end > %s
        GROUP BY key, value"""
    db.execute(sql, (time_now,))
    for (maint_end, key, value) in db.fetchall():
        boxids = get_boxids_by_key(key, value)
        for boxid in boxids:
            if boxid in maxdate_boxes and maxdate_boxes[boxid] > maint_end:
                continue
            maxdate_boxes[boxid] = maint_end


def send_event(events, maxdate_boxes, boxes_off_maintenance):
    """Sends events to the event queue."""
    db = _get_db()
    for curr_event in events:
        event_type = curr_event['type']
        taskid = curr_event['taskid']

        # Get all components related to task/event
        sql = """SELECT key, value FROM maint_component
                 WHERE maint_taskid = %(maint_taskid)s"""
        data = {'maint_taskid': taskid}
        db.execute(sql, data)

        for (key, val) in db.fetchall():
            # Prepare event variables
            target = 'eventEngine'
            subsystem = 'maintenance'
            source = subsystem
            severity = 50
            eventtype = 'maintenanceState'
            if event_type == 'active':
                state = 's'  # s = start
                value = 100
            elif event_type == 'passed':
                state = 'e'  # e = end
                value = 0

            # Get all related netboxes
            netboxes = []
            if key in ('location', 'room'):
                if key == 'location':
                    sql = """SELECT netboxid, sysname, deviceid
                        FROM netbox INNER JOIN room USING (roomid)
                        WHERE locationid = %(locationid)s"""
                    data = {'locationid': val}

                    _logger.debug("location query: %s", sql % data)
                    db.execute(sql, data)
                    _logger.debug("location number of results: %d", db.rowcount)
                elif key == 'room':
                    sql = """SELECT netboxid, sysname, deviceid
                        FROM netbox
                        WHERE roomid = %(roomid)s"""
                    data = {'roomid': val}

                    _logger.debug("room query: %s", sql % data)
                    db.execute(sql, data)
                    _logger.debug("room number of results: %d", db.rowcount)

                for (netboxid, sysname, deviceid) in db.fetchall():
                    netboxes.append({'netboxid': netboxid,
                                     'sysname': sysname,
                                     'deviceid': deviceid,
                                     'cvar': 'netbox',
                                     'cval': sysname})
            elif key == 'netbox':
                sql = """SELECT netboxid, sysname, deviceid
                    FROM netbox
                    WHERE netboxid = %(netboxid)s"""
                data = {'netboxid': int(val)}

                _logger.debug("netbox query: %s", sql % data)
                db.execute(sql, data)
                _logger.debug("netbox number of results: %d", db.rowcount)
                result = db.fetchone()

                if result:
                    (netboxid, sysname, deviceid) = result
                    netboxes.append({'netboxid': netboxid,
                                     'sysname': sysname,
                                     'deviceid': deviceid,
                                     'cvar': 'netbox',
                                     'cval': sysname})
            elif key == 'service':
                sql = """SELECT netboxid, sysname, deviceid, handler
                    FROM service INNER JOIN netbox USING (netboxid)
                    WHERE serviceid = %(serviceid)s"""
                data = {'serviceid': int(val)}

                _logger.debug("service query: %s", sql % data)
                db.execute(sql, data)
                _logger.debug("service number of results: %d", db.rowcount)
                result = db.fetchone()

                if result:
                    (netboxid, sysname, deviceid, handler) = result
                    netboxes.append({'netboxid': netboxid,
                                     'sysname': sysname,
                                     'deviceid': deviceid,
                                     'serviceid': int(val),
                                     'servicename': handler,
                                     'cvar': 'service',
                                     'cval': handler})
            elif key == 'module':
                # Unsupported as of NAV 3.2
                raise DeprecationWarning("Deprecated component key")

            # Create events for all related netboxes
            for netbox in netboxes:
                if event_type == 'passed' and netbox['netboxid'] in maxdate_boxes:
                    netbox_id = netbox['netboxid']
                    if maxdate_boxes[netbox_id] > curr_event['maint_end']:
                        _logger.debug(
                            "Skip stop event for netbox %s. It's on "
                            "maintenance until %s.",
                            str(netbox['netboxid']),
                            str(curr_event['maint_end'])
                        )
                        continue
                    # Append to list of boxes taken off maintenance
                    # during this run
                if event_type == 'passed':
                    boxes_off_maintenance.append(netbox['netboxid'])

                if 'serviceid' in netbox:
                    subid = netbox['serviceid']
                else:
                    subid = None

                # Create event
                event = nav.event.Event(source=source, target=target,
                    deviceid=netbox['deviceid'],
                    netboxid=netbox['netboxid'], subid=subid,
                    eventtypeid=eventtype, state=state, value=value,
                    severity=severity)
                event[netbox['cvar']] = netbox['cval']
                event['maint_taskid'] = taskid

                # Add event to eventq
                result = event.post()
                _logger.debug("Event: %s, Result: %s", event, result)

        # Update state
        sql = """UPDATE maint_task
            SET state = %(state)s
            WHERE maint_taskid = %(maint_taskid)s"""
        data = {'state': event_type,
                'maint_taskid': taskid}
        db.execute(sql, data)

        # Commit transaction
        _get_dbconn().commit()


def remove_forgotten(boxes_off_maintenance):
    """
    Remove 'forgotten' netboxes from their maintenance state.

    Sometimes, like when netboxes have been deleted from a maintenance task
    during its active maintenance window, we will no longer know that the box
    has gone on maintenenance and should be taken off. This function takes all
    'forgotten' netboxes off maintenance.

    """
    db = _get_db()
    # This SQL retrieves a list of boxes that are currently on
    # maintenance, according to the alert history.
    sql_actual = """SELECT ah.netboxid, ah.deviceid, n.sysname, subid
        FROM alerthist ah LEFT JOIN netbox n USING (netboxid)
        WHERE eventtypeid='maintenanceState' AND netboxid IS NOT NULL
        AND end_time = 'infinity'"""

    # This SQL retrieves a list of boxes that are supposed to be on
    # maintenance, according to the schedule.
    sql_sched = """SELECT n.netboxid, n.deviceid, n.sysname, NULL AS subid
        FROM maint m INNER JOIN netbox n ON (n.netboxid::text = m.value)
        WHERE m.key = 'netbox' AND m.state = 'active'

        UNION

        SELECT n.netboxid, n.deviceid, n.sysname, NULL AS subid
        FROM maint m INNER JOIN netbox n ON (n.roomid = m.value)
        WHERE m.key = 'room' AND m.state = 'active'

        UNION

        SELECT n.netboxid, n.deviceid, n.sysname, NULL AS subid
        FROM maint m INNER JOIN netbox n ON (n.roomid IN
            (SELECT roomid FROM room WHERE locationid = m.value))
        WHERE m.key = 'location' AND m.state = 'active'

        UNION

        SELECT n.netboxid, n.deviceid, n.sysname, m.value AS subid
        FROM maint m INNER JOIN netbox n ON (n.netboxid IN
            (SELECT netboxid FROM service WHERE
                serviceid::text LIKE m.value))
        WHERE m.key = 'service' AND m.state = 'active'"""

    # The full SQL is a set operation to select all boxes that are
    # currently on maintenance and subtracts those that are supposed
    # to be on maintenance - resulting in a list of boxes that should
    # be taken off maintenance immediately.
    sql_full = "(%s) \n EXCEPT \n (%s)" % (sql_actual, sql_sched)
    db.execute(sql_full)

    target = 'eventEngine'
    subsystem = 'maintenance'
    source = subsystem
    severity = 50
    eventtype = 'maintenanceState'
    state = 'e'
    value = 0

    for (netboxid, deviceid, sysname, subid) in db.fetchall():
        if netboxid in boxes_off_maintenance:
            # MaintenenceOff-events posted during this run might not
            # have been processed by eventEngine yet. We discard these
            # boxes here.
            continue

        # If it's a service, we have to set subid also
        if subid is None:
            _logger.info("Box %s (%d) is on unscheduled maintenance. "
                         "Taking off maintenance now.", sysname, netboxid)
            subid = False
        else:
            _logger.info(
                "Service (%d) at box %s (%d) is on unscheduled maintenance. "
                "Taking off maintenance...", subid, sysname, netboxid)
            subid = int(subid)

        # Create event
        event = nav.event.Event(
            source=source, target=target,
            deviceid=deviceid, netboxid=netboxid, subid=subid,
            eventtypeid=eventtype, state=state, value=value, severity=severity)

        result = event.post()
        _logger.debug("Event: %s, Result: %s", event, result)

    # Commit transaction
    _get_dbconn().commit()


def check_devices_on_maintenance():
    """Start the main logic for checking maintenance tasks."""
    schedule()
    check_tasks_without_end()
    events = []
    maxdate_boxes = {}
    check_state(events, maxdate_boxes)
    boxes_off_maintenance = []
    send_event(events, maxdate_boxes, boxes_off_maintenance)
    remove_forgotten(boxes_off_maintenance)

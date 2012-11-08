#!/usr/bin/env python
#
# Copyright 2003-2005 Norwegian University of Science and Technology
# Copyright 2006, 2008, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""
This program dispatches maintenance events according to the maintenance
schedule in NAVdb.
"""
import datetime
import logging
import os.path
import sys
import nav.db
import nav.event
import nav.logs

logfile = os.path.join(nav.path.localstatedir, 'log', 'maintengine.log')
logformat = "[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s"
logger = logging.getLogger('maintengine')

INFINITY = datetime.datetime.max

# Placeholders
events = []
states = ['scheduled', 'active', 'passed', 'canceled']
debug = False
boxesOffMaintenance = []
maxdate_boxes = {}

dbconn = nav.db.getConnection('eventEngine', 'manage')
# Make sure isolation level is "read committed", not "serialized"
dbconn.set_isolation_level(1)
db = dbconn.cursor()


def loginit():
    """Initialize logging setup"""

    global _loginited
    try:
        # Make sure we don't initialize logging setup several times (in case
        # of module reloads and such)
        if _loginited:
            return
    except:
        pass

    root = logging.getLogger('')

    formatter = logging.Formatter(logformat)
    try:
        handler = logging.FileHandler(logfile)
    except IOError, e:
        # Most likely, we were denied access to the log file.
        # We silently ignore it and log nothing :-P
        pass
    else:
        handler.setFormatter(formatter)
        root.addHandler(handler)
        nav.logs.set_log_levels()
        _loginited = True


def schedule():
    """Check if there are maintenance tasks to be schedule"""

    sql = """UPDATE maint_task SET state = 'scheduled'
        WHERE state IS NULL
        OR state NOT IN ('scheduled', 'active', 'passed', 'canceled')"""
    db.execute(sql)
    dbconn.commit()


def get_tasks_and_boxes_without_end():
    """Collect all netboxes from maintenance tasks that do not have a defined
        end time.  Place them in a dictionary with maintenance identity as key
        and a list of affected netboxes for each task."""
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
        # Use maintenance key as key for netboxes that are affected by
        # the maintenance task.
        if maint_id in tasks_and_boxes:
            tasks_and_boxes[maint_id].extend(netbox_ids)
        else:
            tasks_and_boxes[maint_id] = netbox_ids
    return tasks_and_boxes


def check_tasks_without_end():
    """Loop thru all maintenance tasks without a defined end time, and end the
    task if all boxes included in the task have been up for longer than an hour."""
    tasks_and_boxes = get_tasks_and_boxes_without_end()
    # Loop thru all maintenance tasks and check if the affected boxes
    # have been up for at least an hour.
    for (maint_id, netbox_ids) in tasks_and_boxes.iteritems():
        boxes_still_on_maint = []
        for box_id in netbox_ids:
            sql = """SELECT up, upsince
                        FROM netbox
                        WHERE netboxid = %s"""
            db.execute(sql, (box_id,))
            (up, upsince,) = db.fetchone()
            if not up or (up and up == 'n'):
                # Boxstate is unknown or box is down.
                boxes_still_on_maint.append(str(box_id))
            elif up and up == 'y' and upsince:
                # Box is up
                end_time_to_check = (datetime.datetime(upsince.year, upsince.month,
                                                        upsince.day, upsince.hour,
                                                        upsince.minute, upsince.second)
                                        + datetime.timedelta(hours=1))
                if end_time_to_check > datetime.datetime.now():
                    # Box have not been up for an hour yet.
                    boxes_still_on_maint.append(str(box_id))
        if len(boxes_still_on_maint) > 0:
            # Some boxes are still down...
            logger.debug('Maintenance task %d: Boxes %s are still on maintenance' %
                         (maint_id, ", ".join(boxes_still_on_maint)))
        else:
            # All affected boxes for this maintenance task have been up again for
            # at least an hour.
            time_now = datetime.datetime.now()
            logger.warn("Maintenance task %d: Set end at %s" % (maint_id, str(time_now)))
            sql = """UPDATE maint_task SET maint_end = %s WHERE maint_taskid = %s"""
            db.execute(sql, (time_now, maint_id,))
            dbconn.commit()


def check_state():
    """Checks if there are some maintenance tasks to be set active or
    passed."""

    sql = """SELECT maint_taskid FROM maint_task
        WHERE maint_start < NOW() AND state = 'scheduled'"""
    db.execute(sql)
    for (taskid,) in db.fetchall():
        e = {}
        e['type'] = 'active'
        e['taskid'] = taskid
        events.append(e)

    sql = """SELECT maint_taskid, maint_end FROM maint_task
        WHERE maint_end < NOW() AND state = 'active'"""
    db.execute(sql)
    for (taskid, maint_end) in db.fetchall():
        e = {}
        e['type'] = 'passed'
        e['taskid'] = taskid
        e['maint_end'] = maint_end
        events.append(e)

    # Get boxes that should still stay on maintenance
    sql = """SELECT max(maint_end) AS maint_end, key, value
        FROM maint_task INNER JOIN maint_component USING (maint_taskid)
        WHERE state = 'active' AND maint_end > NOW()
        GROUP BY key, value"""
    db.execute(sql)
    for (maint_end, key, value) in db.fetchall():
        if key in ('room', 'location'):
            if key == 'location':
                sql = """SELECT netboxid FROM netbox
                    INNER JOIN room USING (roomid)
                    WHERE locationid = %s"""
            if key == 'room':
                sql = """SELECT netboxid FROM netbox
                    WHERE roomid = %s"""
            db.execute(sql, (value,))
            boxids = [boxid for (boxid,) in db.fetchall()]
        elif key == 'service':
            sql = "SELECT netboxid FROM service WHERE serviceid = %s"
            db.execute(sql, (int(value),))
            result = db.fetchone()
            if result:
                (netboxid,) = result
                boxids = [netboxid]
        elif key == 'netbox':
            boxids = [value]
        for boxid in boxids:
            if boxid in maxdate_boxes and maxdate_boxes[boxid] > maint_end:
                continue
            maxdate_boxes[boxid] = maint_end


def send_event():
    """Sends events to the event queue."""

    for e in events:
        type = e['type']
        taskid = e['taskid']

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
            if type == 'active':
                state = 's'  # s = start
                value = 100
            elif type == 'passed':
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

                    logger.debug("location query: %s", sql % data)
                    db.execute(sql, data)
                    logger.debug("location number of results: %d", db.rowcount)
                elif key == 'room':
                    sql = """SELECT netboxid, sysname, deviceid
                        FROM netbox
                        WHERE roomid = %(roomid)s"""
                    data = {'roomid': val}

                    logger.debug("room query: %s", sql % data)
                    db.execute(sql, data)
                    logger.debug("room number of results: %d", db.rowcount)

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

                logger.debug("netbox query: %s", sql % data)
                db.execute(sql, data)
                logger.debug("netbox number of results: %d", db.rowcount)
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

                logger.debug("service query: %s", sql % data)
                db.execute(sql, data)
                logger.debug("service number of results: %d", db.rowcount)
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
                if type == 'passed' and netbox['netboxid'] in maxdate_boxes:
                    if maxdate_boxes[netbox['netboxid']] > e['maint_end']:
                        logger.debug("Skip stop event for netbox %(id)s. It's on maintenance until %(date)s." % {
                            'id': netbox['netboxid'],
                            'date': e['maint_end'],
                        })
                        continue
                # Append to list of boxes taken off maintenance during this run
                if type == 'passed':
                    boxesOffMaintenance.append(netbox['netboxid'])

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
                logger.debug("Event: %s, Result: %s", event, result)

        # Update state
        sql = """UPDATE maint_task
            SET state = %(state)s
            WHERE maint_taskid = %(maint_taskid)s"""
        data = {'state': type,
                'maint_taskid': taskid}
        db.execute(sql, data)

        # Commit transaction
        dbconn.commit()


def remove_forgotten():
    """
    Remove 'forgotten' netboxes from their maintenance state.

    Sometimes, like when netboxes have been deleted from a maintenance task
    during its active maintenance window, we will no longer know that the box
    has gone on maintenenance and should be taken off. This function takes all
    'forgotten' netboxes off maintenance.

    """

    # This SQL retrieves a list of boxes that are currently on
    # maintenance, according to the alert history.
    sqlactual = """SELECT ah.netboxid, ah.deviceid, n.sysname, subid 
        FROM alerthist ah LEFT JOIN netbox n USING (netboxid)
        WHERE eventtypeid='maintenanceState' AND netboxid IS NOT NULL
        AND end_time = 'infinity'"""

    # This SQL retrieves a list of boxes that are supposed to be on
    # maintenance, according to the schedule.
    sqlsched = """SELECT n.netboxid, n.deviceid, n.sysname, NULL AS subid
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
    sqlfull = "(%s) \n EXCEPT \n (%s)" % (sqlactual, sqlsched)
    db.execute(sqlfull)

    target = 'eventEngine'
    subsystem = 'maintenance'
    source = subsystem
    severity = 50
    eventtype = 'maintenanceState'
    state = 'e'
    value = 0

    for (netboxid, deviceid, sysname, subid) in db.fetchall():
        if netboxid in boxesOffMaintenance:
            # MaintenenceOff-events posted during this run might not
            # have been processed by eventEngine yet. We discard these
            # boxes here.
            continue

        # If it's a service, we have to set subid also
        if subid is None:
            logger.info("Box %s (%d) is on unscheduled maintenance. " +
                        "Taking off maintenance now.", sysname, netboxid)
            subid = False
        else:
            logger.info("Service (%d) at box %s (%d) is on unscheduled " +
                        "maintenance. Taking off maintenance...",
                        subid, sysname, netboxid)
            subid = int(subid)

        # Create event
        event = nav.event.Event(source=source, target=target,
            deviceid=deviceid, netboxid=netboxid, subid=subid,
            eventtypeid=eventtype, state=state, value=value, severity=severity)

        result = event.post()
        logger.debug("Event: %s, Result: %s", event, result)

    # Commit transaction
    dbconn.commit()


if __name__ == '__main__':
    loginit()
    schedule()
    check_tasks_without_end()
    check_state()
    send_event()
    remove_forgotten()

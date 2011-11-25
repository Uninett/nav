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

from calendar import HTMLCalendar
from itertools import groupby
from datetime import date
from time import strftime

from django.core.urlresolvers import reverse
from django.utils.html import conditional_escape
from django.db import connection

def components_for_task(task_id):
    # Raw SQL, as doing this in the Django ORM is not that easy, and would
    # probably be harder to read.
    cursor = connection.cursor()
    cursor.execute("""SELECT key, value,
            COALESCE(location.locationid, room.roomid, netbox.netboxid::varchar, service.serviceid::varchar) AS info_found,
            location.locationid, location.descr AS locationdescr,
            room.roomid, room.descr AS roomdescr,
            netbox.netboxid, netbox.sysname, netbox.ip,
            service.serviceid, service.handler
        FROM maint_component
        LEFT OUTER JOIN service ON (key = 'service' AND value = service.serviceid::varchar)
        LEFT OUTER JOIN netbox ON (
            key = 'netbox' AND value = netbox.netboxid::varchar OR
            key = 'service' AND service.netboxid = netbox.netboxid
        )
        LEFT OUTER JOIN room ON (
            key = 'room' AND value = room.roomid OR
            (key = 'netbox' OR key = 'service') AND netbox.roomid = room.roomid
        )
        LEFT OUTER JOIN location ON (
            key = 'location' AND value = location.locationid OR
            key <> 'location' AND room.locationid = location.locationid
        )
        WHERE maint_taskid = %s""", (task_id,))
    return [
        dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()
    ]

def components_for_keys(keys):
    # Raw SQL, as doing this in the Django ORM is not that easy, and would
    # probably be harder to read.
    cursor = connection.cursor()
    cursor.execute("""SELECT 'service' AS key, service.serviceid::varchar AS value,
        COALESCE(service.serviceid::varchar) AS info_found,
        location.locationid, location.descr AS locationdescr,
        room.roomid, room.descr AS roomdescr,
        netbox.netboxid, netbox.sysname, netbox.ip,
        service.serviceid, service.handler
        FROM service
        INNER JOIN netbox USING (netboxid)
        INNER JOIN room USING (roomid)
        INNER JOIN location USING (locationid)
        WHERE serviceid = ANY (%s::int[])

        UNION

        SELECT 'netbox' AS key, netbox.netboxid::varchar AS value,
        COALESCE(netbox.netboxid::varchar) AS info_found,
        location.locationid, location.descr AS locationdescr,
        room.roomid, room.descr AS roomdescr,
        netbox.netboxid, netbox.sysname, netbox.ip,
        NULL AS serviceid, NULL AS handler
        FROM netbox
        INNER JOIN room USING (roomid)
        INNER JOIN location USING (locationid)
        WHERE
        netboxid = ANY (%s::int[])

        UNION

        SELECT 'room' AS key, room.roomid AS value,
        COALESCE(room.roomid) AS info_found,
        location.locationid, location.descr AS locationdescr,
        room.roomid, room.descr AS roomdescr,
        NULL AS netboxid, NULL AS sysname, NULL AS ip,
        NULL AS serviceid, NULL AS handler
        FROM room
        INNER JOIN location USING (locationid)
        WHERE
        room.roomid = ANY (%s)

        UNION

        SELECT 'location' AS key, location.locationid AS value,
        COALESCE(location.locationid) AS info_found,
        location.locationid, location.descr AS locationdescr,
        NULL as roomid, NULL as roomdescr, NULL AS netboxid, NULL AS sysname, NULL AS ip, NULL AS serviceid, NULL AS handler
        FROM location
        WHERE locationid = ANY (%s)""", (
            keys['service'],
            keys['netbox'],
            keys['room'],
            keys['location']
        ))
    return [
        dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()
    ]

def task_component_trails(components):
    trails = []
    for comp in components:
        title = comp['key']
        if title == 'netbox':
            title = 'IP Device'
        trail = []
        if not comp['info_found']:
            trail.append({
                'url': None,
                'title': None,
                'name': "ID %s (Details not available)" % comp['value'],
            })
        else:
            if comp['key'] in ('location', 'room', 'netbox', 'service'):
                trail.append({
                    'url': reverse('report-room-location', args=[comp['locationid']]),
                    'title': comp['locationdescr'],
                    'name': comp['locationid'],
                })
            if comp['key'] in ('room', 'netbox', 'service'):
                trail.append({
                    'url': reverse('report-netbox-room', args=[comp['roomid']]),
                    'title': comp['roomdescr'],
                    'name': comp['roomid'],
                })
            if comp['key'] in ('netbox', 'service'):
                trail.append({
                    'url': reverse('ipdevinfo-details-by-name', args=[comp['sysname']]),
                    'title': comp['ip'],
                    'name': comp['sysname'],
                })
            if comp['key'] == 'service':
                trail.append({
                    'url': None,
                    'title': None,
                    'name': comp['handler'],
                })
            if comp['key'] == 'module':
                trail.append({
                    'url': None,
                    'title': None,
                    'name': "(Warning: Modules can no longer be a maintenance component.)",
                })
        trails.append({
            'title': title,
            'trail': trail,
        })
    return trails

class MaintenanceCalendar(HTMLCalendar):
    def __init__(self, tasks):
        super(MaintenanceCalendar, self).__init__(0)
        self.tasks = self.group_by_start(tasks)

    def formatday(self, day, weekday):
        if day != 0:
            this_day = date(self.year, self.month, day)
            css = self.cssclasses[weekday]
            if date.today() == this_day:
                css += " today"
            if this_day in self.tasks:
                css += " task"
                content = ["<ul>"]
                for task in self.tasks[this_day]:
                    desc = task.description
                    if len(desc) > 16:
                        desc = desc[:16]
                    content.append("<li>")
                    content.append("%s " % strftime('%H:%M', task.start_time.timetuple()))
                    content.append('<a href="%s">' % reverse('maintenance-view', args=[task.id]))
                    content.append(conditional_escape(desc))
                    content.append("</a>")
                    content.append("</li>")
                content.append("</ul>")
                return self.day_cell(css, "%d %s" % (day, ''.join(content)))
            return self.day_cell(css, day)
        return self.day_cell('noday', '&nbsp;')

    def formatweekheader(self):
        header = super(MaintenanceCalendar, self).formatweekheader()
        return header.replace('<tr>', '<tr class="weekheader">', 1)

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(MaintenanceCalendar, self).formatmonth(year, month)

    def group_by_start(self, tasks):
        field = lambda task: task.start_time.date()
        return dict([(start_time, list(items)) for start_time, items in groupby(tasks, field)])

    def day_cell(self, css_class, content):
        return '<td class="%s">%s</td>' % (css_class, content)

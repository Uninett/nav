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

def task_components(task):
    components = []
    for comp in task['components']:
        title = comp['key']
        if title == 'netbox':
            title = 'IP Device'
        trail = []
        if not comp['info']:
            trail.append({
                'url': None,
                'title': None,
                'name': "ID %s (Details not available)" % comp['value'],
            })
        else:
            if comp['key'] in ('location', 'room', 'netbox', 'service'):
                trail.append({
                    'url': reverse('report-room-location', args=[comp['info']['locationid']]),
                    'title': comp['info']['locationdescr'],
                    'name': comp['info']['locationid'],
                })
            if comp['key'] in ('room', 'netbox', 'service'):
                trail.append({
                    'url': reverse('report-netbox-room', args=[comp['info']['roomid']]),
                    'title': comp['info']['roomdescr'],
                    'name': comp['info']['roomid'],
                })
            if comp['key'] in ('netbox', 'service'):
                trail.append({
                    'url': reverse('ipdevinfo-details-by-name', args=[comp['info']['sysname']]),
                    'title': comp['info']['ip'],
                    'name': comp['info']['sysname'],
                })
            if comp['key'] == 'service':
                trail.append({
                    'url': None,
                    'title': None,
                    'name': comp['info']['handler'],
                })
            if comp['key'] == 'module':
                trail.append({
                    'url': None,
                    'title': None,
                    'name': "(Warning: Modules can no longer be a maintenance component.)",
                })
        components.append({
            'title': title,
            'trail': trail,
        })
    return components

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

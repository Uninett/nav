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

from nav.models.manage import Netbox, Room, Location
from nav.models.service import Service

PRIMARY_KEY_INTEGER = ('netbox', 'service')

FIELD_KEYS = {
    'service': {
        'netbox': 'netbox__',
        'room': 'netbox__room__',
        'location': 'netbox__room__location__',
    },
    'netbox': {
        'netbox': '',
        'room': 'room__',
        'location': 'room__location__',
    },
    'room': {
        'room': '',
        'location': 'location__',
    },
    'location': {
        'location': '',
    }
}

def get_component_keys_from_post(post):
    remove = {}
    raw_component_keys = {
        'service': post.getlist('service'),
        'netbox': post.getlist('netbox'),
        'room': post.getlist('room'),
        'location': post.getlist('location'),
    }
    raw_component_keys['location'].extend(post.getlist('loc'))
    if 'remove' in post:
        remove = {
            'service': post.getlist('remove_service'),
            'netbox': post.getlist('remove_netbox'),
            'room': post.getlist('remove_room'),
            'location': post.getlist('remove_location'),
        }
    component_keys = {'service': [], 'netbox': [], 'room': [], 'location': []}
    for key in raw_component_keys:
        for value in raw_component_keys[key]:
            if not remove or value not in remove[key]:
                if key in PRIMARY_KEY_INTEGER:
                    value = int(value)
                if value not in component_keys[key]:
                    component_keys[key].append(value)
    return component_keys

def components_for_keys(component_keys):
    component_data = {}
    component_data['service'] = Service.objects.filter(id__in=component_keys['service']).values(
        'id', 'handler', 'netbox__id', 'netbox__sysname', 'netbox__ip',
        'netbox__room__id', 'netbox__room__description',
        'netbox__room__location__id', 'netbox__room__location__description')
    component_data['netbox'] = Netbox.objects.filter(id__in=component_keys['netbox']).values(
        'id', 'sysname', 'ip', 'room__id', 'room__description',
        'room__location__id', 'room__location__description')
    component_data['room'] = Room.objects.filter(id__in=component_keys['room']).values(
        'id', 'description', 'location__id', 'location__description')
    component_data['location'] = Location.objects.filter(id__in=component_keys['location']).values(
        'id', 'description')
    return component_data

def task_component_trails(component_keys, components):
    trails = []
    for key in component_keys:
        title = key
        if title == 'netbox':
            title = 'IP Device'
        for pkey in component_keys[key]:
            trail = []
            try:
                comp = components[key][pkey]
            except KeyError:
                trail.append({
                    'url': None,
                    'title': None,
                    'name': "ID %s (Details not available)" % pkey,
                })
            else:
                if key in ('location', 'room', 'netbox', 'service'):
                    location_id = comp[FIELD_KEYS[key]['location'] + "id"]
                    location_description = comp[FIELD_KEYS[key]['location'] + "description"]
                    trail.append({
                        'url': reverse('report-room-location', args=[location_id]),
                        'title': location_description,
                        'name': location_id,
                    })
                if key in ('room', 'netbox', 'service'):
                    room_id = comp[FIELD_KEYS[key]['room'] + "id"]
                    room_description = comp[FIELD_KEYS[key]['room'] + "description"]
                    trail.append({
                        'url': reverse('report-netbox-room', args=[room_id]),
                        'title': room_description,
                        'name': room_id,
                    })
                if key in ('netbox', 'service'):
                    netbox_sysname = comp[FIELD_KEYS[key]['netbox'] + "sysname"]
                    netbox_ip = comp[FIELD_KEYS[key]['netbox'] + "ip"]
                    trail.append({
                        'url': reverse('ipdevinfo-details-by-name', args=[netbox_sysname]),
                        'title': netbox_ip,
                        'name': netbox_sysname,
                    })
                if key == 'service':
                    trail.append({
                        'url': None,
                        'title': None,
                        'name': comp['handler'],
                    })
            trails.append({
                'id': pkey,
                'type': key,
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

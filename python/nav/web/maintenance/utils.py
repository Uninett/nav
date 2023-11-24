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

from calendar import HTMLCalendar
from datetime import date, datetime, timedelta
from time import strftime

from django.urls import reverse
from django.utils.html import conditional_escape

from nav.models.manage import Netbox, Room, Location, NetboxGroup
from nav.models.service import Service
from nav.models.msgmaint import MaintenanceTask

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
    },
}

NAVPATH = [
    ('Home', '/'),
    ('Maintenance', '/maintenance/'),
]

TITLE = "NAV - Maintenance"

INFINITY = datetime.max


def task_form_initial(task=None, start_time=None):
    if task:
        initial = {
            'start_time': task.start_time,
            'end_time': task.end_time,
            'description': task.description,
        }
    else:
        if start_time:
            start_time = datetime.strptime(start_time, "%Y-%m-%d")
        else:
            start_time = datetime.today()
        end_time = start_time + timedelta(days=1)
        initial = {
            'start_time': start_time.strftime("%Y-%m-%d %H:%M"),
            'end_time': end_time.strftime("%Y-%m-%d %H:%M"),
        }
    return initial


def infodict_by_state(task):
    if (
        task.state == MaintenanceTask.STATE_SCHEDULED
        and task.start_time > datetime.now()
    ):
        state = 'planned'
        navpath = NAVPATH + [('Planned tasks', reverse('maintenance-planned'))]
    elif task.state in (MaintenanceTask.STATE_PASSED, MaintenanceTask.STATE_CANCELED):
        state = 'historic'
        navpath = NAVPATH + [('Historic tasks', reverse('maintenance-historic'))]
    else:
        state = 'active'
        navpath = NAVPATH + [('Active tasks', reverse('maintenance-active'))]
    return {
        'active': {state: True},
        'navpath': navpath,
    }


def get_component_keys(post):
    remove = {}
    errors = []
    raw_component_keys = {
        'service': post.getlist('service'),
        'netbox': post.getlist('netbox'),
        'room': post.getlist('room'),
        'location': post.getlist('location'),
        'netboxgroup': post.getlist('netboxgroup'),
    }
    raw_component_keys['location'].extend(post.getlist('loc'))
    if 'remove' in post:
        remove = {
            'service': post.getlist('remove_service'),
            'netbox': post.getlist('remove_netbox'),
            'room': post.getlist('remove_room'),
            'location': post.getlist('remove_location'),
            'netboxgroup': post.getlist('remove_netboxgroup'),
        }
    component_keys = {
        'service': [],
        'netbox': [],
        'room': [],
        'location': [],
        'netboxgroup': [],
    }
    for key in raw_component_keys:
        for value in raw_component_keys[key]:
            if not remove or value not in remove[key]:
                if key in PRIMARY_KEY_INTEGER:
                    if not value.isdigit():
                        errors.append(key + ": argument needs to be a number")
                        continue
                    value = int(value)
                if value not in component_keys[key]:
                    component_keys[key].append(value)
    return component_keys, errors


def components_for_keys(component_keys):
    component_data = {}
    component_data_errors = []
    if component_keys['service']:
        component_data['service'] = Service.objects.filter(
            id__in=component_keys['service']
        ).values(
            'id',
            'handler',
            'netbox__id',
            'netbox__sysname',
            'netbox__ip',
            'netbox__room__id',
            'netbox__room__description',
            'netbox__room__location__id',
            'netbox__room__location__description',
        )
        if not component_data['service']:
            component_data_errors.append(
                "service: no elements with the given identifiers found"
            )
    if component_keys['netbox']:
        component_data['netbox'] = Netbox.objects.filter(
            id__in=component_keys['netbox']
        ).values(
            'id',
            'sysname',
            'ip',
            'room__id',
            'room__description',
            'room__location__id',
            'room__location__description',
        )
        if not component_data['netbox']:
            component_data_errors.append(
                "netbox: no elements with the given identifiers found"
            )
    if component_keys['room']:
        component_data['room'] = Room.objects.filter(
            id__in=component_keys['room']
        ).values('id', 'description', 'location__id', 'location__description')
        if not component_data['room']:
            component_data_errors.append(
                "room: no elements with the given identifiers found"
            )
    if component_keys['location']:
        component_data['location'] = Location.objects.filter(
            id__in=component_keys['location']
        ).values('id', 'description')
        if not component_data['location']:
            component_data_errors.append(
                "location: no elements with the given identifiers found"
            )
    if component_keys['netboxgroup']:
        component_data['netboxgroup'] = NetboxGroup.objects.filter(
            id__in=component_keys['netboxgroup']
        ).values('id', 'description')
        if not component_data['netboxgroup']:
            component_data_errors.append(
                "netboxgroup: no elements with the given identifiers found"
            )
    return component_data, component_data_errors


def structure_component_data(component_data):
    components = {}
    for key in component_data:
        for component in component_data[key]:
            pkey = component['id']
            if key not in components:
                components[key] = {}
            components[key][pkey] = component
    return components


def task_component_trails(component_keys, components):
    """Create the 'trail' of selected components

    An IP Device would have a trail consisting of a location, room and the
    device itself, and a room would have a trail consisting of a location and
    the room itself.

    Ex:
    IP Device: <location> -> <room> -> <device>
    """

    # Mapping for changing the title of the trail.
    title_mapping = {'netbox': 'IP Device', 'netboxgroup': 'Device Group'}

    trails = []
    for key in component_keys:
        title = title_mapping.get(key, key)
        for pkey in component_keys[key]:
            trail = []
            try:
                comp = components[key][pkey]
            except KeyError:
                trail.append(
                    {
                        'url': None,
                        'title': None,
                        'name': "ID %s (Component was deleted)" % pkey,
                    }
                )
            else:
                if key in ('location', 'room', 'netbox', 'service'):
                    location_id = comp[FIELD_KEYS[key]['location'] + "id"]
                    location_description = comp[
                        FIELD_KEYS[key]['location'] + "description"
                    ]
                    trail.append(
                        {
                            'url': reverse('location-info', args=[location_id]),
                            'title': location_description,
                            'name': location_id,
                        }
                    )
                if key in ('room', 'netbox', 'service'):
                    room_id = comp[FIELD_KEYS[key]['room'] + "id"]
                    room_description = comp[FIELD_KEYS[key]['room'] + "description"]
                    trail.append(
                        {
                            'url': reverse('room-info', args=[room_id]),
                            'title': room_description,
                            'name': room_id,
                        }
                    )
                if key in ('netbox', 'service'):
                    netbox_sysname = comp[FIELD_KEYS[key]['netbox'] + "sysname"]
                    netbox_ip = comp[FIELD_KEYS[key]['netbox'] + "ip"]
                    trail.append(
                        {
                            'url': reverse(
                                'ipdevinfo-details-by-name', args=[netbox_sysname]
                            ),
                            'title': netbox_ip,
                            'name': netbox_sysname,
                        }
                    )
                if key == 'service':
                    trail.append(
                        {
                            'url': None,
                            'title': None,
                            'name': comp['handler'],
                        }
                    )
                if key == 'netboxgroup':
                    trail.append(
                        {
                            'url': reverse('netbox-group-detail', args=[comp['id']]),
                            'title': '',
                            'name': comp['id'],
                        }
                    )
            trails.append(
                {
                    'id': pkey,
                    'type': key,
                    'title': title,
                    'trail': trail,
                }
            )
    return trails


class MaintenanceCalendar(HTMLCalendar):
    START = 'start'
    END = 'end'
    CONTINUED = 'continued'
    CONTINUED_MONTH = 'continued_month'

    def __init__(self, tasks):
        super(MaintenanceCalendar, self).__init__(0)
        self.tasks = self.group_span(tasks)
        self.bg_cache = {}
        self.bg_num = 0

    def bg_color(self, key):
        if key in self.bg_cache:
            return self.bg_cache[key]
        self.bg_num += 1
        if self.bg_num > 5:
            self.bg_num = 1
        self.bg_cache[key] = "bg%ilight" % self.bg_num
        return self.bg_cache[key]

    def formatweekheader(self):
        header = super(MaintenanceCalendar, self).formatweekheader()
        return header.replace('<tr>', '<tr class="weekheader">', 1)

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(MaintenanceCalendar, self).formatmonth(year, month)

    def formatday(self, day, weekday):
        def format_task(task_dict):
            content = []
            group = task_dict['grouping']
            task = task_dict['task']
            desc = task.description
            if len(desc) >= 25:
                desc = desc[:20] + "(...)"
            formated_start = strftime('%H:%M', task.start_time.timetuple())
            formated_end = strftime('%H:%M', task.end_time.timetuple())
            content.append('<li class="%s">' % group)
            content.append(
                '<a class="task_%(id)s %(color)s" href="%(url)s">'
                % {
                    'id': task.pk,
                    'color': self.bg_color(task.pk),
                    'url': reverse('maintenance-view', args=[task.pk]),
                }
            )
            if group == self.CONTINUED_MONTH:
                content.append("... ")
                content.append(conditional_escape(desc))
            elif group == self.START:
                content.append("%s " % formated_start)
                content.append(conditional_escape(desc))
            elif group == self.END:
                content.append('<span>%s</span>' % formated_end)
            else:
                content.append('&nbsp;')
            content.append("</a>")
            return ''.join(content)

        if day != 0:
            this_day = date(self.year, self.month, day)
            css = self.cssclasses[weekday]
            dayurl = '<a href="%s" class="daynumber">%d</a>' % (
                reverse('maintenance-new-date', args=[this_day]),
                day,
            )
            if date.today() == this_day:
                css += " today"
            if this_day in self.tasks:
                css += " task"
                content = ["<ul>"]
                for index in self.tasks[this_day]:
                    task_dict = self.tasks[this_day][index]
                    if task_dict:
                        content.append(format_task(task_dict))
                    else:
                        content.append("<li>&nbsp;")
                    content.append("</li>")
                content.append("</ul>")
                return self.day_cell(css, "%s %s" % (dayurl, ''.join(content)))
            return self.day_cell(css, dayurl)
        return self.day_cell('noday', '&nbsp;')

    def group_span(self, tasks):
        grouped = {}
        task_index = {}
        for task in tasks:
            day = task.start_time.date()
            end_day = task.end_time.date()
            if end_day >= INFINITY.date():
                # Need to stop somewhere when tasks do not specify end date.
                end_day = task.start_time.date() + timedelta(weeks=4)
            while day <= end_day:
                if day not in grouped:
                    grouped[day] = {}
                if task.pk in task_index:
                    index = task_index[task.pk]
                    for ii in range(index):
                        if ii not in grouped[day]:
                            grouped[day][ii] = None
                else:
                    index = len(grouped[day])
                    for ii in range(index):
                        if ii not in grouped[day] or not grouped[day][ii]:
                            index = ii
                            break
                    task_index[task.pk] = index

                grouping = self.CONTINUED
                if task.start_time.month < day.month and day.day == 1:
                    grouping = self.CONTINUED_MONTH
                elif day == task.start_time.date():
                    grouping = self.START
                elif day == task.end_time.date():
                    grouping = self.END

                grouped[day][index] = {'task': task, 'grouping': grouping}
                day += timedelta(days=1)
        return grouped

    def day_cell(self, css_class, content):
        return '<td class="%s">%s</td>' % (css_class, content)

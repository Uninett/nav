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
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from time import strftime
from typing import Union, List, Iterator

from django.db import models
from django.db.models import IntegerField
from django.urls import reverse
from django.utils.html import conditional_escape

from nav.models.fields import LegacyGenericForeignKey
from nav.models.manage import Netbox, Room, Location, NetboxGroup
from nav.models.service import Service
from nav.models.msgmaint import MaintenanceTask, MaintenanceComponent

ALLOWED_COMPONENTS = ('service', 'netbox', 'room', 'location', 'netboxgroup')

COMPONENTS_WITH_INTEGER_PK = [
    table
    for table in ALLOWED_COMPONENTS
    if isinstance(
        LegacyGenericForeignKey.get_model_class(table)._meta.get_field('id'),
        IntegerField,
    )
]

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


@dataclass
class MissingComponent:
    """Represents a deleted component still associated with a task"""

    model_class: models.Model
    pk: Union[int, str]
    description: str

    @property
    def _meta(self):
        """Provides a fake `_meta` attribute for compatibility with Django model
        objects.
        """
        return self.model_class._meta

    def __str__(self):
        descr = self.description or self.pk
        return f"{descr} (Component was deleted)"


ComponentType = Union[Location, Room, Netbox, Service, NetboxGroup, MissingComponent]


def component_to_trail(component: ComponentType) -> List[ComponentType]:
    """Transforms a single component into a list of components that make up a trail for
    display purposes.
    """
    if isinstance(component, Room):
        return [component.location, component]
    if isinstance(component, Netbox):
        return [component.room.location, component.room, component]
    if isinstance(component, Service):
        return [
            component.netbox.room.location,
            component.netbox.room,
            component.netbox,
            component,
        ]
    return [component]


def get_components(task: MaintenanceTask) -> Iterator[ComponentType]:
    """Yields all components associated with a task, replacing deleted components with
    a MissingComponent instance.
    """
    relation: MaintenanceComponent
    for relation in task.maintenance_components.all():
        if relation.component is None:
            yield MissingComponent(
                model_class=relation.get_component_class(),
                pk=relation.value,
                description=relation.description,
            )
        else:
            yield relation.component


def get_component_keys(post):
    """Transforms GET/POST data into a dictionary of component keys.

    This would preferably be done by a Django Form class, but the original code
    predates Django.
    """
    remove = {}
    errors = []
    raw_component_keys = {key: post.getlist(key) for key in ALLOWED_COMPONENTS}
    raw_component_keys['location'].extend(post.getlist('loc'))
    if 'remove' in post:
        remove = {key: post.getlist(f"remove_{key}") for key in ALLOWED_COMPONENTS}
    component_keys = {key: [] for key in ALLOWED_COMPONENTS}
    for key in raw_component_keys:
        for value in raw_component_keys[key]:
            if not remove or value not in remove[key]:
                if key in COMPONENTS_WITH_INTEGER_PK:
                    if not value.isdigit():
                        errors.append(key + ": argument needs to be a number")
                        continue
                    value = int(value)
                if value not in component_keys[key]:
                    component_keys[key].append(value)
    return component_keys, errors


def get_component_name(model: models.Model):
    """Returns a short name for the component type based on its model class.

    Used as the input name for component keys in forms and APIs.

    Location is abbreviated to 'loc' to avoid XSS issues.
    """
    if model._meta.db_table == 'location':
        return 'loc'
    return model._meta.db_table


def get_components_from_keydict(
    component_keys: dict[str, List[Union[int, str]]],
) -> tuple[List[ComponentType], List[str]]:
    """Fetches components from a dictionary of component keys, typically as created
    from POST data.

    Returns a list of matched components and a list of errors encountered during the
    process.  Again, this would be better handled by a Django Form class.
    """
    components = []
    component_data_errors = []

    for key, values in component_keys.items():
        if not values:
            continue
        model_class = (
            LegacyGenericForeignKey.get_model_class(key)
            if key in ALLOWED_COMPONENTS
            else None
        )
        if not model_class:
            component_data_errors.append(f"{key}: invalid component type")
            continue

        objects = model_class.objects.filter(id__in=values)
        components.extend(objects)
        if not objects:
            component_data_errors.append(
                f"{key}: no elements with the given identifiers found"
            )
    return components, component_data_errors


def prefetch_and_group_components(
    component_type: models.Model,
    query_results: models.QuerySet,
    group_by: Union[models.Model, None] = None,
):
    """
    Prefetches the related model and groups components by the related model name.
    """
    if not group_by:
        return query_results

    group_by_name = group_by._meta.db_table

    if hasattr(query_results, 'prefetch_related') and hasattr(
        component_type, group_by_name
    ):
        query_results = query_results.prefetch_related(group_by_name)

    grouped_results = {}
    for component in query_results:
        group_by_model = getattr(component, group_by_name)
        group_name = str(group_by_model)

        if group_name not in grouped_results:
            grouped_results[group_name] = []
        grouped_results[group_name].append(component)

    return [(group, components) for group, components in grouped_results.items()]


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

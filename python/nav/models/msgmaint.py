# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django ORM wrapper for the NAV manage database"""

from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

from nav.models.fields import (
    VarcharField,
    LegacyGenericForeignKey,
    DateTimeInfinityField,
    INFINITY,
)
from nav.models import manage


class Message(models.Model):
    """From NAV Wiki: The table contains the messages registered
    in the messages tool. Each message has a timeframe for when
    it is published on the NAV main page."""

    id = models.AutoField(db_column='messageid', primary_key=True)
    title = VarcharField()
    description = models.TextField()
    tech_description = models.TextField(null=True, blank=True)
    publish_start = models.DateTimeField(default=timezone.now)
    publish_end = models.DateTimeField(default=datetime.now() + timedelta(days=7))
    author = VarcharField()
    last_changed = models.DateTimeField()
    replaces_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        db_column='replaces_message',
        related_name='replaced_by',
        null=True,
    )
    maintenance_tasks = models.ManyToManyField(
        'MaintenanceTask',
        through='MessageToMaintenanceTask',
        blank=True,
        related_name="messages",
    )

    class Meta(object):
        db_table = 'message'

    def __str__(self):
        return '"%s" by %s' % (self.title, self.author)


class MaintenanceTaskManager(models.Manager):
    """Custom manager for MaintenanceTask objects"""

    def current(self, relative_to=None):
        """Retrieves current maintenancen tasks

        Those are tasks whose time window matches the current time and that are
        not cancelled
        """
        now = relative_to or datetime.now()
        return (
            self.get_queryset()
            .exclude(state=MaintenanceTask.STATE_CANCELED)
            .filter(start_time__lte=now, end_time__gte=now)
        )

    def past(self, relative_to=None):
        """Retrieves past maintenance tasks"""
        now = relative_to or datetime.now()
        return self.get_queryset().filter(end_time__lt=now)

    def future(self, relative_to=None):
        """Retrieves future maintenance tasks"""
        now = relative_to or datetime.now()
        return self.get_queryset().filter(start_time__gt=now)

    def endless(self):
        """Retrieves tasks with an unspecified end time"""
        return self.get_queryset().filter(end_time__gte=INFINITY)


class MaintenanceTask(models.Model):
    """From NAV Wiki: The maintenance task created in the maintenance task
    tool."""

    objects = MaintenanceTaskManager()

    STATE_SCHEDULED = 'scheduled'
    STATE_ACTIVE = 'active'
    STATE_PASSED = 'passed'
    STATE_CANCELED = 'canceled'
    STATES = (
        (STATE_SCHEDULED, 'Scheduled'),
        (STATE_ACTIVE, 'Active'),
        (STATE_PASSED, 'Passed'),
        (STATE_CANCELED, 'Canceled'),
    )

    id = models.AutoField(db_column='maint_taskid', primary_key=True)
    start_time = models.DateTimeField(db_column='maint_start')
    end_time = DateTimeInfinityField(db_column='maint_end', blank=True)
    description = models.TextField()
    author = VarcharField()
    state = VarcharField(choices=STATES)

    class Meta(object):
        db_table = 'maint_task'

    def __str__(self):
        return '"%s" by %s' % (self.description, self.author)

    def full_representation(self):
        """
        Help function to represent a task with desc, start and end.
        """
        return '%s (%s - %s)' % (
            self.description,
            self.start_time,
            ('No end time' if self.is_endless() else self.end_time),
        )

    def get_components(self):
        """
        Returns the list of model objects involved in this task
        """
        return [c.component for c in self.maintenance_components.all()]

    def get_event_subjects(self):
        """
        Returns a list of the model objects, represented by this task,
        that can be the subjects of actual maintenanceState events.
        """
        subjects = []
        for component in self.get_components():
            if isinstance(component, (manage.Room, manage.NetboxGroup)):
                subjects.extend(component.netboxes.all())
            elif isinstance(component, manage.Location):
                for location in component.get_descendants(include_self=True):
                    subjects.extend(
                        manage.Netbox.objects.filter(room__location=location)
                    )
            elif component is None:
                continue  # no use in including deleted components
            else:
                subjects.append(component)

        return list(set(subjects))

    def is_endless(self):
        """Returns true if the task is endless"""
        return self.end_time >= INFINITY


class MaintenanceComponent(models.Model):
    """From NAV Wiki: The components that are put on maintenance in the
    maintenance tool."""

    id = models.AutoField(primary_key=True)  # Serial for faking primary key
    maintenance_task = models.ForeignKey(
        MaintenanceTask,
        on_delete=models.CASCADE,
        db_column='maint_taskid',
        related_name="maintenance_components",
    )
    key = VarcharField()
    value = VarcharField()
    description = VarcharField(null=True, blank=True)
    component = LegacyGenericForeignKey('key', 'value')

    class Meta(object):
        db_table = 'maint_component'
        unique_together = (('maintenance_task', 'key', 'value'),)  # Primary key

    def __str__(self):
        return '%s=%s' % (self.key, self.value)

    def get_component_class(self) -> models.Model:
        """Returns a Model class based on the database table name stored in key"""
        return LegacyGenericForeignKey.get_model_class(self.key)


class MessageToMaintenanceTask(models.Model):
    """From NAV Wiki: The connection between messages and related maintenance
    tasks."""

    id = models.AutoField(primary_key=True)  # Serial for faking primary key
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, db_column='messageid'
    )
    maintenance_task = models.ForeignKey(
        MaintenanceTask, on_delete=models.CASCADE, db_column='maint_taskid'
    )

    class Meta(object):
        db_table = 'message_to_maint_task'
        unique_together = (('message', 'maintenance_task'),)  # Primary key

    def __str__(self):
        return 'Message %s, connected to task %s' % (
            self.message,
            self.maintenance_task,
        )

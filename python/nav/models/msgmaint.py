# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django ORM wrapper for the NAV manage database"""

from django.db import models

from nav.models.fields import VarcharField

class Message(models.Model):
    """From MetaNAV: The table contains the messages registered in the messages
    tool. Each message has a timeframe for when it is published on the NAV main
    page."""

    id = models.AutoField(db_column='messageid', primary_key=True)
    title = VarcharField()
    description = models.TextField()
    tech_description = models.TextField()
    publish_start = models.DateTimeField()
    publish_end = models.DateTimeField()
    author = VarcharField()
    last_changed = models.DateTimeField()
    replaces_message = models.ForeignKey('self', db_column='replaces_message',
        related_name='replaced_by', null=True)
    maintenance_tasks = models.ManyToManyField('MaintenanceTask',
        through='MessageToMaintenanceTask')

    class Meta:
        db_table = 'message'

    def __unicode__(self):
        return u'"%s" by %s' % (self.title, self.author)

class MaintenanceTask(models.Model):
    """From MetaNAV: The maintenance task created in the maintenance task
    tool."""

    id = models.AutoField(db_column='maint_taskid', primary_key=True)
    start_time = models.DateTimeField(db_column='maint_start')
    end_time = models.DateTimeField(db_column='maint_end')
    description = models.TextField()
    author = VarcharField()
    state = VarcharField()

    class Meta:
        db_table = 'maint_task'

    def __unicode__(self):
        return u'"%s" by %s' % (self.description, self.author)

class MaintenanceComponent(models.Model):
    """From MetaNAV: The components that are put on maintenance in the
    maintenance tool."""

    id = models.AutoField(primary_key=True) # Serial for faking primary key
    maintenance_task = models.ForeignKey(MaintenanceTask,
        db_column='maint_taskid')
    key = VarcharField()
    value = VarcharField()

    class Meta:
        db_table = 'maint_component'
        unique_together = (('maint_task', 'key', 'value'),) # Primary key

    def __unicode__(self):
        return u'%s=%s' % (self.key, self.value)

class MessageToMaintenanceTask(models.Model):
    """From MetaNAV: The connection between messages and related maintenance
    tasks."""

    id = models.AutoField(primary_key=True) # Serial for faking primary key
    message = models.ForeignKey(Message, db_column='messageid',
        related_name='maintenance_tasks')
    maintenance_task = models.ForeignKey(MaintenanceTask,
        db_column='maint_taskid', related_name='messages')

    class Meta:
        db_table = 'message_to_maint_task'
        unique_together = (('message', 'maintenance_task'),) # Primary key

    def __unicode__(self):
        return u'Message %s, connected to task %s' % (
            self.message, self.maintenance_task)

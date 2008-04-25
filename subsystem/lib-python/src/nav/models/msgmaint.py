# -*- coding: utf-8 -*-
#
# Copyright 2007 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

"""Django ORM wrapper for the NAV manage database"""

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id$"

from django.db import models

class Message(models.Model):
    """From MetaNAV: The table contains the messages registered in the messages
    tool. Each message has a timeframe for when it is published on the NAV main
    page."""

    id = models.AutoField(db_column='messageid', primary_key=True)
    title = models.CharField(max_length=-1)
    description = models.TextField()
    tech_description = models.TextField()
    publish_start = models.DateTimeField()
    publish_end = models.DateTimeField()
    author = models.CharField(max_length=-1)
    last_changed = models.DateTimeField()
    replaces_message = models.ForeignKey('self', db_column='replaces_message',
        related_name='replaced_by', null=True)

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
    author = models.CharField(max_length=-1)
    state = models.CharField(max_length=-1)

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
    key = models.CharField(max_length=-1)
    value = models.CharField(max_length=-1)

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

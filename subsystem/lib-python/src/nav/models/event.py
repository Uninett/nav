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

# FIXME:
#     * Make sure each model has one field with primary_key=True
#     * Add unique_togheter constraints
#     * Split the file into smaller ones
#
# Also note: You will have to insert the output of 'django-admin.py sqlcustom
# [appname]' into your database.

from django.db import models

from nav.models.manage import Device, Netbox

class Subsystem(models.Model):
    name = models.CharField(max_length=-1, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    class Meta:
        db_table = 'subsystem'

#######################################################################
### Event system

class EventQueue(models.Model):
    STATE_CHOICES = (
        ('x', 'stateless'),
        ('s', 'start'),
        ('e', 'end'),
    )
    id = models.IntegerField(db_column='eventqid', primary_key=True)
    source = models.ForeignKey('Subsystem', db_column='source',
        related_name='source_of_events')
    target = models.ForeignKey('Subsystem', db_column='target',
        related_name='target_of_events')
    device = models.ForeignKey('Device', db_column='deviceid')
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    subid = models.CharField(max_length=-1)
    time = models.DateTimeField()
    event_type = models.ForeignKey('EventType', db_column='eventtypeid')
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='x')
    value = models.IntegerField(default=100)
    severity = models.IntegerField(default=50)
    class Meta:
        db_table = 'eventq'

class EventType(models.Model):
    STATEFUL_CHOICES = (
        ('y', 'stateful'),
        ('n', 'stateless'),
    )
    id = models.CharField(db_column='eventtypeid',
        max_length=32, primary_key=True)
    description = models.CharField(db_column='eventtypedesc', max_length=-1)
    stateful = models.CharField(max_length=1, choices=STATEFUL_CHOICES)
    class Meta:
        db_table = 'eventtype'

class EventQueueVar(models.Model):
    event_queue = models.ForeignKey('EventQueue', db_column='eventqid',
        related_name='variables')
    variable = models.CharField(db_column='var', max_length=-1)
    value = models.TextField(db_column='val')
    class Meta:
        db_table = 'eventqvar'

#######################################################################
### Alert system

class AlertQueue(models.Model):
    id = models.IntegerField(db_column='alertqid', primary_key=True)
    source = models.ForeignKey('Subsystem', db_column='source')
    device = models.ForeignKey('Device', db_column='deviceid')
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    subid = models.CharField(max_length=-1)
    time = models.DateTimeField()
    event_type = models.ForeignKey('EventType', db_column='eventtypeid')
    alert_type = models.ForeignKey('AlertType', db_column='alerttypeid')
    state = models.CharField(max_length=1) # FIXME: Add choices
    value = models.IntegerField()
    severity = models.IntegerField()
    class Meta:
        db_table = 'alertq'

class AlertType(models.Model):
    id = models.IntegerField(db_column='alerttypeid', primary_key=True)
    event_type = models.ForeignKey('EventType', db_column='eventtypeid')
    name = models.CharField(db_column='alterttype', max_length=-1)
    description= models.CharField(db_column='alerttypedesc', max_length=-1)
    class Meta:
        db_table = 'alerttype'

class AlertQueueMessage(models.Model):
    alert_queue = models.ForeignKey('AlertQueue', db_column='alertqid',
        related_name='messages')
    type = models.CharField(db_column='msgtype', max_length=-1)
    language = models.CharField(max_length=-1)
    message = models.TextField(db_column='msg')
    class Meta:
        db_table = 'alertqmsg'

class AlertQueueVariable(models.Model):
    alert_queue = models.ForeignKey('AlertQueue', db_column='alertqid',
        related_name='variables')
    variable = models.CharField(db_column='var', max_length=-1)
    value = models.TextField(db_column='val')
    class Meta:
        db_table = 'alertqvar'

class AlertHistory(models.Model):
    id = models.IntegerField(db_column='alerthistid', primary_key=True)
    source = models.ForeignKey('Subsystem', db_column='source')
    device = models.ForeignKey('Device', db_column='deviceid')
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    subid = models.CharField(max_length=-1)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event_type = models.ForeignKey('EventType', db_column='eventtypeid')
    alert_type = models.ForeignKey('AlertType', db_column='alerttypeid')
    value = models.IntegerField()
    severity = models.IntegerField()
    class Meta:
        db_table = 'alerthist'

class AlertHistoryMessage(models.Model):
    alert_history = models.ForeignKey('AlertHistory', db_column='alerthistid',
        related_name='messages')
    state = models.CharField(max_length=1) # FIXME: Add choices
    type = models.CharField(db_column='msgtype', max_length=-1)
    language = models.CharField(max_length=-1)
    message = models.TextField(db_column='msg')
    class Meta:
        db_table = 'alerthistmsg'

class AlertHistoryVariable(models.Model):
    alert_history = models.ForeignKey('AlertHistory', db_column='alerthistid')
    state = models.CharField(max_length=1) # FIXME: Add choices
    variable = models.CharField(db_column='var', max_length=-1)
    value = models.TextField(db_column='val')
    class Meta:
        db_table = 'alerthistvar'
        unique_together = (('alert_history', 'state', 'variable'),)

class AlertEngine(models.Model):
    last_alert_queue_id = models.IntegerField(db_column='lastalertqueueid')
    class Meta:
        db_table = 'alertengine'

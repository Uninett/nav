# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 UNINETT AS
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

# Don't warn about Meta classes, we can't help the Django API
# pylint: disable=R0903

import datetime as dt

from django.db import models

from nav.models.manage import Device, Netbox
from nav.models.fields import VarcharField

# Choices used in multiple models, "imported" into the models which use them
STATE_STATELESS = 'x'
STATE_START = 's'
STATE_END = 'e'
STATE_CHOICES = (
    (STATE_STATELESS, 'stateless'),
    (STATE_START, 'start'),
    (STATE_END, 'end'),
)

class Subsystem(models.Model):
    """From NAV Wiki: Defines the subsystems that post or receives an event."""

    name = VarcharField(primary_key=True)
    description = VarcharField(db_column='descr')

    class Meta:
        db_table = 'subsystem'

    def __unicode__(self):
        return self.name

#######################################################################
### Event system

class EventQueue(models.Model):
    """From NAV Wiki: The event queue. Additional data in eventqvar. Different
    subsystem (specified in source) post events on the event queue. Normally
    event engine is the target and will take the event off the event queue and
    process it.  getDeviceData are in some cases the target."""

    STATE_STATELESS = STATE_STATELESS
    STATE_START = STATE_START
    STATE_END = STATE_END
    STATE_CHOICES = STATE_CHOICES

    id = models.AutoField(db_column='eventqid', primary_key=True)
    source = models.ForeignKey('Subsystem', db_column='source',
        related_name='source_of_events')
    target = models.ForeignKey('Subsystem', db_column='target',
        related_name='target_of_events')
    device = models.ForeignKey(Device, db_column='deviceid', null=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid', null=True)
    subid = VarcharField()
    time = models.DateTimeField(default=dt.datetime.now)
    event_type = models.ForeignKey('EventType', db_column='eventtypeid')
    state = models.CharField(max_length=1, choices=STATE_CHOICES,
        default=STATE_STATELESS)
    value = models.IntegerField(default=100)
    severity = models.IntegerField(default=50)

    class Meta:
        db_table = 'eventq'

    def __unicode__(self):
        return u'Source %s, target %s, state %s' % (
            self.source, self.target, self.get_state_display())

    def getvardict(self):
        "Returns the variables attached to this event as a dict"
        return dict((var.variable, var.value)
                    for var in self.variables.all())

    def setvars(self, **vardict):
        "Sets the variables attached to this event"
        return self.setvardict(vardict)

    def setvardict(self, vardict):
        "Sets the variables attached to this event"
        if vardict:
            removed = self.variables.exclude(variable__in=vardict.keys())
            removed.delete()
        varmap = dict((v.variable, v) for v in self.variables.all())
        for key, value in vardict.items():
            if key in varmap:
                if varmap[key].value != value:
                    varmap[key] = value
                    varmap[key].save()
            else:
                var = EventQueueVar(event_queue=self,
                                    variable=key, value=value)
                var.save()



class EventType(models.Model):
    """From NAV Wiki: Defines event types."""

    STATEFUL_TRUE = 'y'
    STATEFUL_FALSE = 'n'
    STATEFUL_CHOICES = (
        (STATEFUL_TRUE, 'stateful'),
        (STATEFUL_FALSE, 'stateless'),
    )

    id = models.CharField(db_column='eventtypeid',
        max_length=32, primary_key=True)
    description = VarcharField(db_column='eventtypedesc')
    stateful = models.CharField(max_length=1, choices=STATEFUL_CHOICES)

    class Meta:
        db_table = 'eventtype'

    def __unicode__(self):
        return self.id

class EventQueueVar(models.Model):
    """From NAV Wiki: Defines additional (key,value) tuples that follow
    events."""

    event_queue = models.ForeignKey('EventQueue', db_column='eventqid',
        related_name='variables')
    variable = VarcharField(db_column='var')
    value = models.TextField(db_column='val')

    class Meta:
        db_table = 'eventqvar'
        unique_together = (('event_queue', 'variable'),)

    def __unicode__(self):
        return u'%s=%s' % (self.variable, self.value)

#######################################################################
### Alert system

class AlertQueue(models.Model):
    """From NAV Wiki: The alert queue. Additional data in alertqvar and
    alertmsg. Event engine posts alerts on the alert queue (and in addition on
    the alerthist table). Alert engine will process the data on the alert queue
    and send alerts to users based on their alert profiles. When all signed up
    users have received the alert, alert engine will delete the alert from
    alertq (but not from alert history)."""

    STATE_STATELESS = STATE_STATELESS
    STATE_START = STATE_START
    STATE_END = STATE_END
    STATE_CHOICES = STATE_CHOICES

    id = models.IntegerField(db_column='alertqid', primary_key=True)
    source = models.ForeignKey('Subsystem', db_column='source')
    device = models.ForeignKey(Device, db_column='deviceid', null=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid', null=True)
    subid = VarcharField()
    time = models.DateTimeField()
    event_type = models.ForeignKey('EventType', db_column='eventtypeid')
    alert_type = models.ForeignKey('AlertType', db_column='alerttypeid',
        null=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES,
        default=STATE_STATELESS)
    value = models.IntegerField()
    severity = models.IntegerField()

    history = models.ForeignKey('AlertHistory', null=True, blank=True,
                                db_column='alerthistid')

    class Meta:
        db_table = 'alertq'

    def __unicode__(self):
        return u'Source %s, state %s, severity %d' % (
            self.source, self.get_state_display(), self.severity)

class AlertType(models.Model):
    """From NAV Wiki: Defines the alert types. An event type may have many alert
    types."""

    id = models.AutoField(db_column='alerttypeid', primary_key=True)
    event_type = models.ForeignKey('EventType', db_column='eventtypeid')
    name = VarcharField(db_column='alerttype')
    description = VarcharField(db_column='alerttypedesc')

    class Meta:
        db_table = 'alerttype'
        unique_together = (('event_type', 'name'),)

    def __unicode__(self):
        return u'%s, of event type %s' % (self.name, self.event_type)

class AlertQueueMessage(models.Model):
    """From NAV Wiki: Event engine will, based on alertmsg.conf, preformat the
    alarm messages, one message for each configured alert channel (email, sms),
    one message for each configured language. The data are stored in the
    alertmsg table."""

    id = models.AutoField(primary_key=True)
    alert_queue = models.ForeignKey('AlertQueue', db_column='alertqid',
        related_name='messages')
    type = VarcharField(db_column='msgtype')
    language = VarcharField()
    message = models.TextField(db_column='msg')

    class Meta:
        db_table = 'alertqmsg'
        unique_together = (('alert_queue', 'type', 'language'),)

    def __unicode__(self):
        return u'%s message in language %s' % (self.type, self.language)

class AlertQueueVariable(models.Model):
    """From NAV Wiki: Defines additional (key,value) tuples that follow alert.
    Note: the eventqvar tuples are passed along to the alertqvar table so that
    the variables may be used in alert profiles."""

    id = models.AutoField(primary_key=True)
    alert_queue = models.ForeignKey('AlertQueue', db_column='alertqid',
        related_name='variables')
    variable = VarcharField(db_column='var')
    value = models.TextField(db_column='val')

    class Meta:
        db_table = 'alertqvar'
        unique_together = (('alert_queue', 'variable'),)

    def __unicode__(self):
        return u'%s=%s' % (self.variable, self.value)

class AlertHistory(models.Model):
    """From NAV Wiki: The alert history. Simular to the alert queue with one
    important distinction; alert history stores stateful events as one row,
    with the start and end time of the event."""

    id = models.AutoField(db_column='alerthistid', primary_key=True)
    source = models.ForeignKey('Subsystem', db_column='source')
    device = models.ForeignKey(Device, db_column='deviceid', null=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid', null=True)
    subid = VarcharField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    event_type = models.ForeignKey('EventType', db_column='eventtypeid')
    alert_type = models.ForeignKey('AlertType', db_column='alerttypeid',
        null=True)
    value = models.IntegerField()
    severity = models.IntegerField()

    class Meta:
        db_table = 'alerthist'

    def __unicode__(self):
        return u'Source %s, severity %d' % (self.source, self.severity)

    def is_stateful(self):
        """Returns true if the alert is stateful."""

        if self.end_time is None:
            return False
        else:
            return True

    def is_open(self):
        """Returns true if stateful and open."""

        if self.is_stateful() and self.end_time == dt.datetime.max:
            return True
        else:
            return False

    def get_downtime(self):
        """Returns the difference between start_time and end_time, the current
        downtime if the alert is still open, and None if the alert is
        stateless."""

        if self.is_stateful():
            if self.is_open():
                # Open alert
                return (dt.datetime.now() - self.start_time)
            else:
                # Closed alert
                return (self.end_time - self.start_time)
        else:
            # Stateless alert
            return None

class AlertHistoryMessage(models.Model):
    """From NAV Wiki: To have a history of the formatted messages too, they are
    stored in alerthistmsg."""

    STATE_STATELESS = STATE_STATELESS
    STATE_START = STATE_START
    STATE_END = STATE_END
    STATE_CHOICES = STATE_CHOICES

    id = models.AutoField(primary_key=True)
    alert_history = models.ForeignKey('AlertHistory', db_column='alerthistid',
        related_name='messages')
    state = models.CharField(max_length=1, choices=STATE_CHOICES,
        default=STATE_STATELESS)
    type = VarcharField(db_column='msgtype')
    language = VarcharField()
    message = models.TextField(db_column='msg')

    class Meta:
        db_table = 'alerthistmsg'
        unique_together = (('alert_history', 'state', 'type', 'language'),)

    def __unicode__(self):
        return u'%s message in language %s' % (self.type, self.language)

class AlertHistoryVariable(models.Model):
    """From NAV Wiki: Defines additional (key,value) tuples that follow the
    alerthist record."""

    STATE_STATELESS = STATE_STATELESS
    STATE_START = STATE_START
    STATE_END = STATE_END
    STATE_CHOICES = STATE_CHOICES

    id = models.AutoField(primary_key=True)
    alert_history = models.ForeignKey('AlertHistory', db_column='alerthistid')
    state = models.CharField(max_length=1, choices=STATE_CHOICES,
        default=STATE_STATELESS)
    variable = VarcharField(db_column='var')
    value = models.TextField(db_column='val')

    class Meta:
        db_table = 'alerthistvar'
        unique_together = (('alert_history', 'state', 'variable'),)

    def __unicode__(self):
        return u'%s=%s' % (self.variable, self.value)

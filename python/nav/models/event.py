# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2015 Uninett AS
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

from collections import defaultdict
import logging
import datetime as dt

from django.db import models, transaction
from django.db.models import Q
from django.core.validators import MaxValueValidator, MinValueValidator

from nav.models.fields import VarcharField, DateTimeInfinityField, UNRESOLVED

_logger = logging.getLogger(__name__)

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

    class Meta(object):
        db_table = 'subsystem'

    def __str__(self):
        return self.name


#######################################################################
### Event system


class VariableMapBase(object):
    """Descriptor for simplified dict-like access to the variable map tables
    associated with EventQueue and AlertQueue.

    NOTE: Updating the dictionary will not save it, the attribute must be
    assigned a dict value for a db update to take place.

    """

    def __init__(self):
        self.cachename = "_cached_variables"

    def __get__(self, obj, obj_type=None):
        if obj is None:
            return self

        if hasattr(obj, self.cachename):
            return getattr(obj, self.cachename)
        elif obj.pk:
            varmap = self._as_dict(obj)
            setattr(obj, self.cachename, varmap)
            return varmap
        else:
            return {}

    def __set__(self, obj, vardict):
        if obj is None:
            raise AttributeError("can only be set on instances")

        if not hasattr(vardict, 'items'):
            raise ValueError("value must be a dict")

        if obj.pk:
            variables = obj.variables
            if vardict:
                self._delete_missing_variables(vardict, variables)

            self._update_variables(obj, vardict)

        setattr(obj, self.cachename, vardict)

    def _as_dict(self, obj):
        raise NotImplementedError

    def _delete_missing_variables(self, vardict, variables):
        raise NotImplementedError

    def _update_variables(self, obj, vardict):
        raise NotImplementedError


class VariableMap(VariableMapBase):
    def _as_dict(self, obj):
        variables = obj.variables
        return {var.variable: var.value for var in variables.all()}

    def _delete_missing_variables(self, vardict, variables):
        removed = variables.exclude(variable__in=vardict.keys())
        removed.delete()

    def _update_variables(self, obj, vardict):
        varmap = {var.variable: var for var in obj.variables.all()}

        for key, value in vardict.items():
            if key in varmap:
                if varmap[key].value != value:
                    varmap[key].value = value
                    varmap[key].save()
            else:
                obj.variables.create(
                    variable=key,
                    value=value,
                )


class StateVariableMap(VariableMapBase):
    """Descriptor for simplified dict-like access to the AlertHistory
    stateful variable map.

    NOTE: Updating the dictionary will not save it, the attribute must be
    assigned a dict value for a db update to take place.

    """

    def _as_dict(self, obj):
        variables = obj.variables
        varmap = defaultdict(dict)
        for var in variables.all():
            varmap[var.state][var.variable] = var.value
        return dict(varmap)

    def _delete_missing_variables(self, vardict, variables):
        for state, _descr in STATE_CHOICES:
            removed = variables.filter(state=state)
            if state in vardict:
                removed.exclude(variable__in=vardict[state].keys())
            removed.delete()

    def _update_variables(self, obj, vardict):
        varmap = self._as_dict(obj)

        for state, vars in vardict.items():
            for key, value in vars.items():
                if state in varmap and key in varmap[state]:
                    if varmap[state][key].value != value:
                        varmap[state][key] = value
                        varmap[state][key].save()
                else:
                    obj.variables.create(
                        state=state,
                        variable=key,
                        value=value,
                    )


class UnknownEventSubject(object):
    """Representation of unknown alert/event subjects"""

    def __init__(self, alert):
        self._alert = alert
        self.netbox = alert.netbox
        self.subid = alert.subid

    def get_absolute_url(self):
        """Returns a fall-back canonical URL to the netbox, if attached"""
        if self.netbox:
            return self.netbox.get_absolute_url()

    def __str__(self):
        descr = self._get_description_from_message()
        if descr:
            return descr
        else:
            fmt = "{0} ({1})"
            return fmt.format(self.netbox or "N/A", self.subid)

    def _get_description_from_message(self):
        if not hasattr(self._alert, 'messages'):
            return

        m = self._alert.messages.filter(type='sms', language='en')
        if m:
            return m[0].message


class EventMixIn(object):
    """MixIn for methods common to multiple event/alert/alerthistory models"""

    def get_key(self):
        """Returns an identifying key for this event.

        The key is a tuple of identity attribute values and can be used as a
        dictionary key to keep track of events that reference the same
        problem.

        """
        id_keys = ('netbox_id', 'subid', 'event_type_id')
        values = (getattr(self, key) for key in id_keys)
        return tuple(values)

    # This dict encodes knowledge of what the subid attribute represents in
    # various event types, in lieu of a more generic mechanism
    SUBID_MAP = {
        'linkState': 'Interface',
        'aggregateLinkState': 'Interface',
        'moduleState': 'Module',
        'serviceState': 'Service',
        'psuState': 'PowerSupplyOrFan',
        'fanState': 'PowerSupplyOrFan',
        'chassisState': 'NetboxEntity',
        'bgpState': 'GatewayPeerSession',
    }

    def get_subject(self):
        """
        Returns the subject of a given event/alert.

        Sometimes, the subject is just a Netbox objects. Other times, it may
        be some physical or logical subcomponents of a Netbox.

        """
        subject = getattr(self, "_cached_subject", None)
        subid = getattr(self, "_cached_subid", None)
        if not subid or subid != self.subid:
            subject = self._fetch_subject()
            subid = self.subid
            setattr(self, "_cached_subject", subject)
            setattr(self, "_cached_subid", subid)

        return subject

    def _fetch_subject(self):
        if self.subid:
            from django.apps import apps

            subid = self.subid
            if self.event_type_id in self.SUBID_MAP:
                model = apps.get_model('nav_models', self.SUBID_MAP[self.event_type_id])
            elif (
                self.event_type_id == 'maintenanceState'
                and 'service' in self.varmap.get(EventQueue.STATE_START, {})
            ):
                model = apps.get_model('nav_models', 'Service')
            elif self.event_type_id == 'thresholdState':
                return ThresholdEvent(self)
            else:
                return UnknownEventSubject(self)

            if model:
                try:
                    return model.objects.get(pk=subid)
                except model.DoesNotExist:
                    _logger.warning(
                        "alert subid %s points to non-existant %s",
                        subid,
                        model,
                    )
                    return UnknownEventSubject(self)

        # catch-all
        return self.netbox or self.device or UnknownEventSubject(self)


class ThresholdEvent(object):
    """
    Magic class to act as a threshold event subject that produces useful
    descriptions and relations to the event.
    """

    def __init__(self, event):
        from django.apps import apps

        self.event = event
        try:
            ruleid, self.metric = event.subid.split(':', 1)
        except ValueError:
            ruleid = event.subid
            self.metric = None

        klass = apps.get_model('nav_models', 'ThresholdRule')
        try:
            self.rule = klass.objects.get(pk=ruleid)
        except (klass.DoesNotExist, ValueError):
            self.rule = None

        if self.metric:
            from nav.metrics.lookup import lookup

            self.subject = lookup(self.metric)
        else:
            self.subject = None

    def __str__(self):
        subject = self.subject or self.metric
        if self.rule:
            descr = self.rule.description or self.rule.alert
        else:
            descr = 'Unknown rule'

        if subject:
            return "{} ({})".format(subject, descr)
        else:
            return "{} ({})".format(descr, subject)

    def get_absolute_url(self):
        """Returns a URL to the metric subject, if one was found"""
        if self.subject:
            if hasattr(self.subject, 'get_absolute_url'):
                return self.subject.get_absolute_url()
            elif hasattr(self.subject, 'netbox') and hasattr(
                self.subject.netbox, 'get_absolute_url'
            ):
                return self.subject.netbox.get_absolute_url()


class EventQueue(models.Model, EventMixIn):
    """From NAV Wiki: The event queue. Additional data in eventqvar. Different
    subsystem (specified in source) post events on the event queue. Normally
    event engine is the target and will take the event off the event queue and
    process it.  getDeviceData are in some cases the target."""

    STATE_STATELESS = STATE_STATELESS
    STATE_START = STATE_START
    STATE_END = STATE_END
    STATE_CHOICES = STATE_CHOICES

    id = models.AutoField(db_column='eventqid', primary_key=True)
    source = models.ForeignKey(
        'Subsystem',
        on_delete=models.CASCADE,
        db_column='source',
        related_name='source_of_events',
    )
    target = models.ForeignKey(
        'Subsystem',
        on_delete=models.CASCADE,
        db_column='target',
        related_name='target_of_events',
    )
    device = models.ForeignKey(
        'nav_models.Device',
        on_delete=models.CASCADE,
        db_column='deviceid',
        null=True,
        related_name="events",
    )
    netbox = models.ForeignKey(
        'nav_models.Netbox',
        on_delete=models.CASCADE,
        db_column='netboxid',
        null=True,
        related_name="events",
    )
    subid = VarcharField(default='')
    time = models.DateTimeField(default=dt.datetime.now)
    event_type = models.ForeignKey(
        'EventType',
        on_delete=models.CASCADE,
        db_column='eventtypeid',
        related_name="events",
    )
    state = models.CharField(
        max_length=1, choices=STATE_CHOICES, default=STATE_STATELESS
    )
    value = models.IntegerField(default=100)
    severity = models.IntegerField(
        default=3,
        validators=[MaxValueValidator(5), MinValueValidator(1)],
    )

    varmap = VariableMap()

    class Meta(object):
        db_table = 'eventq'

    def __repr__(self):
        return "<EventQueue: %s>" % ", ".join(
            "%s=%r" % (attr, getattr(self, attr))
            for attr in (
                'id',
                'event_type_id',
                'source_id',
                'target_id',
                'netbox',
                'subid',
                'state',
                'time',
            )
        )

    def __str__(self):
        string = (
            "{self.event_type} {state} event for {self.netbox} "
            "(subid={self.subid}) from {self.source} to {self.target} "
            "at {self.time}"
        )
        return string.format(self=self, state=dict(self.STATE_CHOICES)[self.state])

    @transaction.atomic
    def save(self, *args, **kwargs):
        new_object = self.pk is None
        super(EventQueue, self).save(*args, **kwargs)
        if new_object:
            assert self.pk
            self.varmap = self.varmap


class EventType(models.Model):
    """From NAV Wiki: Defines event types."""

    STATEFUL_TRUE = 'y'
    STATEFUL_FALSE = 'n'
    STATEFUL_CHOICES = (
        (STATEFUL_TRUE, 'stateful'),
        (STATEFUL_FALSE, 'stateless'),
    )

    id = models.CharField(db_column='eventtypeid', max_length=32, primary_key=True)
    description = VarcharField(db_column='eventtypedesc')
    stateful = models.CharField(max_length=1, choices=STATEFUL_CHOICES)

    class Meta(object):
        db_table = 'eventtype'

    def __str__(self):
        return self.id


class EventQueueVar(models.Model):
    """From NAV Wiki: Defines additional (key,value) tuples that follow
    events."""

    event_queue = models.ForeignKey(
        'EventQueue',
        on_delete=models.CASCADE,
        db_column='eventqid',
        related_name='variables',
    )
    variable = VarcharField(db_column='var')
    value = models.TextField(db_column='val')

    class Meta(object):
        db_table = 'eventqvar'
        unique_together = (('event_queue', 'variable'),)

    def __str__(self):
        return '%s=%s' % (self.variable, self.value)


#######################################################################
### Alert system


class AlertQueue(models.Model, EventMixIn):
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

    id = models.AutoField(db_column='alertqid', primary_key=True)
    source = models.ForeignKey(
        'Subsystem',
        on_delete=models.CASCADE,
        db_column='source',
        related_name="alerts",
    )
    device = models.ForeignKey(
        'nav_models.Device',
        on_delete=models.CASCADE,
        db_column='deviceid',
        null=True,
        related_name="alerts",
    )
    netbox = models.ForeignKey(
        'nav_models.Netbox',
        on_delete=models.CASCADE,
        db_column='netboxid',
        null=True,
        related_name="alerts",
    )
    subid = VarcharField(default='')
    time = models.DateTimeField()
    event_type = models.ForeignKey(
        'EventType',
        on_delete=models.CASCADE,
        db_column='eventtypeid',
        related_name="alerts",
    )
    alert_type = models.ForeignKey(
        'AlertType',
        on_delete=models.CASCADE,
        db_column='alerttypeid',
        null=True,
        related_name="alerts",
    )
    state = models.CharField(
        max_length=1, choices=STATE_CHOICES, default=STATE_STATELESS
    )
    value = models.IntegerField()
    severity = models.IntegerField(
        default=3,
        validators=[MaxValueValidator(5), MinValueValidator(1)],
    )

    history = models.ForeignKey(
        'AlertHistory',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='alerthistid',
        related_name="alerts",
    )

    varmap = VariableMap()

    class Meta(object):
        db_table = 'alertq'

    def __str__(self):
        return 'Source %s, state %s, severity %d' % (
            self.source,
            self.get_state_display(),
            self.severity,
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        new_object = self.pk is None
        super(AlertQueue, self).save(*args, **kwargs)
        if new_object:
            assert self.pk
            self.varmap = self.varmap


class AlertType(models.Model):
    """From NAV Wiki: Defines the alert types. An event type may have many alert
    types."""

    id = models.AutoField(db_column='alerttypeid', primary_key=True)
    event_type = models.ForeignKey(
        'EventType',
        on_delete=models.CASCADE,
        db_column='eventtypeid',
        related_name="alert_types",
    )
    name = VarcharField(db_column='alerttype')
    description = VarcharField(db_column='alerttypedesc')

    class Meta(object):
        db_table = 'alerttype'
        unique_together = (('event_type', 'name'),)

    def __str__(self):
        return '%s, of event type %s' % (self.name, self.event_type)


class AlertQueueMessage(models.Model):
    """From NAV Wiki: Event engine will, based on alertmsg.conf, preformat the
    alarm messages, one message for each configured alert channel (email, sms),
    one message for each configured language. The data are stored in the
    alertmsg table."""

    id = models.AutoField(primary_key=True)
    alert_queue = models.ForeignKey(
        'AlertQueue',
        on_delete=models.CASCADE,
        db_column='alertqid',
        related_name='messages',
    )
    type = VarcharField(db_column='msgtype')
    language = VarcharField()
    message = models.TextField(db_column='msg')

    class Meta(object):
        db_table = 'alertqmsg'
        unique_together = (('alert_queue', 'type', 'language'),)

    def __str__(self):
        return '%s message in language %s' % (self.type, self.language)


class AlertQueueVariable(models.Model):
    """From NAV Wiki: Defines additional (key,value) tuples that follow alert.
    Note: the eventqvar tuples are passed along to the alertqvar table so that
    the variables may be used in alert profiles."""

    id = models.AutoField(primary_key=True)
    alert_queue = models.ForeignKey(
        'AlertQueue',
        on_delete=models.CASCADE,
        db_column='alertqid',
        related_name='variables',
    )
    variable = VarcharField(db_column='var')
    value = models.TextField(db_column='val')

    class Meta(object):
        db_table = 'alertqvar'
        unique_together = (('alert_queue', 'variable'),)

    def __str__(self):
        return '%s=%s' % (self.variable, self.value)


class AlertHistoryQuerySet(models.QuerySet):
    """Custom QuerySet for the AlertHistory model"""

    def unresolved(self, event_type_id=None):
        """
        Gets only unresolved entries.

        :param event_type_id: An optional event type id string to filter on
        :rtype: django.db.models.query.QuerySet
        """
        if event_type_id:
            filtr = UNRESOLVED & Q(event_type__id=event_type_id)
        else:
            filtr = UNRESOLVED
        return self.filter(filtr)


class AlertHistory(models.Model, EventMixIn):
    """From NAV Wiki: The alert history. Simular to the alert queue with one
    important distinction; alert history stores stateful events as one row,
    with the start and end time of the event."""

    objects = AlertHistoryQuerySet.as_manager()

    id = models.AutoField(db_column='alerthistid', primary_key=True)
    source = models.ForeignKey(
        'Subsystem',
        on_delete=models.CASCADE,
        db_column='source',
        related_name="alert_history_set",
    )
    device = models.ForeignKey(
        'nav_models.Device',
        on_delete=models.CASCADE,
        db_column='deviceid',
        null=True,
        related_name="alert_history_set",
    )
    netbox = models.ForeignKey(
        'nav_models.Netbox',
        on_delete=models.CASCADE,
        db_column='netboxid',
        null=True,
        related_name="alert_history_set",
    )
    subid = VarcharField(default='')
    start_time = models.DateTimeField()
    end_time = DateTimeInfinityField(null=True)
    event_type = models.ForeignKey(
        'EventType',
        on_delete=models.CASCADE,
        db_column='eventtypeid',
        related_name="alert_history_set",
    )
    alert_type = models.ForeignKey(
        'AlertType',
        on_delete=models.CASCADE,
        db_column='alerttypeid',
        null=True,
        related_name="alert_history_set",
    )
    value = models.IntegerField()
    severity = models.IntegerField(
        default=3,
        validators=[MaxValueValidator(5), MinValueValidator(1)],
    )

    varmap = StateVariableMap()

    class Meta(object):
        db_table = 'alerthist'

    def __str__(self):
        return 'Id %s Source %s, severity %d' % (self.id, self.source, self.severity)

    def is_stateful(self):
        """Returns true if the alert is stateful."""

        return self.end_time is not None

    def is_open(self):
        """Returns true if stateful and open."""

        return self.is_stateful() and self.end_time == dt.datetime.max

    def get_downtime(self):
        """Returns the difference between start_time and end_time, the current
        downtime if the alert is still open, and None if the alert is
        stateless."""

        if self.is_stateful():
            if self.is_open():
                # Open alert
                return dt.datetime.now() - self.start_time
            else:
                # Closed alert
                return self.end_time - self.start_time
        else:
            # Stateless alert
            return None

    def is_acknowledged(self):
        """
        Returns an Acknowledgement instance if this alert has been
        acknowledged, otherwise None.
        """
        try:
            return self.acknowledgement
        except Acknowledgement.DoesNotExist:
            return

    def acknowledge(self, account, comment):
        """
        Acknowledges this alert using a given account and comment.

        Any pre-existing acknowledgement will be overwritten.
        """
        try:
            ack = self.acknowledgement
        except Acknowledgement.DoesNotExist:
            ack = Acknowledgement(alert=self, account=account, comment=comment)
        else:
            ack.account = account
            ack.comment = comment
            ack.date = dt.datetime.now()

        ack.save()

    @transaction.atomic
    def save(self, *args, **kwargs):
        new_object = self.pk is None
        super(AlertHistory, self).save(*args, **kwargs)
        if new_object:
            assert self.pk
            self.varmap = self.varmap


class AlertHistoryMessage(models.Model):
    """From NAV Wiki: To have a history of the formatted messages too, they are
    stored in alerthistmsg."""

    STATE_STATELESS = STATE_STATELESS
    STATE_START = STATE_START
    STATE_END = STATE_END
    STATE_CHOICES = STATE_CHOICES

    id = models.AutoField(primary_key=True)
    alert_history = models.ForeignKey(
        'AlertHistory',
        on_delete=models.CASCADE,
        db_column='alerthistid',
        related_name='messages',
    )
    state = models.CharField(
        max_length=1, choices=STATE_CHOICES, default=STATE_STATELESS
    )
    type = VarcharField(db_column='msgtype')
    language = VarcharField()
    message = models.TextField(db_column='msg')

    class Meta(object):
        db_table = 'alerthistmsg'
        unique_together = (('alert_history', 'state', 'type', 'language'),)

    def __str__(self):
        return '%s message in language %s' % (self.type, self.language)


class AlertHistoryVariable(models.Model):
    """From NAV Wiki: Defines additional (key,value) tuples that follow the
    alerthist record."""

    STATE_STATELESS = STATE_STATELESS
    STATE_START = STATE_START
    STATE_END = STATE_END
    STATE_CHOICES = STATE_CHOICES

    id = models.AutoField(primary_key=True)
    alert_history = models.ForeignKey(
        'AlertHistory',
        on_delete=models.CASCADE,
        db_column='alerthistid',
        related_name='variables',
    )
    state = models.CharField(
        max_length=1, choices=STATE_CHOICES, default=STATE_STATELESS
    )
    variable = VarcharField(db_column='var')
    value = models.TextField(db_column='val')

    class Meta(object):
        db_table = 'alerthistvar'
        unique_together = (('alert_history', 'state', 'variable'),)

    def __str__(self):
        return '%s=%s' % (self.variable, self.value)


class Acknowledgement(models.Model):
    """Alert acknowledgements"""

    alert = models.OneToOneField(
        'AlertHistory',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        primary_key=True,
        related_name="acknowledgement",
    )
    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="acknowledgements",
    )
    comment = VarcharField(blank=True)
    date = models.DateTimeField(null=False, default=dt.datetime.now)

    class Meta(object):
        db_table = 'alerthist_ack'

    def __str__(self):
        return "%r acknowledged by %s at %s" % (self.alert, self.account, self.date)

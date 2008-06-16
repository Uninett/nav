# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 UNINETT AS
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
# Authors: Thomas Adamcik <thomas.adamcik@uninett.no>
#

"""Django ORM wrapper for profiles in NAV"""

__copyright__ = "Copyright 2007-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no"
__id__ = "$Id$"

from datetime import datetime

from django.db import models
from django.db.models import Q

from nav.models.event import AlertQueue

_ = lambda a: a

#######################################################################
### Account models

class Account(models.Model):
    login = models.CharField(max_length=-1, unique=True)
    name = models.CharField(max_length=-1)
    password = models.CharField(max_length=-1)
    ext_sync = models.CharField(max_length=-1)

    class Meta:
        db_table = u'account'

    def __unicode__(self):
        return self.login

    def get_active_profile(self):
        return self.alertpreference.active_profile

class AccountGroup(models.Model):
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1, db_column='descr')
    accounts = models.ManyToManyField('Account') # FIXME this uses a view hack, was AccountInGroup

    class Meta:
        db_table = u'accountgroup'

    def __unicode__(self):
        return self.name

class AccountProperty(models.Model):
    account = models.ForeignKey('Account', db_column='accountid')
    property = models.CharField(max_length=-1)
    value = models.CharField(max_length=-1)

    class Meta:
        db_table = u'accountproperty'

    def __unicode__(self):
        return '%s=%s' % (self.property, self.value)

class AccountOrganization(models.Model):
    account = models.ForeignKey('Account', db_column='accountid')
    organization = models.CharField(max_length=30)

    class Meta:
        db_table = u'accountorg'

    def __unicode__(self):
        return self.orgid

class AlertAddress(models.Model):
    SMS = 2
    EMAIL = 1

    ALARM_TYPE = (
        (EMAIL, _('email')),
        (SMS, _('SMS')),
    )

    account = models.ForeignKey('Account', db_column='accountid')
    type = models.IntegerField(choices=ALARM_TYPE)
    address = models.CharField(max_length=-1, db_column='adresse')

    class Meta:
        db_table = u'alarmadresse'

    def __unicode__(self):
        return '%s by %s' % (self.address, self.get_type_display())

class AlertPreference(models.Model):
    account = models.OneToOneField('Account', primary_key=True,  db_column='accountid')
    active_profile = models.OneToOneField('AlertProfile', db_column='activeprofile', null=True)
    last_sent_day = models.DateTimeField(db_column='lastsentday')
    last_sent_week = models.DateTimeField(db_column='lastsentweek')

    class Meta:
        db_table = u'preference'

    def __unicode__(self):
        return 'preferences for %s' % self.account


#######################################################################
### Profile models

class AlertProfile(models.Model):
    account = models.ForeignKey('Account', db_column='accountid')
    name = models.CharField(max_length=-1, db_column='navn')
    time = models.TimeField(db_column='tid')
    weekday = models.IntegerField(db_column='ukedag')
    weektime = models.TimeField(db_column='uketid')

    class Meta:
        db_table = u'brukerprofil'

    def get_active_timeperiod(self):
        now = datetime.now()

        # Limit our query to the correct type of time periods
        if now.isoweekday() in [6,7]:
            valid_during = [TimePeriod.ALL_WEEK,TimePeriod.WEEKENDS]
        else:
            valid_during = [TimePeriod.ALL_WEEK,TimePeriod.WEEKDAYS]

        # The following code should get the currently active timeperiod.
        # If we don't find a timeperiod we use tp which will we the last
        # possilbe timeperiod (which wraps around to covering the first part of
        # the day.
        activve_timeperiod = None
        for tp in self.timeperiod_set.filter(valid_during__in=valid_during).order_by('start'):
            if not activve_timeperiod or (tp.start <= now.time()):
                activve_timeperiod = tp

        return activve_timeperiod or tp

    def __unicode__(self):
        return self.name

class TimePeriod(models.Model):
    ALL_WEEK = 1
    WEEKDAYS = 2
    WEEKENDS = 3

    VALID_DURING_CHOICES = (
        (ALL_WEEK, _('all days')),
        (WEEKDAYS, _('weekdays')),
        (WEEKENDS, _('weekends')),
    )

    profile = models.ForeignKey('AlertProfile', db_column='brukerprofilid')
    start = models.TimeField(db_column='starttid')
    valid_during = models.IntegerField(db_column='helg', choices=VALID_DURING_CHOICES)

    class Meta:
        db_table = u'tidsperiode'

    def __unicode__(self):
        return u'from %s for %s profile on %s' % (self.start, self.profile, self.get_valid_during_display())

class AlertSubscription(models.Model): # FIXME this needs a better name
    NOW = 0
    DAILY = 1
    WEEKLY = 2
    MAX = 3
    # FIXME according to profiles 3="Queue [Until profile changes]" ie next
    # time peroid, engine thinks that 3="NOW()-q.time>=p.queuelength AS max" ie
    # queu until alert has been in queue a certain number of days
    SUBSCRIPTION_TYPES = (
        (NOW, _('send immediately')),
        (DAILY, _('send daily at predefined time')),
        (WEEKLY, _('send weekly at predefined time')),
        (MAX, _('send at end of timeperiod')),
    )

    alarm_address = models.ForeignKey('AlarmAddress', db_column='alarmadresseid')
    time_period = models.ForeignKey('TimePeriod', db_column='tidsperiodeid')
    equipment_group = models.ForeignKey('FilterGroup', db_column='utstyrgruppeid')
    type = models.IntegerField(db_column='vent', choices=SUBSCRIPTION_TYPES)

    class Meta:
        db_table = u'varsle'

    def __unicode__(self):
        return 'alerts received %s should be %s to %s' % (self.time_period, self.get_subscription_type_display(), self.alarm_address)

#######################################################################
### Equipment models

class FilterGroupContent(models.Model):
    #            inc   pos
    # Add      |  1  |  1  | union in set theory
    # Sub      |  0  |  1  | exclusion
    # And      |  0  |  0  | intersection in set theory
    # Add inv. |  1  |  0  | complement of set

    include = models.BooleanField(db_column='inkluder')   # Include alert if filter macthes?
    positive = models.BooleanField(db_column='positiv')   # Negate match?
    priority = models.IntegerField(db_column='prioritet')

    filter = models.ForeignKey('Filter', db_column='utstyrfilterid')
    filter_group = models.ForeignKey('FilterGroup', db_column='utstyrgruppeid')

    class Meta:
        db_table = u'gruppetilfilter'
        ordering = ['priority']

    def __unicode__(self):
        if self.include:
            type = 'inclusive'
        else:
            type = 'exclusive'

        if not self.positive:
            type = 'inverted %s'  % type

        return '%s filter on %s' % (type, self.filter)

class Operator(models.Model):
    EQUALS = 0
    GREATER = 1
    GREATER_EQ = 2
    LESS = 3
    LESS_EQ = 4
    NOT_EQUAL = 5
    STARTSWITH = 6
    ENDSWITH = 7
    CONTAINS = 8
    REGEXP = 9
    WILDCARD = 10
    IN = 11

    # FIXME implment all of these in alertengine or disable those that don't
    # get implemeted.
    OPERATOR_TYPES = (
        (EQUALS, _('equals')),
        (GREATER, _('is greater')),
        (GREATER_EQ, _('is greater or equal')),
        (LESS, _('is less')),
        (LESS_EQ, _('is less or equal')),
        (NOT_EQUAL, _('not equals')),
        (STARTSWITH, _('starts with')),
        (ENDSWITH, _('ends with')),
        (CONTAINS, _('contains')),
        (REGEXP, _('regexp')),
        (WILDCARD, _('wildcard (? og *)')),
        (IN, _('in')),
    )
    OPERATOR_MAPPING = {
        EQUALS: '__exact',
        GREATER: '__gt',
        GREATER_EQ: '__gte',
        LESS: '__lt',
        LESS_EQ: '__lte',
#        NOT_EQUAL: '', # FIXME
        STARTSWITH: '__startswith',
        ENDSWITH: '__endswith',
        CONTAINS: '__contains',
        REGEXP: '__regex',
#        WILDCARD: '', #FIXME
        IN: '__in',
    }
    type = models.IntegerField(db_column='operatorid', choices=OPERATOR_TYPES)
    match_field = models.ForeignKey('MatchField', db_column='matchfieldid')

    class Meta:
        db_table = u'operator'
        unique_together = (('operator', 'match_field'),)

    def __unicode__(self):
        return u'%s match on %s' % (self.get_operator_display(), self.match_field)

    def get_operator_mapping(self):
        return self.OPERATOR_MAPPING[self.type]


class Expresion(models.Model):
    equipment_filter = models.ForeignKey('Filter', db_column='utstyrfilterid')
    match_field = models.ForeignKey('MatchField', db_column='matchfelt')
    operator = models.ForeignKey('Operator' ,db_column='matchtype')
    value = models.CharField(max_length=-1, db_column='verdi')

    class Meta:
        db_table = u'filtermatch'

    def __unicode__(self):
        return '%s match on %s against %s' % (self.operator.get_type_display(), self.match_field, self.value)

class Filter(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('Account', db_column='accountid')
    name = models.CharField(max_length=-1, db_column='navn')

    class Meta:
        db_table = u'utstyrfilter'

    def __unicode__(self):
        return self.name

class FilterGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    owner = models.ForeignKey('Account', db_column='accountid', null=True)
    name = models.CharField(max_length=-1, db_column='navn')
    description = models.CharField(max_length=-1, db_column='descr')

    group_permisions = models.ManyToManyField('AccountGroup') # FIXME this uses view hack, was rettighet

    class Meta:
        db_table = u'utstyrgruppe'

    def __unicode__(self):
        return self.name

class MatchField(models.Model):
    # Attributes that define data type meanings:
    STRING = 0
    INTEGER = 1
    IP = 2

    DATA_TYPES = (
        (STRING, _('string')),
        (INTEGER, _('integer')),
        (IP, _('ip')),
    )

    ''' #TODO finish this
    FIELD_CHOICES = []
    from nav.models.event import AlertQueue, AlertType, EventType, Subsystem
    from nav.models.manage import Arp, Cam, Category, Device, GwPort, Location, Memory, Netbox, NetboxCategory, NetboxInfo, NetboxType, Organization, Prefix, Product, Room, Subcategory, SwPort, Usage, Vlan, Vendor

    for model in [
            # event models
                AlertQueue, AlertType, EventType, Subsystem,
            # manage models
                Arp, Cam, Category, Device, GwPort, Location, Memory, Netbox,
                NetboxCategory, NetboxInfo, NetboxType, Organization, Prefix,
                Product, Room, Subcategory, SwPort, Vendor, Vlan,
                Usage,
#                TypeGroup, Service,
            ]:
        model_choices = []
        for field in model._meta.fields:
            model_choices.append( (field.db_column or field.attname, field.attname))
        FIELD_CHOICES.append( (model._meta.db_table, model_choices) )
    '''

    # Attributes for the fields:

    # Unless the attribute name is prefixed with something we are refering to
    # the netbox connected to an alert.
    ALERT_TYPE = 'alerttype'
    ARP = 'arp'
    CAM = 'cam'
    CAT = 'cat'
    CATEGORY = 'category'
    DEVICE = 'device'
    EVENT_TYPE = 'eventtype'
    GWPORT = 'gwport'
    LOCATION = 'location'
    MEMORY = 'mem'
    MODULE = 'module'
    NETBOX = 'netbox'
    NETBOXINFO = 'netboxinfo'
    ORGANIZATION = 'org'
    PREFIX = 'prefix'
    PRODUCT = 'product'
    ROOM = 'room'
    SERVICE = 'service'
    SUBCATEGORY = 'subcat'
    SUBSYSTEM = 'subsystem'
    SWPORT = 'swport'
    TYPE = 'type'
    TYPEGROUP = 'typegroup'
    VENDOR = 'vendor'
    VLAN = 'vlan'
    USAGE = 'usage'


    LOOKUP_FIELDS = (
        (ALERT_TYPE, _('alert type')),
        (ARP, _('arp')),
        (CAM, _('cam')),
        (CAT, _('cat')),
        (CATEGORY, _('category')),
        (DEVICE, _('device')),
        (EVENT_TYPE, _('event type')),
        (GWPORT, _('GW-port')),
        (LOCATION, _('location')),
        (MEMORY, _('memeroy')),
        (MODULE, _('module')),
        (NETBOX, _('netbox')),
        (NETBOXINFO, _('netbox info')),
        (ORGANIZATION, _('organization')),
        (PREFIX, _('prefix')),
        (PRODUCT, _('product')),
        (ROOM, _('room')),
        (SERVICE, _('service')),
        (SUBCATEGORY, _('subcategory')),
        (SUBSYSTEM, _('subsystem')),
        (SWPORT, _('SW-port')),
        (TYPE, _('type')),
        (TYPEGROUP, _('typegroup')),
        (VENDOR, _('vendor')),
        (VLAN, _('vlan')),
        (USAGE, _('usage')),
    )

    # This mapping designates how a MatchField relates to an alert. (yes the
    # formating is not PEP8, but it wouldn't be very readable otherwise)
    #
    # <lookup>__<variable>__<operator>=<value> should do the trick here.
    LOOKUP_MAP = {
        ARP:          'netbox__arp',                              # "select a.* from arp a, netbox n where n.netboxid=$this->{alertq}->{netboxid} and a.netboxid=n.netboxid",
        CAM:          'netbox__cam',                              # "select c.* from cam c, netbox n where n.netboxid=$this->{alertq}->{netboxid} and c.netboxid=n.netboxid",
        CAT:          'netbox__category',#FIXME                   # "select c.* from cat c, netbox n where n.netboxid=$this->{alertq}->{netboxid} and n.catid=c.catid",
        DEVICE:       'netbox__device',                           # "select d.* from device d, netbox n where n.netboxid=$this->{alertq}->{netboxid} and d.deviceid=n.deviceid",
        EVENT_TYPE:   'event_type',                               # "select * from eventtype where eventtypeid='$this->{alertq}->{eventtypeid}'",
        GWPORT:       'netbox__connected_to_gwport',              # "select g.* from gwport g,module m, netbox n where n.netboxid=$this->{alertq}->{netboxid} and m.deviceid=n.deviceid and g.moduleid=m.moduleid",
        LOCATION:     'netbox__room__location',                   # "select l.* from location l, room r, netbox n where n.netboxid=$this->{alertq}->{netboxid} and r.roomid=n.roomid and r.locationid=l.locationid",
        MEMORY:       'netbox__memory',                           # "select m.* from mem m, netbox n where n.netboxid=$this->{alertq}->{netboxid} and m.netboxid=n.netboxid",
        MODULE:       'netbox__module',                           # "select m.* from module m, netbox n where n.netboxid=$this->{alertq}->{netboxid} and m.deviceid=n.deviceid",
        NETBOX:       'netbox',                                   # "select * from netbox where netboxid=$this->{alertq}->{netboxid}",
        CATEGORY:     'netbox__category', #FIXME                   # "select nc.* from netboxcategory nc, netbox n where n.netboxid=$this->{alertq}->{netboxid} and nc.netboxid=n.netboxid",
        NETBOXINFO:   'netbox__info',                             # "select ni.* from netboxinfo ni, netbox n where n.netboxid=$this->{alertq}->{netboxid} and ni.netboxid=n.netboxid",
        ORGANIZATION: 'netbox__organization',                     # "select o.* from org o, netbox n where n.netboxid=$this->{alertq}->{netboxid} and o.orgid=n.orgid",
        PREFIX:       'netbox__prefix',                           # "select p.* from prefix p, netbox n where n.netboxid=$this->{alertq}->{netboxid} and p.prefixid=n.prefixid",
        PRODUCT:      'netbox__device__product',                  # "select p.* from product p, device d, netbox n where n.netboxid=$this->{alertq}->{netboxid} and d.deviceid=n.deviceid and p.productid=d.productid",
        ROOM:         'netbox__room',                             # "select r.* from room r, netbox n where n.netboxid=$this->{alertq}->{netboxid} and r.roomid=n.roomid",
        SERVICE:      'netbox__', #FIXME                          # "select s.* from service s, netbox n where n.netboxid=$this->{alertq}->{netboxid} and s.netboxid=n.netboxid",
        SUBSYSTEM:    '', #FXIME                                   # "select * from subsystem where name=$this->{alertq}->{subid}",
        SWPORT:       'netbox__connected_to_swport',              # "select s.* from swport s,module m, netbox n where n.netboxid=$this->{alertq}->{netboxid} and m.deviceid=n.deviceid and s.moduleid=m.moduleid",
        TYPE:         'netbox__type',                             # "select t.* from type t, netbox n where n.netboxid=$this->{alertq}->{netboxid} and t.typeid=n.typeid",
        TYPEGROUP:    'netbox__type__group', #FIXME               # "select tg.* from typegroup tg,type t, netbox n where n.netboxid=$this->{alertq}->{netboxid} and t.typeid=n.typeid and tg.typegroupid=t.typehroupid",
        USAGE:        'netbox__organization__vlan__usage', #FIXME # "select u.* from usage u,vlan v,org o, netbox n where n.netboxid=$this->{alertq}->{netboxid} and o.orgid=n.orgid and v.orgid=o.orgid and u.usageid=v.usageid",
        VENDOR:       'netbox__device__product__vendor',          # "select v.* from vendor v, product p, device d, netbox n where n.netboxid=$this->{alertq}->{netboxid} and d.deviceid=n.deviceid and p.productid=d.productid and v.vendorid=p.vendorid",
        VLAN:         'netbox__organization__vlan',               # "select v.* from vlan v,org o, netbox n where n.netboxid=$this->{alertq}->{netboxid} and o.orgid=n.orgid and v.orgid=o.orgid",
        SUBCATEGORY:  '', #FIXME                                  # "select s.* from subcat s join netboxcategory n on (s.subcatid=n.category) where n.netboxid=$this->{alertq}->{netboxid}",
        ALERT_TYPE:   'alert_type',                               # "select * from alerttype where alerttypeid=$this->{alertq}->{alerttypeid}",
    }

    id = models.IntegerField(primary_key=True, db_column='matchfieldid')
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1, db_column='descr')
    value_help = models.CharField(max_length=-1, db_column='valuehelp')
    value_id = models.CharField(max_length=-1, db_column='valueid')
    value_name = models.CharField(max_length=-1, db_column='valuename')
    value_category = models.CharField(max_length=-1, db_column='valuecategory')
    value_sort = models.CharField(max_length=-1, db_column='valuesort')
    list_limit = models.IntegerField(db_column='listlimit')
    data_type = models.IntegerField(db_column='datatype', choices=DATA_TYPES)
    show_list = models.BooleanField(db_column='showlist')

    class Meta:
        db_table = u'matchfield'

    def __unicode__(self):
        return self.name

    def get_lookup_mapping(self):
        return self.LOOKUP_MAP[self.value_id]


#######################################################################
### AlertEngine models

class SMSQueue(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    time = models.DateTimeField()
    phone = models.CharField(max_length=15)
    msg = models.CharField(max_length=145)
    sent = models.CharField(max_length=1, default='N') #FIXME change to boolean?
    smsid = models.IntegerField()
    time_sent = models.DateTimeField(db_column='timesent')
    severity = models.IntegerField()

    class Meta:
        db_table = u'smsq'

class AccountAlertQueue(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    addrress = models.ForeignKey('AlarmAddress', db_column='addrid')
    alertid = models.IntegerField()
    insertion_time = models.DateTimeField(auto_now_add=True, db_column='time')

    class Meta:
        db_table = u'queue'

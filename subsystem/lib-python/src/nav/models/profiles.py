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

from django.db import models

_ = lambda a: a

#######################################################################
### Account models

class Account(models.Model):
    id = models.IntegerField(primary_key=True)
    login = models.CharField(max_length=-1)
    name = models.CharField(max_length=-1)
    password = models.CharField(max_length=-1)
    ext_sync = models.CharField(max_length=-1)

    class Meta:
        db_table = u'account'

    def __unicode__(self):
        return self.login

class AccountGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1, db_column='descr')
    accounts = models.ManyToManyField('Account')

    class Meta:
        db_table = u'accountgroup'

class AccountProperty(models.Model):
    account = models.ForeignKey('Account', db_column='accountid')
    property = models.CharField(max_length=-1)
    value = models.CharField(max_length=-1)

    class Meta:
        db_table = u'accountproperty'

class AccountOrg(models.Model):
    account = models.ForeignKey('Account', db_column='accountid')
    orgid = models.CharField(max_length=30) # XXX integer? foreign key?

    class Meta:
        db_table = u'accountorg'

class AlarmAddress(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    type = models.IntegerField()
    address = models.CharField(max_length=-1, db_column='adresse')

    class Meta:
        db_table = u'alarmadresse'

class Preference(models.Model):
    account = models.ForeignKey('Account', primary_key=True,  db_column='accountid')
    queuelength = models.TextField() # This is realy an PG interval FIXME?
    active_profile = models.ForeignKey('AccountProfile', db_column='activeprofile')
    last_sent_day = models.DateTimeField(db_column='lastsentday')
    last_sent_week = models.DateTimeField(db_column='lastsentweek')

    class Meta:
        db_table = u'preference'

class Log(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    type = models.IntegerField()
    time = models.DateTimeField(db_column='tid')
    description = models.CharField(max_length=-1, db_column='descr')

    class Meta:
        db_table = u'logg'

#######################################################################
### Profile models

class Profile(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    name = models.CharField(max_length=-1, db_column='navn')
    time = models.TimeField(db_column='tid')
    weekday = models.IntegerField(db_column='ukedag')
    weektime = models.TimeField(db_column='uketid')

    class Meta:
        db_table = u'brukerprofil'

class TimePeriod(models.Model):
    id = models.IntegerField(primary_key=True)
    profile = models.ForeignKey('AccountProfile', db_column='brukerprofilid')
    start = models.TimeField(db_column='starttid')
    weekend = models.IntegerField(db_column='helg')

    class Meta:
        db_table = u'tidsperiode'

    def __unicode__(self):
        if self.weekend:
            weekend = ' during the weekend'
        else:
            weekend = ''
        return u'From %s for %s%s' % (self.start, self.profile, weekend)

class Alert(models.Model):
    # FIXME add choices

    alarmadresse = models.ForeignKey('AlarmAddress', db_column='alarmadresseid')
    time_period = models.ForeignKey('TimePeriod', db_column='tidsperiodeid')
    equipment_group = models.ForeignKey('EquipmentGroup', db_column='utstyrgruppeid')
    alert_type = models.IntegerField(db_column='vent')

    class Meta:
        db_table = u'varsle'

#######################################################################
### Equipment models

class DefaultEquipment(models.Model):
    account_group = models.ForeignKey('AccountGroup', db_column='accountgroupid')
    equipment_group = models.ForeignKey('EquipmentGroup', db_column='utstyrgruppeid')

    class Meta:
        db_table = u'defaultutstyr'

class GroupFilter(models.Model):
    include = models.BooleanField(db_column='inkluder')
    positive = models.BooleanField(db_column='positiv')
    priority = models.IntegerField(db_column='prioritet')
    equipment_filter = models.ForeignKey('EquipmentFilter', db_column='utstyrfilterid')
    equipment_group = models.ForeignKey('EquipmentGroup', db_column='utstyrgruppeid')

    class Meta:
        db_table = u'gruppetilfilter'

class FilterMatch(models.Model):
    equipment_filter = models.ForeignKey('EquipmentFilter', db_column='utstyrfilterid')
    match_field = models.ForeignKey('MatchField', db_column='matchfelt')
    match_type = models.IntegerField(db_column='matchtype')
    value = models.CharField(max_length=-1, db_column='verdi')

    class Meta:
        db_table = u'filtermatch'

class EquipmentFilter(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    name = models.CharField(max_length=-1, db_column='navn')

    class Meta:
        db_table = u'utstyrfilter'

class EquipmentGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    name = models.CharField(max_length=-1, db_column='navn')
    description = models.CharField(max_length=-1, db_column='descr')

    class Meta:
        db_table = u'utstyrgruppe'

class MatchField(models.Model):
    # FIXME choices all over...

    id = models.IntegerField(primary_key=True, db_column='matchfieldid')
    name = models.CharField(max_length=-1)
    description = models.CharField(max_length=-1, db_column='descr')
    value_help = models.CharField(max_length=-1, db_column='valuehelp')
    value_id = models.CharField(max_length=-1, db_column='valueid')
    value_name = models.CharField(max_length=-1, db_column='valuename')
    value_category = models.CharField(max_length=-1, db_column='valuecategory')
    value_sort = models.CharField(max_length=-1, db_column='valuesort')
    list_limit = models.IntegerField(db_column='listlimit')
    data_type = models.IntegerField(db_column='datatype')
    show_list = models.BooleanField(db_column='showlist')

    class Meta:
        db_table = u'matchfield'

    def __unicode__(self):
        return self.name

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

    OPERATORS = (
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

    operator = models.IntegerField(db_column='operatorid', choices=OPERATORS)
    match_field = models.ForeignKey('MatchField', db_column='matchfieldid')

    class Meta:
        db_table = u'operator'
        unique_together = (('operator', 'match_field'),)

    def __unicode__(self):
        return u'%s match on %s' % (self.get_operator_display(), self.match_field)


#######################################################################
### AlertEngine models

class SMSQueue(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    time = models.DateTimeField()
    phone = models.CharField(max_length=15)
    msg = models.CharField(max_length=145)
    sent = models.TextField() # This field type is a guess.
    smsid = models.IntegerField()
    time_sent = models.DateTimeField(db_column='timesent')
    severity = models.IntegerField()
    class Meta:
        db_table = u'smsq'

class Queue(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    addrress = models.ForeignKey('AlarmAddress', db_column='addrid')
    alertid = models.IntegerField()
    time = models.DateTimeField()
    class Meta:
        db_table = u'queue'


#######################################################################
### XXX models

class DefaultFilter(models.Model):
    account_group = models.ForeignKey('AccountGroup', db_column='accountgroupid')
    equipment_filter = models.ForeignKey('EquipmentFilter', db_column='utstyrfilterid')

    class Meta:
        db_table = u'defaultfilter'

class AccountNavBar(models.Model):
    account = models.ForeignKey('Account', db_column='accountid')
    navbarlink = models.ForeignKey('NavBarLink', db_column='navbarlinkid')
    positions = models.CharField(max_length=-1)

    class Meta:
        db_table = u'accountnavbar'

class AccountGroupPrivilege(models.Model):
    accountgroup = models.ForeignKey('AccountGroup', db_column='accountgroupid')
    privilege = models.ForeignKey('Privilege', db_column='privilegeid')
    target = models.CharField(max_length=-1)

    class Meta:
        db_table = u'accountgroupprivilege'

class Brukerrettighet(models.Model): # FIXME norwegian name
    account = models.ForeignKey('Account', db_column='accountid')
    equipment_group = models.ForeignKey('EquipmentGroup', db_column='utstyrgruppeid')

    class Meta:
        db_table = u'brukerrettighet'

class NavBarLink(models.Model):
    id = models.IntegerField(primary_key=True)
    account = models.ForeignKey('Account', db_column='accountid')
    name = models.CharField(max_length=-1)
    uri = models.CharField(max_length=-1)

    class Meta:
        db_table = u'navbarlink'

class PrivilegeByGroup(models.Model):
    account_group = models.IntegerField(db_column='accountgroupid')
    action = models.CharField(max_length=30)
    target = models.CharField(max_length=-1)

    class Meta:
        db_table = u'privilegebygroup'

class AlertPrivilege(models.Model):
    id = models.IntegerField(primary_key=True, db_column='privilegeid')
    name = models.CharField(unique=True, max_length=30, db_column='privilegename')

    class Meta:
        db_table = u'privilege'

class GroupAlertPrivilege(models.Model):
    account_group = models.ForeignKey('AccountGroup', db_column='accountgroupid')
    equipment_group = models.ForeignKey('EquipmentGroup', db_column='utstyrgruppeid')
    class Meta:
        db_table = u'rettighet'

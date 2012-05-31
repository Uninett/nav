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
"""Django ORM wrapper for profiles in NAV"""

# pylint: disable=R0903

import logging
import os
from datetime import datetime
import re
# To stay compatible with both python 2.4 and 2.6:
from nav.django.forms import MultiSelectField

try:
    from hashlib import md5
except ImportError:
    from md5 import md5


from django.db import models, transaction

import nav.path
import nav.pwhash
from nav.config import getconfig as get_alertengine_config
from nav.alertengine.dispatchers import DispatcherException
from nav.alertengine.dispatchers import FatalDispatcherException

from nav.models.event import AlertQueue, AlertType, EventType
from nav.models.manage import Arp, Cam, Category, Device, Location
from nav.models.manage import Memory, Netbox, NetboxInfo, NetboxType
from nav.models.manage import Organization, Prefix, Room, Subcategory
from nav.models.manage import Interface, Usage, Vlan, Vendor
from nav.models.fields import VarcharField

configfile = os.path.join(nav.path.sysconfdir, 'alertengine.conf')

# This should be the authorative source as to which models alertengine
# supports.  The acctuall mapping from alerts to data in these models is done
# the MatchField model.
SUPPORTED_MODELS = [
    # event models
        AlertQueue, AlertType, EventType,
    # manage models
        Arp, Cam, Category, Device, Location, Memory, Netbox, NetboxInfo,
        NetboxType, Organization, Prefix, Room, Subcategory, Interface,
        Vendor, Vlan,
        Usage,
]

_ = lambda a: a

#######################################################################
### Account models

class Account(models.Model):
    ''' NAV's basic account model'''

    DEFAULT_ACCOUNT = 0
    ADMIN_ACCOUNT = 1

    # FIXME get this from setting.
    MIN_PASSWD_LENGTH = 8

    login = VarcharField(unique=True)
    name = VarcharField()
    password = VarcharField()
    ext_sync = VarcharField()

    organizations = models.ManyToManyField(Organization, db_table='accountorg')

    class Meta:
        db_table = u'account'
        ordering = ('login',)

    def __unicode__(self):
        return self.login

    def get_active_profile(self):
        '''Returns the accounts active alert profile'''
        return self.alertpreference.active_profile

    def get_groups(self):
        '''Fetches and returns this users groups.
        Also stores groups in this object for later use.
        '''
        try:
            return self._cached_groups
        except AttributeError:
            self._cached_groups = self.accountgroup_set.values_list(
                'id', flat=True)
            return self._cached_groups

    def get_privileges(self):
        '''Fetches privileges for this users groups.
        Also stores privileges in this object for later use.
        '''
        try:
            return self._cached_privileges
        except AttributeError:
            self._cached_privileges = Privilege.objects.filter(
                group__in=self.get_groups())
            return self._cached_privileges

    def has_perm(self, action, target):
        '''Checks if user has permission to do action on target.'''
        groups = self.get_groups()
        privileges = self.get_privileges()

        if AccountGroup.ADMIN_GROUP in groups:
            return True
        elif privileges.count() == 0:
            return False
        elif action == 'web_access':
            for privilege in privileges:
                regexp = re.compile(privilege.target)
                if regexp.search(target):
                    return True
            return False
        else:
            return privileges.filter(target=target).count() > 0

    def is_system_account(self):
        """Is this system (undeleteable) account?"""
        return self.id < 1000

    def is_default_account(self):
        """Is this the anonymous user account?"""
        return self.id == self.DEFAULT_ACCOUNT

    def is_admin_account(self):
        """Is this the admin account?"""
        return self.id == self.ADMIN_ACCOUNT

    def set_password(self, password):
        '''Sets user password. Copied from nav.db.navprofiles'''
        if len(password.strip()):
            pw_hash = nav.pwhash.Hash(password=password)
            self.password = str(pw_hash)
        else:
            self.password = ''

    def check_password(self, password):
        """
        Return True if the submitted authentication tokens are valid
        for this Account.  In simpler terms; when password
        authentication is used, this method compares the given
        password with the one stored for this account and returns true
        if they are equal.  If the stored password is blank, we
        interpret this as: 'The user is not allowed to log in'

        In the future, this could be extended to accept other types of
        authentication tokens, such as personal certificates or
        whatever.

        Copied from nav.db.navprofiles
        """
        # FIXME If password is old style NAV MD5, shouldn't we update the
        # password in the database to be new style password?
        if len(self.password.strip()) > 0:
            stored_hash = nav.pwhash.Hash()
            try:
                stored_hash.set_hash(self.password)
            except nav.pwhash.InvalidHashStringError:
                # Probably an old style NAV password hash, get out
                # of here and check it the old way
                pass
            else:
                return stored_hash.verify(password)

            # If the stored password looks like an old-style NAV MD5
            # hash we compute the MD5 hash of the supplied password
            # for comparison.
            if self.password[:3] == 'md5':
                pw_hash = md5(password)
                return (pw_hash.hexdigest() == self.password[3:])
            else:
                return (password == self.password)
        else:
            return False

class AccountGroup(models.Model):
    '''NAV account groups'''

    # FIXME other places in code that use similiar definitions should switch to
    # using this one.
    ADMIN_GROUP = 1
    EVERYONE_GROUP = 2
    AUTHENTICATED_GROUP = 3

    name = VarcharField()
    description = VarcharField(db_column='descr')
    # FIXME this uses a view hack, was AccountInGroup
    accounts = models.ManyToManyField('Account')

    class Meta:
        db_table = u'accountgroup'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def is_system_group(self):
        """Is this a system (undeleteable) group?"""
        return self.id < 1000

    def is_protected_group(self):
        """Is this a protected group?

        Users cannot be removed from protected groups.

        """
        return self.id in [self.EVERYONE_GROUP, self.AUTHENTICATED_GROUP]

    def is_admin_group(self):
        """Is this the administrators group?"""
        return self.id == self.ADMIN_GROUP

class AccountProperty(models.Model):
    '''Key-value for account settings'''

    account = models.ForeignKey('Account', db_column='accountid', null=True)
    property = VarcharField()
    value = VarcharField()

    class Meta:
        db_table = u'accountproperty'

    def __unicode__(self):
        return '%s=%s' % (self.property, self.value)

class AccountNavbar(models.Model):
    """A user's web ui navigation bar."""
    account = models.ForeignKey('Account', db_column='accountid')
    navbarlink = models.ForeignKey('NavbarLink', db_column='navbarlinkid')
    positions = VarcharField()

    class Meta:
        db_table = u'accountnavbar'

    def __unicode__(self):
        return '%s in %s' % (self.navbarlink.name, self.positions)

class NavbarLink(models.Model):
    """A hyperlink on a user's navigation bar."""
    account = models.ForeignKey('Account', db_column='accountid')
    name = VarcharField()
    uri = VarcharField()

    class Meta:
        db_table = u'navbarlink'

    def __unicode__(self):
        return '%s=%s' % (self.name, self.uri)

class Privilege(models.Model):
    """A privilege granted to an AccountGroup."""
    group = models.ForeignKey('AccountGroup', db_column='accountgroupid')
    type = models.ForeignKey('PrivilegeType', db_column='privilegeid')
    target = VarcharField()

    class Meta:
        db_table = u'accountgroupprivilege'

    def __unicode__(self):
        return '%s for %s' % (self.type, self.target)


class PrivilegeType(models.Model):
    """A registered privilege type."""
    id = models.AutoField(db_column='privilegeid', primary_key=True)
    name = models.CharField(max_length=30, db_column='privilegename')

    class Meta:
        db_table = u'privilege'

    def __unicode__(self):
        return self.name

class AlertAddress(models.Model):
    """Accounts alert addresses, valid types are retrived from
    alertengine.conf

    """
    DEBUG_MODE = False

    account = models.ForeignKey('Account', db_column='accountid')
    type = models.ForeignKey('AlertSender', db_column='type')
    address = VarcharField()

    class Meta:
        db_table = u'alertaddress'

    def __unicode__(self):
        return '%s by %s' % (self.address, self.type.name)

    @transaction.commit_manually
    def send(self, alert, subscription, dispatcher={}):
        '''Handles sending of alerts to with defined alert notification types

           Return value should indicate if message was sent'''

        logger = logging.getLogger('nav.alertengine.alertaddress.send')

        # Determine the right language for the user.
        try:
            lang = self.account.accountproperty_set.get(
                property='language').value or 'en'
        except AccountProperty.DoesNotExist:
            lang = 'en'

        if not (self.address or '').strip():
            logger.error(
                'Ignoring alert %d (%s: %s)! Account %s does not have an '
                'address set for the alertaddress with id %d, this needs '
                'to be fixed before the user will recieve any alerts.',
                alert.id, alert, alert.netbox, self.account, self.id)

            transaction.commit()

            return True

        if self.type.is_blacklisted():
            transaction.rollback()

            logger.warning(
                'Not sending alert %s to %s as handler %s is blacklisted: %s',
                alert.id, self.address, self.type, self.type.blacklist_reason())

            return False

        try:
            self.type.send(self, alert, language=lang)
            transaction.commit()

            logger.info(
                'alert %d sent by %s to %s due to %s subscription %d',
                alert.id, self.type, self.address,
                subscription.get_type_display(), subscription.id)

        except FatalDispatcherException, error:
            logger.error(
                '%s raised a FatalDispatcherException indicating that the '
                'alert never will be sent: %s',
                self.type, error)
            transaction.rollback()

            raise

        except DispatcherException, error:
            logger.error(
                '%s raised a DispatcherException indicating that an alert '
                'could not be sent at this time: %s',
                self.type, error)
            transaction.rollback()

            return False

        except Exception, error:
            logger.exception(
                'Unhandeld error from %s (the handler has been blacklisted)',
                self.type)
            transaction.rollback()
            self.type.blacklist(e)
            return False

        return True

class AlertSender(models.Model):
    """A registered alert sender/medium."""
    name = models.CharField(max_length=100)
    handler = models.CharField(max_length=100)

    _blacklist = {}
    _handlers = {}

    def __unicode__(self):
        return self.name

    def send(self, *args, **kwargs):
        """Sends an alert via this medium."""
        if self.handler not in self._handlers:
            # Get config
            if not hasattr(AlertSender, 'config'):
                AlertSender.config = get_alertengine_config(
                    os.path.join(nav.path.sysconfdir, 'alertengine.conf'))

            # Load module
            module = __import__(
                'nav.alertengine.dispatchers.%s_dispatcher' % self.handler,
                globals(), locals(), [self.handler])

            # Init module with config
            self.__class__._handlers[self.handler] = getattr(
                module, self.handler)(config=AlertSender.config.get(
                    self.handler, {}))

        # Delegate sending of message
        return self._handlers[self.handler].send(*args, **kwargs)

    def blacklist(self, reason=None):
        """Blacklists this sender/medium from further alert dispatch."""
        self.__class__._blacklist[self.handler] = reason

    def is_blacklisted(self):
        """Gets the blacklist status of this sender/medium."""
        return self.handler in self.__class__._blacklist

    def blacklist_reason(self):
        return self.__class__._blacklist.get(self.handler, 'Unknown reason')

    class Meta:
        db_table = 'alertsender'

class AlertPreference(models.Model):
    '''AlertProfile account preferences'''

    account = models.OneToOneField('Account', primary_key=True,
                                   db_column='accountid')
    active_profile = models.OneToOneField('AlertProfile',
                                          db_column='activeprofile', null=True)
    last_sent_day = models.DateTimeField(db_column='lastsentday')
    last_sent_week = models.DateTimeField(db_column='lastsentweek')

    class Meta:
        db_table = u'alertpreference'

    def __unicode__(self):
        return 'preferences for %s' % self.account


#######################################################################
### Profile models

class AlertProfile(models.Model):
    '''Account AlertProfiles'''

    # Weekday numbers follows date.weekday(), not day.isoweekday().
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    VALID_WEEKDAYS = (
        (MONDAY, _('monday')),
        (TUESDAY, _('tuesday')),
        (WEDNESDAY, _('wednesday')),
        (THURSDAY, _('thursday')),
        (FRIDAY, _('friday')),
        (SATURDAY, _('saturday')),
        (SUNDAY, _('sunday')),
    )

    account = models.ForeignKey('Account', db_column='accountid')
    name = VarcharField()
    daily_dispatch_time = models.TimeField(default='08:00')
    weekly_dispatch_day = models.IntegerField(choices=VALID_WEEKDAYS,
                                              default=MONDAY)
    weekly_dispatch_time = models.TimeField(default='08:00')

    class Meta:
        db_table = u'alertprofile'

    def __unicode__(self):
        return self.name

    def get_active_timeperiod(self):
        '''Gets the currently active timeperiod for this profile'''
        # Could have been done with a ModelManager, but the logic
        # is somewhat tricky to do with the django ORM.

        logger = logging.getLogger(
            'nav.alertengine.alertprofile.get_active_timeperiod')

        now = datetime.now()

        # Limit our query to the correct type of time periods
        if now.isoweekday() in [6, 7]:
            valid_during = [TimePeriod.ALL_WEEK, TimePeriod.WEEKENDS]
        else:
            valid_during = [TimePeriod.ALL_WEEK, TimePeriod.WEEKDAYS]

        # The following code should get the currently active timeperiod.
        active_timeperiod = None
        timeperiods = list(self.timeperiod_set.filter(
                valid_during__in=valid_during).order_by('start'))
        # If the current time is before the start of the first time
        # period, the active time period is the last one (i.e. from
        # the day before)
        if len(timeperiods) > 0 and timeperiods[0].start > now.time():
            active_timeperiod = timeperiods[-1]
        else:
            for period in timeperiods:
                if period.start <= now.time():
                    active_timeperiod = period

        if active_timeperiod:
            logger.debug("Active timeperiod for alertprofile %d is %s (%d)",
                         self.id, active_timeperiod, active_timeperiod.id)
        else:
            logger.debug("No active timeperiod for alertprofile %d", self.id)

        return active_timeperiod

class TimePeriod(models.Model):
    '''Defines TimerPeriods and which part of the week they are valid'''

    ALL_WEEK = 1
    WEEKDAYS = 2
    WEEKENDS = 3

    VALID_DURING_CHOICES = (
        (ALL_WEEK, _('all days')),
        (WEEKDAYS, _('weekdays')),
        (WEEKENDS, _('weekends')),
    )

    profile = models.ForeignKey('AlertProfile', db_column='alert_profile_id')
    start = models.TimeField(db_column='start_time', default='08:00')
    valid_during = models.IntegerField(choices=VALID_DURING_CHOICES,
                                       default=ALL_WEEK)

    class Meta:
        db_table = u'timeperiod'

    def __unicode__(self):
        return u'from %s for %s profile on %s' % (
            self.start, self.profile, self.get_valid_during_display())

class AlertSubscription(models.Model):
    """Links an address and timeperiod to a filtergroup with a given
    subscription type.

    """
    NOW = 0
    DAILY = 1
    WEEKLY = 2
    NEXT = 3

    SUBSCRIPTION_TYPES = (
        (NOW, _('immediately')),
        (DAILY, _('daily at predefined time')),
        (WEEKLY, _('weekly at predefined time')),
        (NEXT, _('at end of timeperiod')),
    )

    alert_address = models.ForeignKey('AlertAddress')
    time_period = models.ForeignKey('TimePeriod')
    filter_group = models.ForeignKey('FilterGroup')
    type = models.IntegerField(db_column='subscription_type',
                               choices=SUBSCRIPTION_TYPES, default=NOW)
    ignore_resolved_alerts = models.BooleanField()

    class Meta:
        db_table = u'alertsubscription'

    def __unicode__(self):
        return 'alerts received %s should be sent %s to %s' % (
            self.time_period, self.get_type_display(), self.alert_address)

#######################################################################
### Equipment models

class FilterGroupContent(models.Model):
    '''Defines how a given filter should be used in a filtergroup'''

    #            inc   pos
    # Add      |  1  |  1  | union in set theory
    # Sub      |  0  |  1  | exclusion
    # And      |  0  |  0  | intersection in set theory
    # Add inv. |  1  |  0  | complement of set

    # include and positive are used to decide how the match result of the
    # filter should be applied. the table above is an attempt at showing how
    # this should work. Add inv is really the only tricky one, basicly it is
    # nothing more that a negated add, ie if we have a filter  that checks
    # severity > 70 using a add inv on it is equivilent til severity < 70.

    # The actual checking of the FilterGroup is done in the alertengine
    # subsystem in an attempt to keep most of the alerteninge code simple and
    # in one place.

    include = models.BooleanField()
    positive = models.BooleanField()
    priority = models.IntegerField()

    filter = models.ForeignKey('Filter')
    filter_group = models.ForeignKey('FilterGroup')

    class Meta:
        db_table = u'filtergroupcontent'
        ordering = ['priority']

    def __unicode__(self):
        if self.include:
            type_ = 'inclusive'
        else:
            type_ = 'exclusive'

        if not self.positive:
            type_ = 'inverted %s'  % type_

        return '%s filter on %s' % (type_, self.filter)

class Operator(models.Model):
    '''Defines valid operators for a given matchfield.'''

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

    # This list designates which operators are supported for any field. The
    # only major special case is IP's which are matched with special pg ip
    # operators where it makes sense, the rest of the operators are handeled
    # with plain text comaparisons against the result of text(ip)
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

    # This is the mapping that is jused when we try querying the ORM to se if
    # filtes match. Note that wildcard is not here as it neeeds to be special
    # cased.
    OPERATOR_MAPPING = {
        EQUALS: '__exact',
        GREATER: '__gt',
        GREATER_EQ: '__gte',
        LESS: '__lt',
        LESS_EQ: '__lte',
        STARTSWITH: '__istartswith',
        ENDSWITH: '__iendswith',
        CONTAINS: '__icontains',
        REGEXP: '__iregex',
        IN: '__in',
    }

    # The IpAddressField in django does not support ipv6 yet so the IP
    # datatype needs to be completly special cased. The following operator
    # mapping is used to achive this and expects that it will get '% field'
    IP_OPERATOR_MAPPING = {
        EQUALS: '%s = %%s',
        GREATER: '%s > %%s',
        GREATER_EQ: '%s >= %%s',
        LESS: '%s < %%s',
        LESS_EQ: '%s <= %%s',
        NOT_EQUAL: '%s <> %%s',
        CONTAINS: '%s >>= %%s',
        IN: '%s <<= %%s',

        WILDCARD: "host(%s) LIKE %%s",
        REGEXP: "host(%s) ~* %%s",
        STARTSWITH: "host(%s) ILIKE '%%%%' + %%s",
        ENDSWITH: "host(%s) ILIKE %%s + '%%%%'",
    }
    type = models.IntegerField(choices=OPERATOR_TYPES, db_column='operator_id')
    match_field = models.ForeignKey('MatchField')

    class Meta:
        db_table = u'operator'
        unique_together = (('type', 'match_field'),)

    def __unicode__(self):
        return u'%s match on %s' % (self.get_type_display(), self.match_field)

    def get_operator_mapping(self):
        """Returns the Django query operator represented by this instance."""
        return self.OPERATOR_MAPPING[self.type]

    def get_ip_operator_mapping(self):
        """Returns the SQL query IP operator represented by this instance."""
        return self.IP_OPERATOR_MAPPING[self.type]


class Expression(models.Model):
    """Combines filer, operator, matchfield and value into an expression that
    can be evaluated.

    """
    filter = models.ForeignKey('Filter')
    match_field = models.ForeignKey('MatchField')
    operator = models.IntegerField(choices=Operator.OPERATOR_TYPES)
    value = VarcharField()

    class Meta:
        db_table = u'expression'

    def __unicode__(self):
        return '%s match on %s against %s' % (self.get_operator_display(),
                                              self.match_field, self.value)

    def get_operator_mapping(self):
        """Returns the Django query operator represented by this expression."""
        return Operator(type=self.operator).get_operator_mapping()

class Filter(models.Model):
    '''One or more expressions that are combined with an and operation.

    Handles the actual construction of queries to be run taking into account
    special cases like the IP datatype and WILDCARD lookups.'''

    owner = models.ForeignKey('Account', null=True)
    name = VarcharField()

    class Meta:
        db_table = u'filter'

    def __unicode__(self):
        return self.name

    def check(self, alert):
        """Combines expressions to an ORM query that will tell us if an alert
        matched.

        This function builds three dicts that are used in the ORM .filter()
        .exclude() and .extra() methods which finally gets a .count() as we
        only need to know if something matched.

        Running alertengine in debug mode will print the dicts to the logs.

        """
        logger = logging.getLogger('nav.alertengine.filter.check')

        filtr = {}
        exclude = {}
        extra = {'where': [], 'params': []}

        for expression in self.expression_set.all():
            # Handle IP datatypes:
            if expression.match_field.data_type == MatchField.IP:
                # Trick the ORM into joining the tables we want
                lookup = ('%s__isnull' %
                          expression.match_field.get_lookup_mapping())
                filtr[lookup] = False

                where = Operator(
                    type=expression.operator).get_ip_operator_mapping()

                if expression.operator in [Operator.IN, Operator.CONTAINS]:
                    values = expression.value.split('|')
                    where = ' OR '.join(
                        [where % expression.match_field.value_id] *
                        len(values))

                    extra['where'].append('(%s)' % where)
                    extra['params'].extend(values)

                else:
                    # Get the IP mapping and put in the field before adding it
                    # to our where clause.
                    extra['where'].append(
                        where % expression.match_field.value_id)
                    extra['params'].append(expression.value)

            # Handle wildcard lookups which are not directly supported by
            # django (as far as i know)
            elif expression.operator == Operator.WILDCARD:
                # Trick the ORM into joining the tables we want
                lookup = ('%s__isnull' %
                          expression.match_field.get_lookup_mapping())
                filtr[lookup] = False

                extra['where'].append(
                    '%s ILIKE %%s' % expression.match_field.value_id)
                extra['params'].append(expression.value)

            # Handle the plain lookups that we can do directly in ORM
            else:
                lookup = (expression.match_field.get_lookup_mapping() +
                          expression.get_operator_mapping())

                # Ensure that in and not equal are handeled correctly
                if expression.operator == Operator.IN:
                    filtr[lookup] = expression.value.split('|')
                elif expression.operator == Operator.NOT_EQUAL:
                    exclude[lookup] = expression.value
                else:
                    filtr[lookup] = expression.value

        # Limit ourselves to our alert
        filtr['id'] = alert.id

        if not extra['where']:
            extra = {}

        logger.debug(
            'alert %d: checking against filter %d with filter: %s, exclude: '
            '%s and extra: %s',
            alert.id, self.id, filtr, exclude, extra)

        # Check the alert maches whith a SELECT COUNT(*) FROM .... so that the
        # db doesn't have to work as much.
        if AlertQueue.objects.filter(**filtr).exclude(**exclude).extra(
            **extra).count():
            logger.debug('alert %d: matches filter %d' % (alert.id, self.id))
            return True

        logger.debug('alert %d: did not match filter %d' % (alert.id, self.id))
        return False

class FilterGroup(models.Model):
    """A set of filters group contents that an account can subscribe to or be
    given permission to.

    """
    owner = models.ForeignKey('Account', null=True)
    name = VarcharField()
    description = VarcharField()

    group_permissions = models.ManyToManyField(
        'AccountGroup', db_table='filtergroup_group_permission')

    class Meta:
        db_table = u'filtergroup'

    def __unicode__(self):
        return self.name

class MatchField(models.Model):
    '''Defines which fields can be matched upon and how'''

    STRING = 0
    INTEGER = 1
    IP = 2

    # Due to the way alertengine has been reimpleneted the code only really
    # does stuff diffrently if datatype is set to IP, however setting datatype
    # still makes alot of sense in alertprofiles so that we can verify
    # userinput
    DATA_TYPES = (
        (STRING, _('string')),
        (INTEGER, _('integer')),
        (IP, _('ip')),
    )

    # This is a manualy mainted mapping between our model concepts and the
    # actual db tables that are in use. This is needed as our value_id is base
    # on this value.
    ALERT = 'alertq'
    ALERTTYPE = 'alerttype'
    ARP = 'arp'
    CAM = 'cam'
    CATEGORY = 'cat'
    SUBCATEGORY = 'subcat'
    DEVICE = 'device'
    EVENT_TYPE = 'eventtype'
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
    INTERFACE = 'interface'
    TYPE = 'type'
    VENDOR = 'vendor'
    VLAN = 'vlan'
    USAGE = 'usage'

    LOOKUP_FIELDS = (
        (ALERT, _('alert')),
        (ALERTTYPE, _('alert type')),
        (ARP, _('arp')),
        (CAM, _('cam')),
        (CATEGORY, _('category')),
        (SUBCATEGORY, _('subcategory')),
        (DEVICE, _('device')),
        (EVENT_TYPE, _('event type')),
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
        (INTERFACE, _('Interface')),
        (TYPE, _('type')),
        (VENDOR, _('vendor')),
        (VLAN, _('vlan')),
        (USAGE, _('usage')),
    )

    # This mapping designates how a MatchField relates to an alert. (yes the
    # formating is not PEP8, but it wouldn't be very readable otherwise)
    # Since we need to know how things are connected this has been done manualy
    FOREIGN_MAP = {
        ARP:          'netbox__arp',
        CAM:          'netbox__cam',
        CATEGORY:     'netbox__category',
        SUBCATEGORY:  'netbox__netboxcategory__category',
        DEVICE:       'netbox__device',
        EVENT_TYPE:   'event_type',
        LOCATION:     'netbox__room__location',
        MEMORY:       'netbox__memory',
        MODULE:       'netbox__module',
        NETBOX:       'netbox',
        NETBOXINFO:   'netbox__info',
        ORGANIZATION: 'netbox__organization',
        PREFIX:       'netbox__prefix',
        PRODUCT:      'netbox__device__product',
        ROOM:         'netbox__room',
        SERVICE:      'netbox__service',
        INTERFACE:    'netbox__connected_to_interface',
        TYPE:         'netbox__type',
        USAGE:        'netbox__organization__vlan__usage',
        VENDOR:       'netbox__device__product__vendor',
        VLAN:         'netbox__organization__vlan',
        ALERT:        '', # Checks alert object itself
        ALERTTYPE:    'alert_type',
    }

    # Build the mapping we need to be able to do checks.
    VALUE_MAP = {}
    CHOICES = []
    MODEL_MAP = {}

    # This code loops over all the SUPPORTED_MODELS and gets the db_table and
    # db_column so that we can translate them into the correspinding attributes
    # on our django models. (field and model need to be set to None to avoid an
    # ugly side effect of field becoming an acctuall field on MatchField)
    for model in SUPPORTED_MODELS:
        for field in model._meta.fields:
            key = '%s.%s' % (model._meta.db_table,
                             field.db_column or field.attname)
            value = '%s__%s' % (FOREIGN_MAP[model._meta.db_table],
                                field.attname)

            VALUE_MAP[key] = field.attname
            CHOICES.append((key, value.lstrip('_')))
            MODEL_MAP[key] = (model, field.attname)
        field = None
    model = None

    name = VarcharField()
    description = VarcharField(blank=True)
    value_help = VarcharField(
        blank=True,
        help_text=_(u'Help text for the match field. Displayed by the value '
                    u'input box in the GUI to help users enter sane values.')
    )
    value_id = VarcharField(
        choices=CHOICES,
        help_text=_(u'The "match field". This is the actual database field '
                    u'alert engine will watch.')
    )
    value_name = VarcharField(
        choices=CHOICES,
        blank=True,
        help_text=_(u'When "show list" is checked, the list will be populated '
                    u'with data from this column as well as the "value id" '
                    u'field. Does nothing else than provide a little more '
                    u'info for the users in the GUI.')
    )
    value_sort = VarcharField(
        choices=CHOICES,
        blank=True,
        help_text=_(u'Options in the list will be ordered by this field (if '
                    u'not set, options will be ordered by primary key). Only '
                    u'does something when "Show list" is checked.')
    )
    list_limit = models.IntegerField(
        blank=True,
        help_text=_(u'Only this many options will be available in the list. '
                    u'Only does something when "Show list" is checked.')
    )
    data_type = models.IntegerField(
        choices=DATA_TYPES,
        help_text=_(u'The data type of the match field.')
    )
    show_list = models.BooleanField(
        blank=True,
        help_text=_(u'If unchecked values can be entered into a text input. '
                    u'If checked values must be selected from a list '
                    u'populated by data from the match field selected above.')
    )

    class Meta:
        db_table = u'matchfield'

    def __unicode__(self):
        return self.name

    def get_lookup_mapping(self):
        """Returns the field lookup represented by this MatchField."""
        logger = logging.getLogger(
            'nav.alertengine.matchfield.get_lookup_mapping')

        try:
            foreign_lookup = self.FOREIGN_MAP[self.value_id.split('.')[0]]
            value = self.VALUE_MAP[self.value_id]

            if foreign_lookup:
                return '%s__%s' % (foreign_lookup, value)
            return value

        except KeyError:
            logger.error(
                "Tried to lookup mapping for %s which is not supported",
                self.value_id)
        return None


#######################################################################
### AlertEngine models

class SMSQueue(models.Model):
    '''Queue of messages that should be sent or have been sent by SMSd'''

    SENT = 'Y'
    NOT_SENT = 'N'
    IGNORED = 'I'

    SENT_CHOICES = (
        (SENT, _('sent')),
        (NOT_SENT, _('not sent yet')),
        (IGNORED, _('ignored')),
    )

    account = models.ForeignKey('Account', db_column='accountid', null=True)
    time = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=15)
    message = models.CharField(max_length=145, db_column='msg')
    sent = models.CharField(max_length=1, default=NOT_SENT,
                            choices=SENT_CHOICES)
    sms_id = models.IntegerField(db_column='smsid')
    time_sent = models.DateTimeField(db_column='timesent')
    severity = models.IntegerField()

    class Meta:
        db_table = u'smsq'

    def __unicode__(self):
        return '"%s" to %s, sent: %s' % (self.message, self.phone, self.sent)

    def save(self, *args, **kwargs):
        """Overrides save to truncate long messages (max is 145)"""
        if len(self.message) > 142:
            self.message = self.message[:142] + '...'

        return super(SMSQueue, self).save(*args, **kwargs)

class AccountAlertQueue(models.Model):
    '''Defines which alerts should be keept around and sent at a later time'''

    account = models.ForeignKey('Account', null=True)
    subscription = models.ForeignKey('AlertSubscription', null=True)
    alert = models.ForeignKey('AlertQueue', null=True)
    insertion_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = u'accountalertqueue'

    def delete(self, *args, **kwargs):
        """Deletes the alert from the user's alert queue.

        Also deletes the alert globally if not queued for anyone else.

        """
        # TODO deleting items with the manager will not trigger this behaviour
        # cleaning up related messages.

        super(AccountAlertQueue, self).delete(*args, **kwargs)

        # Remove the alert from the AlertQueue if we are the last item
        # depending upon it.
        if self.alert.accountalertqueue_set.count() == 0:
            self.alert.delete()

    def send(self):
        '''Sends the alert in question to the address in the subscription'''
        try:
            sent = self.subscription.alert_address.send(self.alert,
                                                        self.subscription)
        except AlertSender.DoesNotExist:
            address = self.subscription.alert_address
            sender  = address.type_id

            if sender is not None:
                raise Exception(
                    "Invalid sender set for address %s, "
                    "please check that %s is in profiles.alertsender" %
                    (address, sender))
            else:
                raise Exception(
                    "No sender set for address %s, this might be due to a "
                    "failed db upgrade from 3.4 to 3.5" % (address))

        except AlertQueue.DoesNotExist:
            logger = logging.getLogger('nav.alertengine.accountalertqueue.send')
            logger.error(('Inconsistent database state, alertqueue entry %d ' +
                          'missing for account-alert. If you know how the ' +
                          'database got into this state please update ' +
                          'LP#494036') % self.alert_id)

            super(AccountAlertQueue, self).delete()
            return False
        except FatalDispatcherException:
            self.delete()
            return False

        if sent:
            self.delete()

        return sent

class StatusPreference(models.Model):
    '''Preferences for the Status tool'''

    SECTION_NETBOX = 'netbox'
    SECTION_NETBOX_MAINTENANCE = 'netbox_maintenance'
    SECTION_MODULE = 'module'
    SECTION_SERVICE = 'service'
    SECTION_SERVICE_MAINTENANCE = 'service_maintenance'
    SECTION_THRESHOLD = 'threshold'
    SECTION_LINKSTATE = 'linkstate'
    SECTION_SNMPAGENT = 'snmpagent'

    SECTION_CHOICES = (
        (SECTION_NETBOX, 'IP Devices down'),
        (SECTION_NETBOX_MAINTENANCE, 'IP Devices on maintenance'),
        (SECTION_MODULE, 'Modules down'),
        (SECTION_SERVICE, 'Services down'),
        (SECTION_SERVICE_MAINTENANCE, 'Services on maintenance'),
        (SECTION_THRESHOLD, 'Thresholds exceeded'),
        (SECTION_LINKSTATE, 'Links down'),
        (SECTION_SNMPAGENT, 'SNMP agents down'),
    )

    name = models.TextField()
    position = models.IntegerField()
    type = VarcharField(choices=SECTION_CHOICES)
    account = models.ForeignKey('Account', db_column='accountid')
    organizations = models.ManyToManyField(
        Organization, db_table='statuspreference_organization')
    categories = models.ManyToManyField(
        Category, db_table='statuspreference_category', blank=True)

    services = models.TextField(blank=True)
    states = models.TextField()

    class Meta:
        db_table = u'statuspreference'
        ordering = ('position',)

    def readable_type(self):
        """Returns a human-readable name for this section type."""
        return StatusPreference.lookup_readable_type(self.type)

    @staticmethod
    def lookup_readable_type(type):
        """Returns a human-readable name for the section type."""
        for (identity, readable_type) in StatusPreference.SECTION_CHOICES:
            if type == identity:
                return readable_type

class StatusPreferenceOrganization(models.Model):
    """Organizational filter for a status preference."""
    statuspreference = models.ForeignKey(StatusPreference)
    organization = models.ForeignKey(Organization)

    class Meta:
        db_table = u'statuspreference_organization'

class StatusPreferenceCategory(models.Model):
    """Category filter for a status preference."""
    statuspreference = models.ForeignKey(StatusPreference)
    category = models.ForeignKey(Category)

    class Meta:
        db_table = u'statuspreference_category'

LINK_TYPES = (1, 'Layer 2'),\
(2, 'Layer 2 with VLAN'),\
(3, 'Layer 3')

class NetmapView(models.Model):
    """Properties for a specific view in Netmap"""
    viewid = models.CharField(max_length=20, primary_key=True)
    owner = models.ForeignKey('Account', db_column='accountid'),
    title = models.TextField()
    link_types = MultiSelectField(max_length=250, blank=False, choices=LINK_TYPES)
    categories = models.ForeignKey('Category', db_column='catid')
    zoom = models.CharField(max_length=255) # picke x,y,scale (translate(x,y) , scale(scale)
    last_modified = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = u'netmap_view'

class NetmapViewNodePosition(models.Model):
    viewid = models.ForeignKey('NetmapView', db_column='viewid')
    netbox = models.ForeignKey('Netbox', db_column='netboxid', related_name='node_position_set')
    x = models.IntegerField()
    y = models.IntegerField()

    class Meta:
        db_table = u'netmap_view_nodeposition'
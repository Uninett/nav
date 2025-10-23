# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Uninett AS
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
"""Django ORM wrapper for profiles in NAV"""

from hashlib import md5
import itertools
import logging
from datetime import datetime
import re
import json

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.postgres.fields import HStoreField
from django.core.cache import cache
from django.db import models, transaction
from django.forms.models import model_to_dict
from django.urls import reverse
from django.views.decorators.debug import sensitive_variables

import nav.buildconf
import nav.pwhash
from nav.config import getconfig as get_alertengine_config
from nav.alertengine.dispatchers import (
    DispatcherException,
    FatalDispatcherException,
    InvalidAlertAddressError,
)

from nav.models.event import AlertQueue, AlertType, EventType
from nav.models.manage import Arp, Cam, Category, Device, Location
from nav.models.manage import Memory, Netbox, NetboxInfo, NetboxType
from nav.models.manage import Organization, Prefix, Room, NetboxGroup
from nav.models.manage import Interface, Usage, Vlan, Vendor
from nav.models.fields import VarcharField, DictAsJsonField


# This should be the authorative source as to which models alertengine
# supports.  The acctuall mapping from alerts to data in these models is done
# the MatchField model.
SUPPORTED_MODELS = [
    # event models
    AlertQueue,
    AlertType,
    EventType,
    # manage models
    Arp,
    Cam,
    Category,
    Device,
    Location,
    Memory,
    Netbox,
    NetboxInfo,
    NetboxType,
    Organization,
    Prefix,
    Room,
    NetboxGroup,
    Interface,
    Vendor,
    Vlan,
    Usage,
]

_ = lambda a: a

#######################################################################
### Account models


class AccountManager(models.Manager):
    """Custom manager for Account objects"""

    def get_by_natural_key(self, login):
        """Gets Account object by its 'natural' key: Its login name."""
        return self.get(login=login)


class Account(AbstractBaseUser):
    """NAV's basic account model"""

    USERNAME_FIELD = 'login'
    EMAIL_FIELD = 'email'
    DEFAULT_ACCOUNT = 0
    ADMIN_ACCOUNT = 1

    # An overview of current preferences.
    # They should start with PREFERENCE_KEY
    PREFERENCE_KEY_LANGUAGE = 'language'  # AlertProfiles
    PREFERENCE_KEY_STATUS = 'status-preferences'
    PREFERENCE_KEY_REPORT_PAGE_SIZE = 'report_page_size'
    PREFERENCE_KEY_WIDGET_DISPLAY_DENSITY = 'widget_display_density'
    PREFERENCE_KEY_IPDEVINFO_PORT_LAYOUT = 'ipdevinfo_port_layout'

    # FIXME get this from setting.
    MIN_PASSWD_LENGTH = 8

    login = VarcharField(unique=True)
    name = VarcharField()
    email = models.EmailField(null=True, blank=True)  # Not currently used by NAV
    password = VarcharField()
    ext_sync = VarcharField(blank=True)
    preferences = HStoreField(default=dict)

    organizations = models.ManyToManyField(
        Organization,
        db_table='accountorg',
        blank=True,
        related_name="accounts",
    )

    # Set this in order to provide a link to the actual operator when Account
    # objects are retrieved from session data
    sudo_operator = None

    objects = AccountManager()

    class Meta(object):
        db_table = 'account'
        ordering = ('login',)

    def __str__(self):
        if self.sudo_operator and self.sudo_operator != self:
            return '{} (operated by {})'.format(self.login, self.sudo_operator)
        else:
            return self.login

    def natural_key(self) -> tuple[str]:
        """Returns the natural key for an account as a tuple"""
        return (self.login,)

    def get_active_profile(self):
        """Returns the account's active alert profile"""
        try:
            return self.alert_preference.active_profile
        except (AlertPreference.DoesNotExist, AlertProfile.DoesNotExist):
            pass

    def get_groups(self):
        """Fetches and returns this users groups.
        Also stores groups in this object for later use.
        """
        try:
            return self._cached_groups
        except AttributeError:
            self._cached_groups = self.groups.values_list('id', flat=True)
            return self._cached_groups

    def get_privileges(self):
        """Fetches privileges for this users groups.
        Also stores privileges in this object for later use.
        """
        try:
            return self._cached_privileges
        except AttributeError:
            self._cached_privileges = Privilege.objects.filter(
                group__in=self.get_groups()
            )
            return self._cached_privileges

    def get_tools(self):
        """Get the tool list for this account"""
        return [
            tool
            for tool in self.account_tools.all().order_by('priority')
            if self.has_perm('web_access', tool.tool.uri)
        ]

    def has_perm(self, action, target):
        """Checks if user has permission to do action on target."""
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

    def is_admin(self):
        """Has this user administrator rights?"""
        return self.has_perm(None, None)

    @property
    def is_anonymous(self):
        """Returns True if this user represents NAV's anonymous user"""
        return self.id == self.DEFAULT_ACCOUNT

    @property
    def is_authenticated(self):
        """Returns True if this represents an authenticated (non-anonymous) user"""
        return self.id != self.DEFAULT_ACCOUNT

    @property
    def is_staff(self):
        """Returns True if this user is a staff member.

        This is only here for compatibility with Django libraries that may expect this
        to be a django.contrib.auth user model.  NAV has no concept of staff vs
        superuser.  Either the user is an admin, or they're not.
        """
        return self.is_admin()

    @property
    def is_superuser(self):
        """Returns True if this user is a superuser.

        This is only here for compatibility with Django libraries that may expect this
        to be a django.contrib.auth user model.  NAV has no concept of staff vs
        superuser.  Either the user is an admin, or they're not.
        """
        return self.is_admin()

    @sensitive_variables('password')
    def set_password(self, password):
        """Sets user password. Copied from nav.db.navprofiles"""
        from nav.web.auth.utils import PASSWORD_ISSUES_CACHE_KEY

        if password.strip():
            pw_hash = nav.pwhash.Hash(password=password)
            self.password = str(pw_hash)
        else:
            self.password = ''

        # Delete cache entry of how many accounts have password issues
        cache.delete(PASSWORD_ISSUES_CACHE_KEY)

    @sensitive_variables('password')
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
        if not self.locked:
            try:
                stored_hash = self.password_hash
            except nav.pwhash.InvalidHashStringError:
                # Probably an old style NAV password hash, get out
                # of here and check it the old way
                pass
            else:
                return stored_hash.verify(password)

            if self.has_old_style_password_hash():
                return self._verify_old_password_hash_and_rehash(password)
            else:
                return password == self.password
        else:
            return False

    def has_old_style_password_hash(self):
        """Returns True if this account has an old-style, insecure password hash"""
        return self.unlocked_password.startswith("md5")

    def has_plaintext_password(self):
        """Returns True if this account appears to contain a plain-text password"""
        if not self.has_old_style_password_hash():
            try:
                self.password_hash
            except nav.pwhash.InvalidHashStringError:
                return True
        return False

    def has_deprecated_password_hash_method(self):
        """Returns True if this account's password is salted hash, but using a
        deprecated hashing method.
        """
        if not (self.has_plaintext_password() or self.has_old_style_password_hash()):
            return self.password_hash.method != nav.pwhash.DEFAULT_METHOD
        return False

    def has_password_issues(self):
        """Returns True if this account has password issues

        Problems can be an old style password hash, a plaintext password or a deprecated
        password hash method
        """
        return self.is_authenticated and (
            self.has_plaintext_password()
            or self.has_old_style_password_hash()
            or self.has_deprecated_password_hash_method()
        )

    @sensitive_variables('password')
    def _verify_old_password_hash_and_rehash(self, password):
        """Verifies an old-style MD5 password hash, and if there is a match,
        the password is re-hashed using the modern and more secure method.
        """
        pw_hash = md5(password.encode("utf-8"))
        verified = pw_hash.hexdigest() == self.password[3:]
        if verified:
            self.set_password(password)
            if self.pk:
                Account.objects.filter(pk=self.pk).update(password=self.password)

        return verified

    @property
    def locked(self):
        return not self.password or self.password.startswith('!')

    @property
    def is_active(self):
        """Returns True if this account is active (i.e. not locked)"""
        return not self.locked

    @locked.setter
    def locked(self, value):
        if not value:
            self.password = self.password.removeprefix("!")
        elif not self.password.startswith('!'):
            self.password = '!' + self.password

    @property
    def password_hash(self):
        """Returns the Account's password as a Hash object"""
        stored_hash = nav.pwhash.Hash()
        stored_hash.set_hash(self.unlocked_password)
        return stored_hash

    @property
    def unlocked_password(self):
        """Returns the raw password value, but with any lock status stripped"""
        if not self.locked:
            return self.password or ''
        else:
            return self.password[1:] if self.password else ''

    def get_email_addresses(self):
        return self.alert_addresses.filter(type__name=AlertSender.EMAIL)


class AccountGroup(models.Model):
    """NAV account groups"""

    # FIXME other places in code that use similiar definitions should switch to
    # using this one.
    ADMIN_GROUP = 1
    EVERYONE_GROUP = 2
    AUTHENTICATED_GROUP = 3

    name = VarcharField()
    description = VarcharField(db_column='descr')
    # FIXME this uses a view hack, was AccountInGroup
    accounts = models.ManyToManyField(
        'Account',
        related_name="groups",
    )

    class Meta(object):
        db_table = 'accountgroup'
        ordering = ('name',)

    def __str__(self):
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


class NavbarLink(models.Model):
    """A hyperlink on a user's navigation bar."""

    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        db_column='accountid',
        related_name="navbar_links",
    )
    name = models.CharField('Link text', blank=False, max_length=100)
    uri = models.CharField('URL', blank=False, max_length=100)

    class Meta(object):
        db_table = 'navbarlink'
        ordering = ('id',)

    def __str__(self):
        return '%s=%s' % (self.name, self.uri)


class Privilege(models.Model):
    """A privilege granted to an AccountGroup."""

    group = models.ForeignKey(
        'AccountGroup',
        on_delete=models.CASCADE,
        db_column='accountgroupid',
        related_name="privileges",
    )
    type = models.ForeignKey(
        'PrivilegeType',
        on_delete=models.CASCADE,
        db_column='privilegeid',
        related_name="privileges",
    )
    target = VarcharField()

    class Meta(object):
        db_table = 'accountgroupprivilege'

    def __str__(self):
        return '%s for %s' % (self.type, self.target)


class PrivilegeType(models.Model):
    """A registered privilege type."""

    id = models.AutoField(db_column='privilegeid', primary_key=True)
    name = models.CharField(max_length=30, db_column='privilegename')

    class Meta(object):
        db_table = 'privilege'

    def __str__(self):
        return self.name


class AlertAddress(models.Model):
    """Accounts alert addresses, valid types are retrived from
    alertengine.conf

    """

    DEBUG_MODE = False

    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        db_column='accountid',
        related_name="alert_addresses",
    )
    type = models.ForeignKey(
        'AlertSender',
        on_delete=models.CASCADE,
        db_column='type',
        related_name="alert_addresses",
    )
    address = VarcharField()

    class Meta(object):
        db_table = 'alertaddress'

    def __str__(self):
        return self.type.scheme() + self.address

    def has_valid_address(self):
        if not self.type.supported or not self.address:
            return False
        dispatcher = self.type.load_dispatcher_class()
        return dispatcher.is_valid_address(self.address)

    @transaction.atomic
    def send(self, alert, subscription):
        """Handles sending of alerts to with defined alert notification types

        Return value should indicate if message was sent"""

        _logger = logging.getLogger('nav.alertengine.alertaddress.send')

        # Determine the right language for the user.
        lang = self.account.preferences.get(Account.PREFERENCE_KEY_LANGUAGE, 'en')

        if not self.has_valid_address():
            _logger.error(
                'Ignoring alert %d (%s: %s)! Account %s does not have a '
                'valid address for the alertaddress with id %d, this needs '
                'to be fixed before the user will recieve any alerts.',
                alert.id,
                alert,
                alert.netbox,
                self.account,
                self.id,
            )

            raise InvalidAlertAddressError

        if self.type.blacklisted_reason:
            _logger.debug(
                'Not sending alert %s to %s as handler %s is blacklisted: %s',
                alert.id,
                self.address,
                self.type,
                self.type.blacklisted_reason,
            )
            return False

        try:
            self.type.send(self, alert, language=lang)
            _logger.info(
                'alert %d sent by %s to %s due to %s subscription %d',
                alert.id,
                self.type,
                self.address,
                subscription.get_type_display(),
                subscription.id,
            )

        except FatalDispatcherException as error:
            _logger.error(
                '%s raised a FatalDispatcherException indicating that the '
                'alert never will be sent: %s',
                self.type,
                error,
            )
            raise

        except DispatcherException as error:
            _logger.error(
                '%s raised a DispatcherException indicating that an alert '
                'could not be sent at this time: %s',
                self.type,
                error,
            )
            return False

        except Exception as error:  # noqa: BLE001
            _logger.exception(
                'Unhandled error from %s (the handler has been blacklisted)', self.type
            )
            self.type.blacklist(str(error))
            return False

        return True


class AlertSender(models.Model):
    """A registered alert sender/medium."""

    name = models.CharField(max_length=100)
    handler = models.CharField(max_length=100)
    supported = models.BooleanField(default=True)
    blacklisted_reason = models.CharField(max_length=100, blank=True)

    _handlers = {}

    EMAIL = 'Email'
    SMS = 'SMS'
    SLACK = 'Slack'

    SCHEMES = {EMAIL: 'mailto:', SMS: 'sms:', SLACK: 'slack:'}

    def __str__(self):
        return self.name

    @transaction.atomic
    def send(self, *args, **kwargs):
        """Sends an alert via this medium."""
        if not self.supported:
            raise FatalDispatcherException("{} is not supported".format(self.name))
        if self.handler not in self._handlers:
            dispatcher_class = self.load_dispatcher_class()
            dispatcher = dispatcher_class(
                config=AlertSender.config.get(self.handler, {})
            )
            self._handlers[self.handler] = dispatcher
        else:
            dispatcher = self._handlers[self.handler]

        # Delegate sending of message
        return dispatcher.send(*args, **kwargs)

    def load_dispatcher_class(self):
        # Get config
        if not hasattr(AlertSender, 'config'):
            AlertSender.config = get_alertengine_config('alertengine.conf')

        # Load module
        module = __import__(
            'nav.alertengine.dispatchers.%s_dispatcher' % self.handler,
            globals(),
            locals(),
            [self.handler],
        )

        # Return matching object from module based on case-insensitive match
        namemap = {name.lower(): obj for name, obj in vars(module).items()}
        return namemap[self.handler.lower()]

    def blacklist(self, reason=None):
        """Blacklists this sender/medium from further alert dispatch."""
        self.blacklisted_reason = reason
        self.save()

    def scheme(self):
        return self.SCHEMES.get(self.name, '')

    class Meta(object):
        db_table = 'alertsender'


class AlertPreference(models.Model):
    """AlertProfile account preferences"""

    account = models.OneToOneField(
        'Account',
        primary_key=True,
        on_delete=models.CASCADE,
        db_column='accountid',
        related_name="alert_preference",
    )
    active_profile = models.OneToOneField(
        'AlertProfile',
        on_delete=models.CASCADE,
        db_column='activeprofile',
        null=True,
        related_name="alert_preference",
    )
    last_sent_day = models.DateTimeField(db_column='lastsentday')
    last_sent_week = models.DateTimeField(db_column='lastsentweek')

    class Meta(object):
        db_table = 'alertpreference'

    def __str__(self):
        return 'preferences for %s' % self.account


#######################################################################
### Profile models


class AlertProfile(models.Model):
    """Account AlertProfiles"""

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

    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        db_column='accountid',
        related_name="alert_profiles",
    )
    name = VarcharField()
    daily_dispatch_time = models.TimeField(default='08:00')
    weekly_dispatch_day = models.IntegerField(choices=VALID_WEEKDAYS, default=MONDAY)
    weekly_dispatch_time = models.TimeField(default='08:00')

    class Meta(object):
        db_table = 'alertprofile'

    def __str__(self):
        return self.name

    def get_active_timeperiod(self):
        """Gets the currently active timeperiod for this profile"""
        # Could have been done with a ModelManager, but the logic
        # is somewhat tricky to do with the django ORM.

        _logger = logging.getLogger(
            'nav.alertengine.alertprofile.get_active_timeperiod'
        )

        now = datetime.now()

        # Limit our query to the correct type of time periods
        if now.isoweekday() in [6, 7]:
            valid_during = [TimePeriod.ALL_WEEK, TimePeriod.WEEKENDS]
        else:
            valid_during = [TimePeriod.ALL_WEEK, TimePeriod.WEEKDAYS]

        # The following code should get the currently active timeperiod.
        active_timeperiod = None
        timeperiods = list(
            self.time_periods.filter(valid_during__in=valid_during).order_by('start')
        )
        # If the current time is before the start of the first time
        # period, the active time period is the last one (i.e. from
        # the day before)
        if timeperiods and timeperiods[0].start > now.time():
            active_timeperiod = timeperiods[-1]
        else:
            for period in timeperiods:
                if period.start <= now.time():
                    active_timeperiod = period

        if active_timeperiod:
            _logger.debug(
                "Active timeperiod for alertprofile %d is %s (%d)",
                self.id,
                active_timeperiod,
                active_timeperiod.id,
            )
        else:
            _logger.debug("No active timeperiod for alertprofile %d", self.id)

        return active_timeperiod


class TimePeriod(models.Model):
    """Defines TimerPeriods and which part of the week they are valid"""

    ALL_WEEK = 1
    WEEKDAYS = 2
    WEEKENDS = 3

    VALID_DURING_CHOICES = (
        (ALL_WEEK, _('all days')),
        (WEEKDAYS, _('weekdays')),
        (WEEKENDS, _('weekends')),
    )

    profile = models.ForeignKey(
        'AlertProfile',
        on_delete=models.CASCADE,
        db_column='alert_profile_id',
        related_name="time_periods",
    )
    start = models.TimeField(db_column='start_time', default='08:00')
    valid_during = models.IntegerField(choices=VALID_DURING_CHOICES, default=ALL_WEEK)

    class Meta(object):
        db_table = 'timeperiod'

    def __str__(self):
        return 'from %s for %s profile on %s' % (
            self.start,
            self.profile,
            self.get_valid_during_display(),
        )


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

    alert_address = models.ForeignKey(
        'AlertAddress',
        on_delete=models.CASCADE,
        related_name="alert_subscriptions",
    )
    time_period = models.ForeignKey(
        'TimePeriod',
        on_delete=models.CASCADE,
        related_name="alert_subscriptions",
    )
    filter_group = models.ForeignKey(
        'FilterGroup',
        on_delete=models.CASCADE,
        related_name="alert_subscriptions",
    )
    type = models.IntegerField(
        db_column='subscription_type', choices=SUBSCRIPTION_TYPES, default=NOW
    )
    ignore_resolved_alerts = models.BooleanField(default=False)

    class Meta(object):
        db_table = 'alertsubscription'

    def delete(self):
        for a in self.queued_alerts.all():
            a.delete()
        super(AlertSubscription, self).delete()

    def __str__(self):
        return 'alerts received %s should be sent %s to %s' % (
            self.time_period,
            self.get_type_display(),
            self.alert_address,
        )


#######################################################################
### Equipment models


class FilterGroupContent(models.Model):
    """Defines how a given filter should be used in a filtergroup"""

    #            inc   pos
    # Add      |  1  |  1  | union in set theory
    # Sub      |  0  |  1  | exclusion
    # And      |  0  |  0  | intersection in set theory
    # Add inv. |  1  |  0  | complement of set

    # include and positive are used to decide how the match result of the
    # filter should be applied. the table above is an attempt at showing how
    # this should work. Add inv is really the only tricky one, basicly it is
    # nothing more that a negated add, ie if we have a filter  that checks
    # severity < 4 using a add inv on it is equivilent til severity >= 4.

    # The actual checking of the FilterGroup is done in the alertengine
    # subsystem in an attempt to keep most of the alerteninge code simple and
    # in one place.

    include = models.BooleanField(default=False)
    positive = models.BooleanField(default=False)
    priority = models.IntegerField()

    filter = models.ForeignKey(
        'Filter',
        on_delete=models.CASCADE,
        related_name="filter_group_contents",
    )
    filter_group = models.ForeignKey(
        'FilterGroup',
        on_delete=models.CASCADE,
        related_name="filter_group_contents",
    )

    class Meta(object):
        db_table = 'filtergroupcontent'
        ordering = ['priority']

    def __str__(self):
        if self.include:
            type_ = 'inclusive'
        else:
            type_ = 'exclusive'

        if not self.positive:
            type_ = 'inverted %s' % type_

        return '%s filter on %s' % (type_, self.filter)


class Operator(models.Model):
    """Defines valid operators for a given matchfield."""

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
        NOT_EQUAL: '',  # exclusion is special-cased by Filter.check()
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
    match_field = models.ForeignKey(
        'MatchField',
        on_delete=models.CASCADE,
        related_name="operators",
    )

    class Meta(object):
        db_table = 'operator'
        unique_together = (('type', 'match_field'),)

    def __str__(self):
        return '%s match on %s' % (self.get_type_display(), self.match_field)

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

    filter = models.ForeignKey(
        'Filter',
        on_delete=models.CASCADE,
        related_name="expressions",
    )
    match_field = models.ForeignKey(
        'MatchField',
        on_delete=models.CASCADE,
        related_name="expressions",
    )
    operator = models.IntegerField(choices=Operator.OPERATOR_TYPES)
    value = VarcharField()

    class Meta(object):
        db_table = 'expression'

    def __str__(self):
        return '%s match on %s against %s' % (
            self.get_operator_display(),
            self.match_field,
            self.value,
        )

    def get_operator_mapping(self):
        """Returns the Django query operator represented by this expression."""
        return Operator(type=self.operator).get_operator_mapping()


class Filter(models.Model):
    """One or more expressions that are combined with an and operation.

    Handles the actual construction of queries to be run taking into account
    special cases like the IP datatype and WILDCARD lookups."""

    owner = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        null=True,
        related_name="filters",
    )
    name = VarcharField()

    class Meta(object):
        db_table = 'filter'

    def __str__(self):
        return self.name

    def verify(self, alert):
        """Combines expressions to an ORM query that will tell us if an alert
        matched.

        This function builds three dicts that are used in the ORM .filter()
        .exclude() and .extra() methods which finally gets a .count() as we
        only need to know if something matched.

        Running alertengine in debug mode will print the dicts to the logs.

        :type alert: nav.models.event.AlertQueue
        """
        _logger = logging.getLogger('nav.alertengine.filter.check')

        filtr = {}
        exclude = {}
        extra = {'where': [], 'params': []}

        for expression in self.expressions.all():
            # Handle IP datatypes:
            if expression.match_field.data_type == MatchField.IP:
                # Trick the ORM into joining the tables we want
                lookup = '%s__isnull' % expression.match_field.get_lookup_mapping()
                filtr[lookup] = False

                where = Operator(type=expression.operator).get_ip_operator_mapping()

                if expression.operator in [Operator.IN, Operator.CONTAINS]:
                    values = expression.value.split('|')
                    where = ' OR '.join(
                        [where % expression.match_field.value_id] * len(values)
                    )

                    extra['where'].append('(%s)' % where)
                    extra['params'].extend(values)

                else:
                    # Get the IP mapping and put in the field before adding it
                    # to our where clause.
                    extra['where'].append(where % expression.match_field.value_id)
                    extra['params'].append(expression.value)

            # Include all sublocations when matching on location
            elif expression.match_field.name == 'Location':
                lookup = "{}__in".format(MatchField.FOREIGN_MAP[MatchField.LOCATION])
                # Location only have two Operators (in and exact) so we handle
                # both with a split
                locations = Location.objects.filter(pk__in=expression.value.split('|'))

                # Find all descendants for locations in a totally readable way
                filtr[lookup] = list(
                    set(
                        itertools.chain(
                            *[
                                location.get_descendants(include_self=True)
                                for location in locations
                            ]
                        )
                    )
                )

            # Handle wildcard lookups which are not directly supported by
            # django (as far as i know)
            elif expression.operator == Operator.WILDCARD:
                # Trick the ORM into joining the tables we want
                lookup = '%s__isnull' % expression.match_field.get_lookup_mapping()
                filtr[lookup] = False

                extra['where'].append('%s ILIKE %%s' % expression.match_field.value_id)
                extra['params'].append(expression.value)

            # Handle the plain lookups that we can do directly in ORM
            else:
                lookup = (
                    expression.match_field.get_lookup_mapping()
                    + expression.get_operator_mapping()
                )

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

        _logger.debug(
            'alert %d: checking against filter %d with filter: %s, exclude: '
            '%s and extra: %s',
            alert.id,
            self.id,
            filtr,
            exclude,
            extra,
        )

        # Check the alert maches whith a SELECT COUNT(*) FROM .... so that the
        # db doesn't have to work as much.
        if AlertQueue.objects.filter(**filtr).exclude(**exclude).extra(**extra).count():
            _logger.debug('alert %d: matches filter %d', alert.id, self.id)
            return True

        _logger.debug('alert %d: did not match filter %d', alert.id, self.id)
        return False


class FilterGroup(models.Model):
    """A set of filters group contents that an account can subscribe to or be
    given permission to.

    """

    owner = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        null=True,
        related_name="filter_groups",
    )
    name = VarcharField()
    description = VarcharField()

    group_permissions = models.ManyToManyField(
        'AccountGroup',
        db_table='filtergroup_group_permission',
        related_name="filter_groups",
    )

    class Meta(object):
        db_table = 'filtergroup'

    def __str__(self):
        return self.name


class MatchField(models.Model):
    """Defines which fields can be matched upon and how"""

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
    NETBOXGROUP = 'netboxgroup'
    DEVICE = 'device'
    EVENT_TYPE = 'eventtype'
    LOCATION = 'location'
    MEMORY = 'mem'
    MODULE = 'module'
    NETBOX = 'netbox'
    NETBOXINFO = 'netboxinfo'
    ORGANIZATION = 'org'
    PREFIX = 'prefix'
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
        (NETBOXGROUP, _('netboxgroup')),
        (DEVICE, _('device')),
        (EVENT_TYPE, _('event type')),
        (LOCATION, _('location')),
        (MEMORY, _('memeroy')),
        (MODULE, _('module')),
        (NETBOX, _('netbox')),
        (NETBOXINFO, _('netbox info')),
        (ORGANIZATION, _('organization')),
        (PREFIX, _('prefix')),
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
        ARP: 'netbox__arp_set',
        CAM: 'netbox__cam_set',
        CATEGORY: 'netbox__category',
        NETBOXGROUP: 'netbox__netboxcategory__category',
        DEVICE: 'netbox__device',
        EVENT_TYPE: 'event_type',
        LOCATION: 'netbox__room__location',
        MEMORY: 'netbox__memory_set',
        MODULE: 'netbox__modules',
        NETBOX: 'netbox',
        NETBOXINFO: 'netbox__info',
        ORGANIZATION: 'netbox__organization',
        PREFIX: 'netbox__prefix',
        ROOM: 'netbox__room',
        SERVICE: 'netbox__service',
        INTERFACE: 'netbox__connected_to_interface',
        TYPE: 'netbox__type',
        USAGE: 'netbox__organization__vlans__usage',
        VENDOR: 'netbox__type__vendor',
        VLAN: 'netbox__organization__vlans',
        ALERT: '',  # Checks alert object itself
        ALERTTYPE: 'alert_type',
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
            key = '%s.%s' % (model._meta.db_table, field.db_column or field.attname)
            value = '%s__%s' % (FOREIGN_MAP[model._meta.db_table], field.attname)

            VALUE_MAP[key] = field.attname
            CHOICES.append((key, value.lstrip('_')))
            MODEL_MAP[key] = (model, field.attname)
        field = None
    model = None

    name = VarcharField()
    description = VarcharField(blank=True)
    value_help = VarcharField(
        blank=True,
        help_text=_(
            'Help text for the match field. Displayed by the value '
            'input box in the GUI to help users enter sane values.'
        ),
    )
    value_id = VarcharField(
        choices=CHOICES,
        help_text=_(
            'The "match field". This is the actual database field '
            'alert engine will watch.'
        ),
    )
    value_name = VarcharField(
        choices=CHOICES,
        blank=True,
        help_text=_(
            'When "show list" is checked, the list will be populated '
            'with data from this column as well as the "value id" '
            'field. Does nothing else than provide a little more '
            'info for the users in the GUI.'
        ),
    )
    value_sort = VarcharField(
        choices=CHOICES,
        blank=True,
        help_text=_(
            'Options in the list will be ordered by this field (if '
            'not set, options will be ordered by primary key). Only '
            'does something when "Show list" is checked.'
        ),
    )
    list_limit = models.IntegerField(
        blank=True,
        help_text=_(
            'Only this many options will be available in the list. '
            'Only does something when "Show list" is checked.'
        ),
    )
    data_type = models.IntegerField(
        choices=DATA_TYPES, help_text=_('The data type of the match field.')
    )
    show_list = models.BooleanField(
        blank=True,
        default=False,
        help_text=_(
            'If unchecked values can be entered into a text input. '
            'If checked values must be selected from a list '
            'populated by data from the match field selected above.'
        ),
    )

    class Meta(object):
        db_table = 'matchfield'

    def __str__(self):
        return self.name

    def get_lookup_mapping(self):
        """Returns the field lookup represented by this MatchField."""
        _logger = logging.getLogger('nav.alertengine.matchfield.get_lookup_mapping')

        try:
            foreign_lookup = self.FOREIGN_MAP[self.value_id.split('.')[0]]
            value = self.VALUE_MAP[self.value_id]

            if foreign_lookup:
                return '%s__%s' % (foreign_lookup, value)
            return value

        except KeyError:
            _logger.error(
                "Tried to lookup mapping for %s which is not supported", self.value_id
            )
        return None


#######################################################################
### AlertEngine models


class SMSQueue(models.Model):
    """Queue of messages that should be sent or have been sent by SMSd"""

    SENT = 'Y'
    NOT_SENT = 'N'
    IGNORED = 'I'

    SENT_CHOICES = (
        (SENT, _('sent')),
        (NOT_SENT, _('not sent yet')),
        (IGNORED, _('ignored')),
    )

    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        db_column='accountid',
        null=True,
        related_name="sms_queues",
    )
    time = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=15)
    message = models.CharField(max_length=145, db_column='msg')
    sent = models.CharField(max_length=1, default=NOT_SENT, choices=SENT_CHOICES)
    sms_id = models.IntegerField(db_column='smsid')
    time_sent = models.DateTimeField(db_column='timesent')
    severity = models.IntegerField()

    class Meta(object):
        db_table = 'smsq'

    def __str__(self):
        return '"%s" to %s, sent: %s' % (self.message, self.phone, self.sent)

    def save(self, *args, **kwargs):
        """Overrides save to truncate long messages (max is 145)"""
        if len(self.message) > 142:
            self.message = self.message[:142] + '...'

        return super(SMSQueue, self).save(*args, **kwargs)


class AccountAlertQueue(models.Model):
    """Defines which alerts should be keept around and sent at a later time"""

    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        null=True,
        related_name="queued_alerts",
    )
    subscription = models.ForeignKey(
        'AlertSubscription',
        on_delete=models.CASCADE,
        null=True,
        related_name="queued_alerts",
    )
    alert = models.ForeignKey(
        'AlertQueue',
        on_delete=models.CASCADE,
        null=True,
        related_name="queued_alerts",
    )
    insertion_time = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        db_table = 'accountalertqueue'

    def delete(self, *args, **kwargs):
        """Deletes the alert from the user's alert queue.

        Also deletes the alert globally if not queued for anyone else.

        """
        # TODO deleting items with the manager will not trigger this behaviour
        # cleaning up related messages.

        super(AccountAlertQueue, self).delete(*args, **kwargs)

        # Remove the alert from the AlertQueue if we are the last item
        # depending upon it.
        if self.alert.queued_alerts.count() == 0:
            self.alert.delete()

    def send(self):
        """Sends the alert in question to the address in the subscription"""
        try:
            sent = self.subscription.alert_address.send(self.alert, self.subscription)
        except AlertSender.DoesNotExist:
            address = self.subscription.alert_address
            sender = address.type_id

            if sender is not None:
                raise Exception(
                    "Invalid sender set for address %s, "
                    "please check that %s is in profiles.alertsender"
                    % (address, sender)
                )
            else:
                raise Exception(
                    "No sender set for address %s, this might be due to a "
                    "failed db upgrade from 3.4 to 3.5" % address
                )

        except AlertQueue.DoesNotExist:
            _logger = logging.getLogger('nav.alertengine.accountalertqueue.send')
            _logger.error(
                (
                    'Inconsistent database state, alertqueue entry %d '
                    + 'missing for account-alert. If you know how the '
                    + 'database got into this state please update '
                    + 'LP#494036'
                ),
                self.alert_id,
            )

            super(AccountAlertQueue, self).delete()
            return False
        except (FatalDispatcherException, InvalidAlertAddressError):
            self.delete()
            return False

        if sent:
            self.delete()

        return sent


# Make sure you update netmap-extras.js too if you change this! ;-)
LINK_TYPES = (2, 'Layer 2'), (3, 'Layer 3')


class NetmapView(models.Model):
    """Properties for a specific view in Netmap"""

    viewid = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        db_column='owner',
        related_name="netmap_views",
    )
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    topology = models.IntegerField(choices=LINK_TYPES)
    # picke x,y,scale (translate(x,y) , scale(scale)
    zoom = models.CharField(max_length=255)
    last_modified = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    display_elinks = models.BooleanField(default=False)
    display_orphans = models.BooleanField(default=False)
    location_room_filter = models.CharField(max_length=255, blank=True)
    categories = models.ManyToManyField(
        Category, through='NetmapViewCategories', related_name='netmap_views'
    )

    def __str__(self):
        return '%s (%s)' % (self.viewid, self.title)

    def topology_unicode(self):
        return dict(LINK_TYPES).get(self.topology)

    def get_absolute_url(self):
        return "%s#/netmap/%s" % (reverse('netmap-index'), self.viewid)

    def get_set_defaultview_url(self):
        """URL for admin django view to set a default view"""
        return reverse('netmap-api-netmap-defaultview-global')

    class Meta(object):
        db_table = 'netmap_view'


class NetmapViewDefaultView(models.Model):
    """Default view for each user"""

    id = models.AutoField(primary_key=True)
    view = models.ForeignKey(
        NetmapView,
        on_delete=models.CASCADE,
        db_column='viewid',
        related_name="default_views",
    )
    owner = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        db_column='ownerid',
        related_name="default_views",
    )

    class Meta(object):
        db_table = 'netmap_view_defaultview'

    def __repr__(self):
        return "{name}{args!r}".format(
            name=self.__class__.__name__, args=(self.id, self.view, self.owner)
        )


class NetmapViewCategories(models.Model):
    """Saved categories for a selected view in Netmap"""

    id = models.AutoField(primary_key=True)  # Serial for faking a primary key
    view = models.ForeignKey(
        NetmapView,
        on_delete=models.CASCADE,
        db_column='viewid',
        related_name='netmap_view_categories',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        db_column='catid',
        related_name='netmap_view_categories',
    )

    def __str__(self):
        return '%s in category %s' % (self.view, self.category)

    class Meta(object):
        db_table = 'netmap_view_categories'
        unique_together = (('view', 'category'),)  # Primary key


class NetmapViewNodePosition(models.Model):
    """Saved positions for nodes for a selected view in Netmap"""

    id = models.AutoField(primary_key=True)  # Serial for faking a primary key
    viewid = models.ForeignKey(
        NetmapView,
        on_delete=models.CASCADE,
        db_column='viewid',
        related_name='node_positions',
    )
    netbox = models.ForeignKey(
        Netbox,
        on_delete=models.CASCADE,
        db_column='netboxid',
        related_name='node_positions',
    )
    x = models.IntegerField()
    y = models.IntegerField()

    class Meta(object):
        db_table = 'netmap_view_nodeposition'


class AccountTool(models.Model):
    """Link between tool and account"""

    id = models.AutoField(primary_key=True, db_column='account_tool_id')
    toolname = VarcharField()
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        db_column='accountid',
        related_name="account_tools",
    )
    display = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)

    def __str__(self):
        return "%s - %s" % (self.toolname, self.account)

    class Meta(object):
        db_table = 'accounttool'


class AccountDashboard(models.Model):
    """Stores dashboards for each user"""

    name = VarcharField()
    is_default = models.BooleanField(default=False)
    num_columns = models.IntegerField(default=3)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="account_dashboards",
    )
    is_shared = models.BooleanField(default=False)
    subscriptions = models.ManyToManyField(
        Account,
        through='AccountDashboardSubscription',
        related_name="account_dashboard_subscriptions",
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('dashboard-index-id', kwargs={'did': self.id})

    def to_json_dict(self):
        data = {
            'name': self.name,
            'num_columns': self.num_columns,
            'account': self.account_id,
            'widgets': [],
            'version': 1,
        }
        for widget in self.widgets.all():
            data['widgets'].append(widget.to_json_dict())
        return data

    def can_access(self, account):
        return self.account_id == account.id or self.is_shared

    def can_edit(self, account):
        if account.is_anonymous:
            return False
        return self.account_id == account.id

    def is_subscribed(self, account):
        return self.subscribers.filter(account=account).exists()

    class Meta(object):
        db_table = 'account_dashboard'
        ordering = ('name',)


class AccountDashboardSubscription(models.Model):
    """Subscriptions for dashboards shared between users"""

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="dashboard_subscriptions",
    )
    dashboard = models.ForeignKey(
        AccountDashboard,
        on_delete=models.CASCADE,
        related_name="subscribers",
    )

    class Meta(object):
        db_table = 'account_dashboard_subscription'
        unique_together = (('account', 'dashboard'),)


class AccountNavlet(models.Model):
    """Store information about a users navlets"""

    navlet = VarcharField()
    order = models.IntegerField(default=0, db_column='displayorder')
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        db_column='account',
        related_name="widgets",
    )
    preferences = DictAsJsonField(null=True)
    column = models.IntegerField(db_column='col')
    dashboard = models.ForeignKey(
        AccountDashboard,
        on_delete=models.CASCADE,
        related_name='widgets',
    )

    def __str__(self):
        return "%s - %s" % (self.navlet, self.account)

    def to_json_dict(self):
        return {
            'navlet': self.navlet,
            'preferences': self.preferences,
            'column': self.column,
            'order': self.order,
        }

    class Meta(object):
        db_table = 'account_navlet'
        ordering = ['order']


class ReportSubscription(models.Model):
    """Subscriptions for availability reports"""

    MONTH = 'month'
    WEEK = 'week'
    DAY = 'day'
    PERIODS = ((MONTH, 'monthly'), (WEEK, 'weekly'), (DAY, 'daily'))

    DEVICE = 'device'
    LINK = 'link'
    TYPES = ((DEVICE, 'device availability'), (LINK, 'link availability'))

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="report_subscriptions",
    )
    address = models.ForeignKey(
        AlertAddress,
        on_delete=models.CASCADE,
    )
    period = VarcharField(choices=PERIODS)
    report_type = VarcharField(choices=TYPES)
    exclude_maintenance = models.BooleanField()

    class Meta(object):
        db_table = 'report_subscription'

    def __str__(self):
        if self.report_type == self.LINK:
            return "{} report for {} sent to {}".format(
                self.get_period_description(self.period),
                self.get_type_description(self.report_type),
                self.address.address,
            )

        return "{} report for {} ({} time in maintenance) sent to {}".format(
            self.get_period_description(self.period),
            self.get_type_description(self.report_type),
            'excluding' if self.exclude_maintenance else 'including',
            self.address.address,
        )

    def serialize(self):
        keys = ['report_type', 'period', 'address']
        filtered = {k: v for k, v in model_to_dict(self).items() if k in keys}
        return json.dumps(filtered)

    @staticmethod
    def get_period_description(period):
        return next(v for k, v in ReportSubscription.PERIODS if k == period)

    @staticmethod
    def get_type_description(report_type):
        return next(v for k, v in ReportSubscription.TYPES if k == report_type)

# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2015 Uninett AS
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

# pylint: disable=R0903

import datetime as dt
from functools import partial
from itertools import count, groupby
import logging
import math
import re

import IPy
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible

from nav import util
from nav.adapters import HStoreField
from nav.bitvector import BitVector
from nav.metrics.data import get_netboxes_availability
from nav.metrics.graphs import get_simple_graph_url
from nav.metrics.names import get_all_leaves_below
from nav.metrics.templates import (
    metric_prefix_for_interface,
    metric_prefix_for_ports,
    metric_prefix_for_device,
    metric_prefix_for_sensors,
    metric_path_for_sensor,
    metric_path_for_prefix,
    metric_path_for_power
)
import nav.natsort
from nav.models.fields import DateTimeInfinityField, VarcharField, PointField
from nav.models.fields import CIDRField
import nav.models.event


_logger = logging.getLogger(__name__)

#######################################################################
### Netbox-related models


class UpsManager(models.Manager):
    """Manager for finding UPS netboxes"""
    def get_queryset(self):
        """Filter out UPSes"""
        return super(UpsManager, self).get_queryset().filter(
            category='POWER',
            sensor__internal_name__startswith='ups').distinct()


@python_2_unicode_compatible
class Netbox(models.Model):
    """From NAV Wiki: The netbox table is the heart of the heart so to speak,
    the most central table of them all. The netbox tables contains information
    on all IP devices that NAV manages with adhering information and
    relations."""

    UP_UP = 'y'
    UP_DOWN = 'n'
    UP_SHADOW = 's'
    UP_CHOICES = (
        (UP_UP, 'up'),
        (UP_DOWN, 'down'),
        (UP_SHADOW, 'shadow'),
    )

    id = models.AutoField(db_column='netboxid', primary_key=True)
    ip = models.GenericIPAddressField(unique=True)
    room = models.ForeignKey('Room', db_column='roomid')
    type = models.ForeignKey('NetboxType', db_column='typeid',
                             blank=True, null=True)
    sysname = VarcharField(unique=True, blank=True)
    category = models.ForeignKey('Category', db_column='catid')
    groups = models.ManyToManyField(
        'NetboxGroup', through='NetboxCategory', blank=True)
    groups.help_text = ''
    organization = models.ForeignKey('Organization', db_column='orgid')
    read_only = VarcharField(db_column='ro', blank=True, null=True)
    read_write = VarcharField(db_column='rw', blank=True, null=True)
    up = models.CharField(max_length=1, choices=UP_CHOICES, default=UP_UP)
    snmp_version = models.IntegerField(verbose_name="SNMP version")
    up_since = models.DateTimeField(db_column='upsince', auto_now_add=True)
    up_to_date = models.BooleanField(db_column='uptodate', default=False)
    discovered = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None)
    master = models.ForeignKey('Netbox', db_column='masterid', null=True,
                               blank=True, default=None,
                               related_name='instances')

    data = HStoreField(blank=True, null=True, default={})
    objects = models.Manager()
    ups_objects = UpsManager()

    class Meta(object):
        db_table = 'netbox'
        verbose_name = 'ip device'
        verbose_name_plural = 'ip devices'
        ordering = ('sysname',)

    def __str__(self):
        return self.get_short_sysname()

    def clean(self):
        """Custom validation"""

        # Make sure master cannot be set to self
        if self.master and self.pk == self.master.pk:
            raise ValidationError('You cannot be your own master')

        # Make sure sysname is set
        if not self.sysname:
            self.sysname = str(self.ip)

    @property
    def device(self):
        """Property to access the former device-field

        Returns the first chassis device if any
        """
        for chassis in self.get_chassis().order_by('index'):
            return chassis.device

    def is_up(self):
        """Returns True if the Netbox isn't known to be down or in shadow"""
        return self.up == self.UP_UP

    def is_snmp_down(self):
        """
        Returns True if this netbox has any unresolved snmp agent state alerts
        """
        return self.get_unresolved_alerts('snmpAgentState').count() > 0

    def get_absolute_url(self):
        kwargs = {
            'name': self.sysname,
        }
        return reverse('ipdevinfo-details-by-name', kwargs=kwargs)

    def last_updated(self, job='inventory'):
        """Returns the last updated timestamp of a particular job as a
        datetime object.

        """
        try:
            log = self.job_log.filter(success=True, job_name=job).order_by(
                '-end_time')[0]
            return log.end_time
        except IndexError:
            return None

    def get_last_jobs(self):
        """Returns the last log entry for all jobs"""
        query = """
            SELECT
              ijl.*
            FROM ipdevpoll_job_log AS ijl
            JOIN (
                SELECT
                  netboxid,
                  job_name,
                  MAX(end_time) AS end_time
                FROM
                  ipdevpoll_job_log
                GROUP BY netboxid, job_name
              ) AS foo USING (netboxid, job_name, end_time)
            JOIN netbox ON (ijl.netboxid = netbox.netboxid)
            WHERE ijl.netboxid = %s
            ORDER BY end_time
        """
        logs = IpdevpollJobLog.objects.raw(query, [self.id])
        return list(logs)

    def get_gwport_count(self):
        """Returns the number of all interfaces that have IP addresses."""
        return self.get_gwports().count()

    def get_gwports(self):
        """Returns all interfaces that have IP addresses."""
        return Interface.objects.filter(netbox=self,
                                        gwportprefix__isnull=False).distinct()

    def get_gwports_sorted(self):
        """Returns gwports naturally sorted by interface name"""

        ports = self.get_gwports().select_related('module', 'netbox')
        return Interface.sort_ports_by_ifname(ports)

    def get_swport_count(self):
        """Returns the number of all interfaces that are switch ports."""
        return self.get_swports().count()

    def get_swports(self):
        """Returns all interfaces that are switch ports."""
        return Interface.objects.filter(netbox=self,
                                        baseport__isnull=False).distinct()

    def get_swports_sorted(self):
        """Returns swports naturally sorted by interface name"""
        ports = self.get_swports().select_related('module', 'netbox')
        return Interface.sort_ports_by_ifname(ports)

    def get_physical_ports(self):
        """Return all ports that are present."""
        return Interface.objects.filter(netbox=self,
                                        ifconnectorpresent=True).distinct()

    def get_physical_ports_sorted(self):
        """Return all ports that are present sorted by interface name."""
        ports = self.get_physical_ports().select_related('module', 'netbox')
        return Interface.sort_ports_by_ifname(ports)

    def get_sensors(self):
        """ Returns sensors associated with this netbox """

        return Sensor.objects.filter(netbox=self)

    def get_availability(self):
        """Calculates and returns an availability data structure."""
        result = get_netboxes_availability([self])
        return result.get(self.pk)

    def get_week_availability(self):
        """Gets the availability for this netbox for the last week"""
        avail = self.get_availability()
        try:
            return "%.2f%%" % avail["availability"]["week"]
        except (KeyError, TypeError):
            return "N/A"

    def get_uplinks(self):
        """Returns a list of uplinks on this netbox. Requires valid vlan."""
        result = []

        for iface in self.connected_to_interface.all():
            if iface.swportvlan_set.filter(
                direction=SwPortVlan.DIRECTION_DOWN).count():
                result.append({
                    'other': iface,
                    'this': iface.to_interface,
                })

        return result

    def get_uplinks_regarding_of_vlan(self):
        result = []

        for iface in self.connected_to_interface.all():
            result.append({
                'other': iface,
                'this': iface.to_interface,
            })

        return result

    def get_function(self):
        """Returns the function description of this netbox."""
        try:
            return self.info_set.get(variable='function', key='').value
        except NetboxInfo.DoesNotExist:
            return None

    def get_prefix(self):
        """Returns the prefix address for this netbox' IP address."""
        try:
            return self.netboxprefix.prefix
        except models.ObjectDoesNotExist:
            return None

    def get_filtered_prefix(self):
        """Returns the netbox' prefix address only when the prefix is not a
        scope, private or reserved prefix.

        """
        prefix = self.get_prefix()
        if prefix and prefix.vlan.net_type.description in (
            'scope', 'private', 'reserved'):
            return None
        else:
            return prefix

    def get_short_sysname(self):
        """Returns sysname without the domain suffix if specified in the
        DOMAIN_SUFFIX setting in nav.conf"""

        if (settings.DOMAIN_SUFFIX is not None
            and self.sysname.endswith(settings.DOMAIN_SUFFIX)):
            return self.sysname[:-len(settings.DOMAIN_SUFFIX)]
        else:
            return self.sysname or self.ip

    def is_on_maintenance(self):
        """Returns True if this netbox is currently on maintenance"""
        states = self.get_unresolved_alerts('maintenanceState').filter(
            variables__variable='netbox')
        return states.count() > 0

    def last_downtime_ended(self):
        """
        Returns the end_time of the last known boxState alert.

        :returns: A datetime object if a serviceState alert was found,
                  otherwise None
        """
        try:
            lastdown = self.alerthistory_set.filter(
                event_type__id='boxState', end_time__isnull=False
            ).order_by("-end_time")[0]
        except IndexError:
            return
        else:
            return lastdown.end_time

    def get_unresolved_alerts(self, kind=None):
        """Returns a queryset of unresolved alert states"""
        return self.alerthistory_set.unresolved(kind)

    def get_powersupplies(self):
        return self.powersupplyorfan_set.filter(
            physical_class='powerSupply').order_by('name')

    def get_fans(self):
        return self.powersupplyorfan_set.filter(
            physical_class='fan').order_by('name')

    def get_system_metrics(self):
        """Gets a list of available Graphite metrics related to this Netbox,
        except for ports and sensors, which are seen as separate.

        :returns: A list of dicts describing the metrics, e.g.:
                  {id:"nav.devices.some-gw.cpu.cpu1.loadavg1min",
                   group="cpu",
                   suffix="cpu1.loadavg1min"}

        """
        ports_exclude = metric_prefix_for_ports(self.sysname)
        sensors_exclude = metric_prefix_for_sensors(self.sysname)
        base = metric_prefix_for_device(self.sysname)

        nodes = get_all_leaves_below(base, [ports_exclude, sensors_exclude])
        result = []
        for node in nodes:
            suffix = node.replace(base + '.', '')
            elements = suffix.split('.')
            group = elements[0]
            suffix = '.'.join(elements[1:])
            result.append(dict(id=node, group=group, suffix=suffix))

        return result

    def has_unignored_unrecognized_neighbors(self):
        """Returns true if this netbox has unignored unrecognized neighbors"""
        return self.unrecognizedneighbor_set.filter(
            ignored_since=None).count() > 0

    def get_chassis(self):
        """Returns a QuerySet of chassis devices seen on this netbox"""
        return self.entity_set.filter(
            device__isnull=False,
            physical_class=NetboxEntity.CLASS_CHASSIS,
        ).select_related('device')

    def get_environment_sensors(self):
        """Returns the sensors to be displayed on the Environment Sensor tab"""
        return self.sensor_set.filter(
            Q(unit_of_measurement__icontains='celsius') |
            Q(unit_of_measurement__icontains='percent'))


@python_2_unicode_compatible
class NetboxInfo(models.Model):
    """From NAV Wiki: The netboxinfo table is the place
    to store additional info on a netbox."""

    id = models.AutoField(db_column='netboxinfoid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid',
                               related_name='info_set')
    key = VarcharField()
    variable = VarcharField(db_column='var')
    value = models.TextField(db_column='val')

    class Meta(object):
        db_table = 'netboxinfo'
        unique_together = (('netbox', 'key', 'variable', 'value'),)

    def __str__(self):
        return u'%s="%s"' % (self.variable, self.value)


@python_2_unicode_compatible
class NetboxEntity(models.Model):
    """
    Represents a physical Entity within a Netbox. Largely modeled after
    ENTITY-MIB::entPhysicalTable. See RFC 4133 (and RFC 6933), but may be
    filled from other sources where applicable.

    """
    # Class choices, extracted from RFC 6933

    CLASS_OTHER = 1
    CLASS_UNKNOWN = 2
    CLASS_CHASSIS = 3
    CLASS_BACKPLANE = 4
    CLASS_CONTAINER = 5  # e.g., chassis slot or daughter-card holder
    CLASS_POWERSUPPLY = 6
    CLASS_FAN = 7
    CLASS_SENSOR = 8
    CLASS_MODULE = 9  # e.g., plug-in card or daughter-card
    CLASS_PORT = 10
    CLASS_STACK = 11  # e.g., stack of multiple chassis entities
    CLASS_CPU = 12
    CLASS_ENERGYOBJECT = 13
    CLASS_BATTERY = 14

    CLASS_CHOICES = (
        (CLASS_OTHER, 'other'),
        (CLASS_UNKNOWN, 'unknown'),
        (CLASS_CHASSIS, 'chassis'),
        (CLASS_BACKPLANE, 'backplane'),
        (CLASS_CONTAINER, 'container'),
        (CLASS_POWERSUPPLY, 'powerSupply'),
        (CLASS_FAN, 'fan'),
        (CLASS_SENSOR, 'sensor'),
        (CLASS_MODULE, 'module'),
        (CLASS_PORT, 'port'),
        (CLASS_STACK, 'stack'),
        (CLASS_CPU, 'cpu'),
        (CLASS_ENERGYOBJECT, 'energyObject'),
        (CLASS_BATTERY, 'battery'),
    )

    id = models.AutoField(db_column='netboxentityid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid',
                               related_name='entity_set')

    index = models.IntegerField()
    source = VarcharField(default='ENTITY-MIB')
    descr = VarcharField(null=True)
    vendor_type = VarcharField(null=True)
    contained_in = models.ForeignKey('NetboxEntity', null=True)
    physical_class = models.IntegerField(choices=CLASS_CHOICES, null=True)
    parent_relpos = models.IntegerField(null=True)
    name = VarcharField(null=True)
    hardware_revision = VarcharField(null=True)
    firmware_revision = VarcharField(null=True)
    software_revision = VarcharField(null=True)
    device = models.ForeignKey('Device', null=True, db_column='deviceid')
    mfg_name = VarcharField(null=True)
    model_name = VarcharField(null=True)
    alias = VarcharField(null=True)
    asset_id = VarcharField(null=True)
    fru = models.NullBooleanField(verbose_name='Is a field replaceable unit')
    mfg_date = models.DateTimeField(null=True)
    uris = VarcharField(null=True)
    gone_since = models.DateTimeField(null=True)
    data = HStoreField(default={})

    class Meta:
        db_table = 'netboxentity'
        unique_together = (('netbox', 'index'),)

    def __str__(self):
        klass = (self.get_physical_class_display() or '').capitalize()
        title = self.name or '(Unnamed entity)'
        if klass and not title.strip().lower().startswith(klass.lower()):
            title = "%s %s" % (klass, title)

        try:
            netbox = self.netbox
        except Netbox.DoesNotExist:
            netbox = '(Unknown netbox)'
        return "{title} at {netbox}".format(
            title=title, netbox=netbox
        )

    def is_chassis(self):
        """Returns True if this is a chassis type entity"""
        return self.physical_class == self.CLASS_CHASSIS

    def get_software_revision(self):
        """Returns the software revision applicable to this entity"""
        if not self.is_chassis():
            return

        if not self.software_revision:
            return self._get_applicable_software_revision()
        return self.software_revision

    def _get_applicable_software_revision(self):
        """Gets an aggregated software revision for this entity"""
        if self.netbox.type.vendor.id == 'cisco':
            return self._get_cisco_sup_software_version()

    def _get_cisco_sup_software_version(self):
        """Returns the supervisors software version

        Finds all modules in the netbox that matches supervisor patterns and has
        this entity as a parent. Returns the software version of the first one
        in that list.
        """
        supervisor_patterns = [
            re.compile(r'supervisor', re.I),
            re.compile('\bSup\b'),
            re.compile(r'WS-SUP'),
        ]

        sup_candidates = []
        modules = NetboxEntity.objects.filter(
            physical_class=NetboxEntity.CLASS_MODULE, netbox=self.netbox)

        for pattern in supervisor_patterns:
            for module in modules:
                if pattern.search(module.model_name):
                    sup_candidates.append(module)

        for sup in sup_candidates:
            parents = sup.get_parents()
            if self in parents and sup.software_revision:
                return sup.software_revision

    def get_parents(self):
        """Gets the parents of this entity

        :rtype: list<NetboxEntity>
        """
        parents = []
        if self.contained_in:
            parents.append(self.contained_in)
            parents += self.contained_in.get_parents()
        return parents


@python_2_unicode_compatible
class NetboxPrefix(models.Model):
    """Which prefix a netbox is connected to.

    This models the read-only netboxprefix view.

    """
    netbox = models.OneToOneField('Netbox', db_column='netboxid',
                                  primary_key=True)
    prefix = models.ForeignKey('Prefix', db_column='prefixid',
                               related_name='netbox_set')

    class Meta(object):
        db_table = 'netboxprefix'
        unique_together = (('netbox', 'prefix'),)

    def __str__(self):
        return u'%s at %s' % (self.netbox.sysname, self.prefix.net_address)

    def save(self, *_args, **_kwargs):
        """Does nothing, since this models a database view."""
        raise Exception("Cannot save to a view.")


@python_2_unicode_compatible
class Device(models.Model):
    """From NAV Wiki: The device table contains all physical devices in the
    network. As opposed to the netbox table, the device table focuses on the
    physical box with its serial number. The device may appear as different net
    boxes or may appear in different modules throughout its lifetime."""

    id = models.AutoField(db_column='deviceid', primary_key=True)
    serial = VarcharField(unique=True, null=True)
    hardware_version = VarcharField(db_column='hw_ver', null=True)
    firmware_version = VarcharField(db_column='fw_ver', null=True)
    software_version = VarcharField(db_column='sw_ver', null=True)
    discovered = models.DateTimeField(default=dt.datetime.now)

    class Meta(object):
        db_table = 'device'

    def __str__(self):
        return self.serial or ''


@python_2_unicode_compatible
class Module(models.Model):
    """From NAV Wiki: The module table defines modules. A module is a part of a
    netbox of category GW, SW and GSW. A module has ports; i.e router ports
    and/or switch ports. A module is also a physical device with a serial
    number."""

    UP_UP = 'y'
    UP_DOWN = 'n'
    UP_CHOICES = (
        (UP_UP, 'up'),
        (UP_DOWN, 'down'),
    )

    id = models.AutoField(db_column='moduleid', primary_key=True)
    device = models.ForeignKey('Device', db_column='deviceid')
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    module_number = models.IntegerField(db_column='module')
    name = VarcharField()
    model = VarcharField()
    description = VarcharField(db_column='descr')
    up = models.CharField(max_length=1, choices=UP_CHOICES, default=UP_UP)
    down_since = models.DateTimeField(db_column='downsince')

    class Meta(object):
        db_table = 'module'
        verbose_name = 'module'
        ordering = ('netbox', 'module_number', 'name')
        unique_together = (('netbox', 'name'),)

    def __str__(self):
        return u'{name} at {netbox}'.format(
            name=self.name or self.module_number, netbox=self.netbox)

    def get_absolute_url(self):
        kwargs = {
            'netbox_sysname': self.netbox.sysname,
            'module_name': self.name,
        }
        return reverse('ipdevinfo-module-details', kwargs=kwargs)

    def get_gwports(self):
        """Returns all interfaces that have IP addresses."""
        return Interface.objects.filter(
            module=self, gwportprefix__isnull=False).distinct()

    def get_gwports_sorted(self):
        """Returns gwports naturally sorted by interface name"""

        ports = self.get_gwports()
        return Interface.sort_ports_by_ifname(ports)

    def get_swports(self):
        """Returns all interfaces that are switch ports."""
        return Interface.objects.select_related().filter(
            module=self, baseport__isnull=False)

    def get_swports_sorted(self):
        """Returns swports naturally sorted by interface name"""

        ports = self.get_swports()
        return Interface.sort_ports_by_ifname(ports)

    def get_physical_ports(self):
        """Return all ports that are present."""
        return Interface.objects.filter(
            module=self, ifconnectorpresent=True).distinct()

    def get_physical_ports_sorted(self):
        """Return all ports that are present sorted by interface name."""
        ports = self.get_physical_ports()
        return Interface.sort_ports_by_ifname(ports)

    def is_on_maintenace(self):
        """Returns True if the owning Netbox is on maintenance"""
        return self.netbox.is_on_maintenance()

    def get_entity(self):
        """
        Attempts to find the NetboxEntity entry that corresponds to this module.

        :returns: Either a NetboxEntity object or None.
        """
        entities = NetboxEntity.objects.filter(netbox=self.netbox,
                                               device=self.device)
        if entities:
            if len(entities) > 1:
                _logger.info("Module.get_entity(): %s weirdly appears to have "
                             "duplicate entities, returning just one", self)
            return entities[0]

    def get_chassis(self):
        """
        Attempts to find the NetboxEntity that corresponds to the chassis that
        contains this module.

        :return:
        """
        me = self.get_entity()
        if not me:
            return

        entities = {e.id: e
                    for e in NetboxEntity.objects.filter(netbox=self.netbox)}
        visited = set()
        current = entities.get(me.id)
        while current is not None and not current.is_chassis():
            visited.add(current)
            current = entities.get(current.contained_in_id)
            if current in visited:
                # there's a loop here, exit now
                return
        return current


@python_2_unicode_compatible
class Memory(models.Model):
    """From NAV Wiki: The mem table describes the memory
    (memory and nvram) of a netbox."""

    id = models.AutoField(db_column='memid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    type = VarcharField(db_column='memtype')
    device = VarcharField()
    size = models.IntegerField()
    used = models.IntegerField()

    class Meta(object):
        db_table = 'mem'
        unique_together = (('netbox', 'type', 'device'),)

    def __str__(self):
        if self.used is not None and self.size is not None and self.size != 0:
            return u'%s, %d%% used' % (self.type, self.used * 100 // self.size)
        else:
            return self.type


@python_2_unicode_compatible
class Room(models.Model):
    """From NAV Wiki: The room table defines a wiring closes / network room /
    server room."""

    id = models.CharField(db_column='roomid', max_length=30, primary_key=True)
    location = models.ForeignKey('Location', db_column='locationid')
    description = VarcharField(db_column='descr', blank=True)
    position = PointField(null=True, blank=True, default=None)
    data = HStoreField(blank=True, default={})

    class Meta(object):
        db_table = 'room'
        verbose_name = 'room'
        ordering = ('id',)

    def __str__(self):
        if self.description:
            return u'%s (%s)' % (self.id, self.description)
        else:
            return u'%s' % (self.id)

    def get_absolute_url(self):
        return reverse('room-info', kwargs={'roomid': self.pk})

    @property
    def latitude(self):
        if self.position:
            return self.position[0]

    @property
    def longitude(self):
        if self.position:
            return self.position[1]


class TreeMixin(object):
    """A mixin that provides methods for models that use parenting hierarchy"""
    def num_ancestors(self):
        """The number of ancestors, how deep am I?"""
        if self.parent:
            return 1 + self.parent.num_ancestors()
        return 0

    def has_children(self):
        """Returns true if this instance has children"""
        return self.get_children().exists()

    def get_children(self):
        """Gets all children"""
        return self.__class__.objects.filter(parent=self)

    def get_descendants(self, include_self=False):
        """Gets all descendants of this instance"""
        descendants = []
        if include_self:
            descendants.append(self)
        for child in self.get_children():
            descendants.extend(child.get_descendants(include_self=True))
        return descendants


@python_2_unicode_compatible
class Location(models.Model, TreeMixin):
    """The location table defines a group of rooms; i.e. a campus."""

    id = models.CharField(db_column='locationid',
                          max_length=30, primary_key=True)
    parent = models.ForeignKey('self', db_column='parent',
                               blank=True, null=True)
    description = VarcharField(db_column='descr', blank=True)
    data = HStoreField(default={})

    class Meta(object):
        db_table = 'location'
        verbose_name = 'location'
        ordering = ['id']

    def __str__(self):
        if self.description:
            return u'{} ({})'.format(self.id, self.description)
        else:
            return u'{}'.format(self.id)

    def get_all_rooms(self):
        """Return a queryset returning all rooms in this location and
        sublocations"""
        locations = self.get_descendants(True)
        return Room.objects.filter(location__in=locations)


@python_2_unicode_compatible
class Organization(models.Model, TreeMixin):
    """From NAV Wiki: The org table defines an organization which is in charge
    of a given netbox and is the user of a given prefix."""

    id = models.CharField(db_column='orgid', max_length=30, primary_key=True)
    parent = models.ForeignKey('self', db_column='parent',
                               blank=True, null=True)
    description = VarcharField(db_column='descr', blank=True)
    contact = VarcharField(db_column='contact', blank=True)
    data = HStoreField(default={})

    class Meta(object):
        db_table = 'org'
        verbose_name = 'organization'
        ordering = ['id']

    def __str__(self):
        if self.description:
            return u'{o.id} ({o.description})'.format(o=self)
        else:
            return u'{o.id}'.format(o=self)

    def extract_emails(self):
        """Naively extract email addresses from the contact string"""
        contact = self.contact if self.contact else ""
        return re.findall(r'(\b[\w.]+@[\w.]+\b)', contact)


@python_2_unicode_compatible
class Category(models.Model):
    """From NAV Wiki: The cat table defines the categories of a netbox
    (GW,GSW,SW,EDGE,WLAN,SRV,OTHER)."""

    id = models.CharField(db_column='catid', max_length=8, primary_key=True)
    description = VarcharField(db_column='descr')
    req_snmp = models.BooleanField(default=False)

    class Meta(object):
        db_table = 'cat'
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return u'%s (%s)' % (self.id, self.description)

    def is_gw(self):
        """Is this a router?"""
        return self.id == 'GW'

    def is_gsw(self):
        """Is this a routing switch?"""
        return self.id == 'GSW'

    def is_sw(self):
        """Is this a core switch?"""
        return self.id == 'SW'

    def is_edge(self):
        """Is this an edge switch?"""
        return self.id == 'EDGE'

    def is_srv(self):
        """Is this a server?"""
        return self.id == 'SRV'

    def is_other(self):
        """Is this an uncategorized device?"""
        return self.id == 'OTHER'


@python_2_unicode_compatible
class NetboxGroup(models.Model):
    """A group that one or more netboxes belong to

    A group is a tag of sorts for grouping netboxes. You can put two netboxes
    in the same group and then use that metainfo in reports and alert profiles.

    This was formerly known as subcat but was altered to netboxgroup because
    the same subcategory could not exist on different categories.

    """

    id = VarcharField(db_column='netboxgroupid', primary_key=True)
    description = VarcharField(db_column='descr')

    class Meta(object):
        db_table = 'netboxgroup'
        ordering = ('id',)
        verbose_name = 'device group'

    def __str__(self):
        return self.id

    def get_absolute_url(self):
        return reverse('netbox-group-detail', kwargs={'groupid': self.pk})


@python_2_unicode_compatible
class NetboxCategory(models.Model):
    """Store the relation between a netbox and its groups"""

    # TODO: This should be a ManyToMany-field in Netbox, but at this time
    # Django only supports specifying the name of the M2M-table, and not the
    # column names.
    id = models.AutoField(primary_key=True)  # Serial for faking a primary key
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    category = models.ForeignKey('NetboxGroup', db_column='category')

    class Meta(object):
        db_table = 'netboxcategory'
        unique_together = (('netbox', 'category'),)  # Primary key

    def __str__(self):
        return u'%s in category %s' % (self.netbox, self.category)


@python_2_unicode_compatible
class NetboxType(models.Model):
    """From NAV Wiki: The type table defines the type of a netbox, the
    sysobjectid being the unique identifier."""

    id = models.AutoField(db_column='typeid', primary_key=True)
    vendor = models.ForeignKey('Vendor', db_column='vendorid')
    name = VarcharField(db_column='typename', verbose_name="type name")
    sysobjectid = VarcharField(unique=True)
    description = VarcharField(db_column='descr')

    class Meta(object):
        db_table = 'type'
        unique_together = (('vendor', 'name'),)

    def __str__(self):
        return u'%s (%s from %s)' % (self.name, self.description, self.vendor)

    def get_enterprise_id(self):
        """Returns the type's enterprise ID as an integer.

        The type's sysobjectid should always start with
        SNMPv2-SMI::enterprises (1.3.6.1.4.1).  The next OID element will be
        an enterprise ID, while the remaining elements will describe the type
        specific to the vendor.

        """
        prefix = u"1.3.6.1.4.1."
        if self.sysobjectid.startswith(prefix):
            specific = self.sysobjectid[len(prefix):]
            enterprise = specific.split('.')[0]
            return int(enterprise)

#######################################################################
### Device management


@python_2_unicode_compatible
class Vendor(models.Model):
    """From NAV Wiki: The vendor table defines vendors. A
    type is of a vendor. A product is of a vendor."""

    id = models.CharField(db_column='vendorid', max_length=15,
                          primary_key=True)

    class Meta(object):
        db_table = 'vendor'
        ordering = ('id', )

    def __str__(self):
        return self.id

#######################################################################
### Router/topology


@python_2_unicode_compatible
class GwPortPrefix(models.Model):
    """Defines IP addresses assigned to Interfaces, with a relation to the
    associated Prefix.

    """
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    prefix = models.ForeignKey('Prefix', db_column='prefixid')
    gw_ip = CIDRField(db_column='gwip', primary_key=True)
    virtual = models.BooleanField(default=False)

    class Meta(object):
        db_table = 'gwportprefix'

    def __str__(self):
        return self.gw_ip


class PrefixManager(models.Manager):
    def contains_ip(self, ipaddr):
        """Gets all prefixes that contain the given IP address,
        ordered by descending network mask length.

        """
        return self.get_queryset().exclude(
            vlan__net_type="loopback"
        ).extra(
            select={'mlen': 'masklen(netaddr)'},
            where=["%s <<= netaddr"],
            params=[ipaddr],
            order_by=["-mlen"]
        ).select_related('vlan')

    def within(self, scope):
        """Gets all prefixes that are within this scope"""
        return self.get_queryset().extra(
            where=["%s >> netaddr"],
            params=[scope]
        ).select_related('vlan')

    def private(self):
        """Gets all the prefixes that is a private network"""
        return self.get_queryset().extra(
            where=["netaddr <<= %s or netaddr <<= %s or netaddr <<= %s"],
            params=['172.16.0.0/12', '10.0.0.0/8', '192.168.0.0/16']
        ).select_related('vlan')


@python_2_unicode_compatible
class Prefix(models.Model):
    """From NAV Wiki: The prefix table stores IP prefixes."""

    objects = PrefixManager()

    id = models.AutoField(db_column='prefixid', primary_key=True)
    net_address = CIDRField(db_column='netaddr', unique=True)
    vlan = models.ForeignKey('Vlan', db_column='vlanid')
    usages = models.ManyToManyField('Usage', through='PrefixUsage',
                                    through_fields=('prefix', 'usage'))

    class Meta(object):
        db_table = 'prefix'

    def __str__(self):
        if self.vlan:
            return u'%s (vlan %s)' % (self.net_address, self.vlan)
        else:
            return self.net_address

    def get_prefix_length(self):
        """Returns the prefix mask length."""
        ip = IPy.IP(self.net_address)
        return ip.prefixlen()

    def get_prefix_size(self):
        ip = IPy.IP(self.net_address)
        return ip.len()

    def get_router_ports(self):
        """Returns a ordered list of GwPortPrefix objects on this prefix"""
        return self.gwportprefix_set.filter(
            interface__netbox__category__id__in=('GSW', 'GW')
        ).select_related(
            'interface', 'interface__netbox'
        ).order_by('-virtual', 'gw_ip')

    def get_graph_url(self):
        """Creates the graph url used for graphing this prefix"""
        path = partial(metric_path_for_prefix, self.net_address)
        ip_count = 'alias({0}, "IP addresses ")'.format(path('ip_count'))
        ip_range = 'alias({0}, "Max addresses")'.format(path('ip_range'))
        mac_count = 'alias({0}, "MAC addresses")'.format(path('mac_count'))
        metrics = [ip_count, mac_count]
        if IPy.IP(self.net_address).version() == 4:
            metrics.append(ip_range)
        return get_simple_graph_url(metrics, title=str(self), format='json')

    def get_absolute_url(self):
        return reverse('prefix-details', args=[self.pk])


@python_2_unicode_compatible
class Vlan(models.Model):
    """From NAV Wiki: The vlan table defines the IP broadcast domain / vlan. A
    broadcast domain often has a vlan value, it may consist of many IP
    prefixes, it is of a network type, it is used by an organization (org) and
    has a user group (usage) within the org."""

    id = models.AutoField(db_column='vlanid', primary_key=True)
    vlan = models.IntegerField(null=True, blank=True)
    net_type = models.ForeignKey('NetType', db_column='nettype')
    organization = models.ForeignKey('Organization', db_column='orgid',
                                     null=True, blank=True)
    usage = models.ForeignKey('Usage', db_column='usageid',
                              null=True, blank=True)
    net_ident = VarcharField(db_column='netident', null=True, blank=True)
    description = VarcharField(null=True, blank=True)
    netbox = models.ForeignKey('NetBox', db_column='netboxid',
                               on_delete=models.SET_NULL,
                               null=True, blank=True)

    class Meta(object):
        db_table = 'vlan'

    def __str__(self):
        result = u''
        if self.vlan:
            result += u'%d' % self.vlan
        else:
            result += u'N/A'
        if self.net_ident:
            result += ' (%s)' % self.net_ident
        return result

    def has_meaningful_net_ident(self):
        if not self.net_ident:
            return False
        if self.net_ident.upper() == "VLAN{}".format(self.vlan):
            return False
        return True

    def get_graph_urls(self):
        """Fetches the graph urls for graphing this vlan"""
        return [url for url in [self.get_graph_url(f) for f in [4, 6]] if url]

    def get_graph_url(self, family=4):
        """Creates a graph url for the given family with all prefixes stacked"""
        assert family in [4, 6]
        prefixes = self.prefix_set.extra(where=["family(netaddr)=%s" % family])
        # Put metainformation in the alias so that Rickshaw can pick it up and
        # know how to draw the series.
        series = ["alias({}, 'renderer=area;;{}')".format(
            metric_path_for_prefix(prefix.net_address, 'ip_count'),
            prefix.net_address) for prefix in prefixes]
        if series:
            if family == 4:
                series.append(
                    "alias(sumSeries(%s), 'Max addresses')" % ",".join([
                        metric_path_for_prefix(prefix.net_address, 'ip_range')
                        for prefix in prefixes
                    ])
                )
            return get_simple_graph_url(
                series,
                title="Total IPv{} addresses on vlan {} - stacked".format(
                    family, str(self)),
                format='json')


@python_2_unicode_compatible
class NetType(models.Model):
    """From NAV Wiki: The nettype table defines network type;lan, core, link,
    elink, loopback, closed, static, reserved, scope. The network types are
    predefined in NAV and may not be altered."""

    id = VarcharField(db_column='nettypeid', primary_key=True)
    description = VarcharField(db_column='descr')
    edit = models.BooleanField(default=False)

    class Meta(object):
        db_table = 'nettype'

    def __str__(self):
        return self.id


@python_2_unicode_compatible
class PrefixUsage(models.Model):
    """Combines prefixes and usages for tagging of prefixes"""
    id = models.AutoField(db_column='prefix_usage_id', primary_key=True)
    prefix = models.ForeignKey('Prefix', db_column='prefixid')
    usage = models.ForeignKey('Usage', db_column='usageid')

    class Meta(object):
        db_table = 'prefix_usage'

    def __str__(self):
        return u"{}:{}".format(self.prefix.net_address, self.usage.id)


@python_2_unicode_compatible
class Usage(models.Model):
    """From NAV Wiki: The usage table defines the user group (student, staff
    etc). Usage categories are maintained in the edit database tool."""

    id = models.CharField(db_column='usageid', max_length=30, primary_key=True)
    description = VarcharField(db_column='descr')

    class Meta(object):
        db_table = 'usage'
        verbose_name = 'usage'
        ordering = ['id']

    def __str__(self):
        return u'%s (%s)' % (self.id, self.description)


@python_2_unicode_compatible
class Arp(models.Model):
    """From NAV Wiki: The arp table contains (ip, mac, time
    start, time end)."""

    id = models.AutoField(db_column='arpid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid', null=True)
    prefix = models.ForeignKey('Prefix', db_column='prefixid', null=True)
    sysname = VarcharField()
    ip = models.GenericIPAddressField()
    # TODO: Create MACAddressField in Django
    mac = models.CharField(max_length=17)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = DateTimeInfinityField()

    class Meta(object):
        db_table = 'arp'

    def __str__(self):
        return u'%s to %s' % (self.ip, self.mac)

#######################################################################
### Switch/topology


@python_2_unicode_compatible
class SwPortVlan(models.Model):
    """From NAV Wiki: The swportvlan table defines the
    vlan values on all switch ports. dot1q trunk ports
    typically have several rows in this table."""

    DIRECTION_UNDEFINED = 'x'
    DIRECTION_UP = 'o'
    DIRECTION_DOWN = 'n'
    DIRECTION_BLOCKED = 'b'
    DIRECTION_CHOICES = (
        (DIRECTION_UNDEFINED, 'undefined'),
        (DIRECTION_UP, 'up'),
        (DIRECTION_DOWN, 'down'),
        (DIRECTION_BLOCKED, 'blocked'),
    )

    id = models.AutoField(db_column='swportvlanid', primary_key=True)
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    vlan = models.ForeignKey('Vlan', db_column='vlanid')
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES,
                                 default=DIRECTION_UNDEFINED)

    class Meta(object):
        db_table = 'swportvlan'
        unique_together = (('interface', 'vlan'),)

    def __str__(self):
        return u'%s, on vlan %s' % (self.interface, self.vlan)


@python_2_unicode_compatible
class SwPortAllowedVlan(models.Model):
    """Stores a hexstring that encodes the list of VLANs that are allowed to
    traverse a trunk port.

    """
    interface = models.OneToOneField('Interface', db_column='interfaceid',
                                     primary_key=True)
    hex_string = VarcharField(db_column='hexstring')
    _cached_hex_string = ''
    _cached_vlan_set = None

    class Meta(object):
        db_table = 'swportallowedvlan'

    def __contains__(self, item):
        vlans = self.get_allowed_vlans()
        return item in vlans

    def get_allowed_vlans(self):
        """Converts the plaintext formatted hex_string attribute to a list of
        VLAN numbers.

        :returns: A set of integers.
        """
        if self._cached_hex_string != self.hex_string:
            self._cached_hex_string = self.hex_string
            self._cached_vlan_set = self._calculate_allowed_vlans()

        return self._cached_vlan_set or set()

    @staticmethod
    def vlan_list_to_hex(vlans):
        """Convert a list of VLAN numbers to a hexadecimal string."""
        # Make sure there are at least 256 digits (128 octets) in the
        # resulting hex string.  This is necessary for parts of NAV to
        # parse the hexstring correctly.
        max_vlan = max(vlans)
        needed_octets = int(math.ceil((max_vlan+1) / 8.0))
        bits = BitVector(b'\x00' * max(needed_octets, 128))
        for vlan in vlans:
            bits[vlan] = True
        return bits.to_hex()

    def set_allowed_vlans(self, vlans):
        self.hex_string = self.vlan_list_to_hex(vlans)

    def _calculate_allowed_vlans(self):
        bits = BitVector(bytes.fromhex(self.hex_string))
        return set(bits.get_set_bits())

    def __str__(self):
        return u'Allowed vlans for swport %s' % self.interface


@python_2_unicode_compatible
class SwPortBlocked(models.Model):
    """This table defines the spanning tree blocked ports for a given vlan for
    a given switch port."""

    id = models.AutoField(db_column='swportblockedid', primary_key=True)
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    vlan = models.IntegerField()

    class Meta(object):
        db_table = 'swportblocked'
        unique_together = (('interface', 'vlan'),)  # Primary key

    def __str__(self):
        return '%d, at %s' % (self.vlan, self.interface)


@python_2_unicode_compatible
class AdjacencyCandidate(models.Model):
    """A candidate for netbox/interface adjacency.

    Used in the process of building the physical topology of the
    network. AdjacencyCandidate defines a candidate for next hop physical
    neighbor.

    """
    id = models.AutoField(db_column='adjacency_candidateid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    to_netbox = models.ForeignKey('Netbox', db_column='to_netboxid',
                                  related_name='to_adjacencycandidate_set')
    to_interface = models.ForeignKey('Interface', db_column='to_interfaceid',
                                     null=True,
                                     related_name='to_adjacencycandidate_set')
    source = VarcharField()
    miss_count = models.IntegerField(db_column='misscnt', default=0)

    class Meta(object):
        db_table = 'adjacency_candidate'
        unique_together = (('netbox', 'interface', 'to_netbox', 'to_interface', 'source'),)

    def __str__(self):
        return u'%s:%s %s candidate %s:%s' % (self.netbox, self.interface,
                                              self.source,
                                              self.to_netbox,
                                              self.to_interface)


@python_2_unicode_compatible
class NetboxVtpVlan(models.Model):
    """From NAV Wiki: A help table that contains the vtp vlan database of a
    switch. For certain cisco switches cam information is gathered using a
    community@vlan string. It is then necessary to know all vlans that are
    active on a switch. The vtp vlan table is an extra source of
    information."""

    id = models.AutoField(primary_key=True)  # Serial for faking a primary key
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    vtp_vlan = models.IntegerField(db_column='vtpvlan')

    class Meta(object):
        db_table = 'netbox_vtpvlan'
        unique_together = (('netbox', 'vtp_vlan'),)

    def __str__(self):
        return u'%d, at %s' % (self.vtp_vlan, self.netbox)


@python_2_unicode_compatible
class Cam(models.Model):
    """From NAV Wiki: The cam table defines (swport, mac, time start, time
    end)"""

    id = models.AutoField(db_column='camid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid', null=True)
    sysname = VarcharField()
    ifindex = models.IntegerField()
    module = models.CharField(max_length=4)
    port = VarcharField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = DateTimeInfinityField()
    miss_count = models.IntegerField(db_column='misscnt', default=0)
    # TODO: Create MACAddressField in Django
    mac = models.CharField(max_length=17)

    class Meta(object):
        db_table = 'cam'
        unique_together = (('netbox', 'sysname', 'module', 'port',
                            'mac', 'start_time'),)

    def __str__(self):
        return u'%s, %s' % (self.mac, self.netbox)


#######################################################################
### Interfaces and related attributes

@python_2_unicode_compatible
class Interface(models.Model):
    """The network interfaces, both physical and virtual, of a Netbox."""

    OPER_UP = 1
    OPER_DOWN = 2
    OPER_TESTING = 3
    OPER_UNKNOWN = 4
    OPER_DORMANT = 5
    OPER_NOTPRESENT = 6
    OPER_LOWERLAYERDOWN = 7

    OPER_STATUS_CHOICES = (
        (OPER_UP, 'up'),
        (OPER_DOWN, 'down'),
        (OPER_TESTING, 'testing'),
        (OPER_UNKNOWN, 'unknown'),
        (OPER_DORMANT, 'dormant'),
        (OPER_NOTPRESENT, 'not present'),
        (OPER_LOWERLAYERDOWN, 'lower layer down'),
    )

    ADM_UP = 1
    ADM_DOWN = 2
    ADM_TESTING = 3

    ADM_STATUS_CHOICES = (
        (ADM_UP, 'up'),
        (ADM_DOWN, 'down'),
        (ADM_TESTING, 'testing'),
    )

    DUPLEX_FULL = 'f'
    DUPLEX_HALF = 'h'
    DUPLEX_CHOICES = (
        (DUPLEX_FULL, 'full duplex'),
        (DUPLEX_HALF, 'half duplex'),
    )

    id = models.AutoField(db_column='interfaceid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    module = models.ForeignKey('Module', db_column='moduleid', null=True)
    ifindex = models.IntegerField()
    ifname = VarcharField()
    ifdescr = VarcharField()
    iftype = models.IntegerField()
    speed = models.FloatField()
    ifphysaddress = models.CharField(max_length=17, null=True)
    ifadminstatus = models.IntegerField(choices=ADM_STATUS_CHOICES)
    ifoperstatus = models.IntegerField(choices=OPER_STATUS_CHOICES)
    iflastchange = models.IntegerField()
    ifconnectorpresent = models.BooleanField(default=False)
    ifpromiscuousmode = models.BooleanField(default=False)
    ifalias = VarcharField()

    baseport = models.IntegerField()
    media = VarcharField(null=True)
    vlan = models.IntegerField()
    trunk = models.BooleanField(default=False)
    duplex = models.CharField(max_length=1, choices=DUPLEX_CHOICES, null=True)

    to_netbox = models.ForeignKey('Netbox', db_column='to_netboxid', null=True,
                                  related_name='connected_to_interface')
    to_interface = models.ForeignKey('self', db_column='to_interfaceid',
                                     null=True,
                                     related_name='connected_to_interface')

    gone_since = models.DateTimeField()

    class Meta(object):
        db_table = u'interface'
        ordering = ('baseport', 'ifname')

    def __init__(self, *args, **kwargs):
        super(Interface, self).__init__(*args, **kwargs)
        # Create cache dictionary
        # FIXME: Replace with real Django caching
        self.time_since_activity_cache = {}

    def __str__(self):
        return u'{ifname} at {netbox}'.format(
            ifname=self.ifname, netbox=self.netbox)

    @property
    def audit_logname(self):
        template = u'{netbox}:{ifname}'
        return template.format(ifname=self.ifname,
                               netbox=self.netbox.get_short_sysname())

    @classmethod
    def sort_ports_by_ifname(cls, ports):
        return sorted(ports, key=lambda p: nav.natsort.split(p.ifname))

    def get_absolute_url(self):
        kwargs = {
            'netbox_sysname': self.netbox.sysname,
            'port_id': self.id,
        }
        return reverse('ipdevinfo-interface-details', kwargs=kwargs)

    def get_vlan_numbers(self):
        """List of VLAN numbers related to the port"""

        # XXX: This causes a DB query per port
        vlans = [swpv.vlan.vlan
            for swpv in self.swportvlan_set.select_related('vlan', 'interface')]
        if self.vlan is not None and self.vlan not in vlans:
            vlans.append(self.vlan)
        vlans.sort()
        return vlans

    def get_allowed_vlan_ranges(self):
        """Returns the set of allowed vlans as a list of ranges

        :rtype: nav.util.NumberRange
        """
        try:
            allowed = self.swportallowedvlan.get_allowed_vlans()
        except SwPortAllowedVlan.DoesNotExist:
            pass
        else:
            return util.NumberRange(allowed)

    def get_last_cam_record(self):
        """Returns the newest cam record gotten from this switch port."""
        try:
            return self.netbox.cam_set.filter(
                ifindex=self.ifindex
            ).latest('end_time')
        except Cam.DoesNotExist:
            return None

    def get_active_time(self, interval=600):
        """
        Time since last CAM activity on port, looking at CAM entries
        for the last ``interval'' days.

        Returns None if no activity is found, else number of days since last
        activity as a datetime.timedelta object.
        """

        # Check cache for result
        if interval in self.time_since_activity_cache:
            return self.time_since_activity_cache[interval]

        min_time = dt.datetime.now() - dt.timedelta(days=interval)
        try:
            # XXX: This causes a DB query per port
            # Use .values() to avoid creating additional objects we do not need
            last_cam_entry_end_time = self.netbox.cam_set.filter(
                ifindex=self.ifindex, end_time__gt=min_time).order_by(
                '-end_time').values('end_time')[0]['end_time']
        except (Cam.DoesNotExist, IndexError):
            # Inactive/not in use
            return None

        if last_cam_entry_end_time == dt.datetime.max:
            # Active now
            self.time_since_activity_cache[interval] = dt.timedelta(days=0)
        else:
            # Active some time inside the given interval
            self.time_since_activity_cache[interval] = \
                dt.datetime.now() - last_cam_entry_end_time

        return self.time_since_activity_cache[interval]

    def get_port_metrics(self):
        """Gets a list of available Graphite metrics related to this Interface.

        :returns: A list of dicts describing the metrics, e.g.:
                  {id:"nav.devices.some-gw.ports.gi1_1.ifInOctets",
                   suffix:"ifInOctets"}

        """
        base = metric_prefix_for_interface(self.netbox, self.ifname)

        nodes = get_all_leaves_below(base)
        result = [dict(id=n,
                       suffix=n.replace(base + '.', ''),
                       url=get_simple_graph_url(n, '1day'))
                  for n in nodes]
        return result

    def get_link_display(self):
        """Returns a display value for this interface's link status."""
        if self.ifoperstatus == self.OPER_UP:
            return "Active"
        elif self.ifadminstatus == self.ADM_DOWN:
            return "Disabled"
        return "Inactive"

    def get_trunkvlans_as_range(self):
        """
        Converts the list of allowed vlans on trunk to a string of ranges.
        Ex: [1, 2, 3, 4, 7, 8, 10] -> "1-4,7-8,10"
        """
        def as_range(iterable):
            l = list(iterable)
            if len(l) > 1:
                return '{0}-{1}'.format(l[0], l[-1])
            else:
                return '{0}'.format(l[0])

        if self.trunk:
            return ",".join(as_range(y) for x, y in groupby(
                sorted(self.swportallowedvlan.get_allowed_vlans()),
                lambda n, c=count(): n - next(c))
            )
        else:
            return ""

    def is_swport(self):
        """Returns True if the interface is configured as a switch-port"""
        return (self.baseport is not None)

    def is_gwport(self):
        """Returns True if the interface has an IP address.

        NOTE: This doesn't necessarily mean the port forwards packets for
        other hosts.

        """
        return (self.gwportprefix_set.count() > 0)

    def is_physical_port(self):
        """Returns true if this interface has a physical connector present"""
        return self.ifconnectorpresent

    def is_admin_up(self):
        """Returns True if interface is administratively up"""
        return self.ifadminstatus == self.ADM_UP

    def is_oper_up(self):
        """Returns True if interface is operationally up"""
        return self.ifoperstatus == self.OPER_UP

    def below_me(self):
        """Returns interfaces stacked with this one on a layer below"""
        return Interface.objects.filter(lower_layer__higher=self)

    def above_me(self):
        """Returns interfaces stacked with this one on a layer above"""
        return Interface.objects.filter(higher_layer__lower=self)

    def get_aggregator(self):
        """Returns the interface that is selected as an aggregator for me.

        Naively selects the aggregator with the lowest ifIndex in cases where
        there are multiple aggregators (may happen on e.g. Juniper devices,
        due to stacking of logical units)
        """
        return Interface.objects.filter(
            aggregators__interface=self).order_by('ifindex').first()

    def get_bundled_interfaces(self):
        """Returns the interfaces that are bundled on this interface"""
        return Interface.objects.filter(bundled__aggregator=self)

    def is_degraded(self):
        """
        Returns True if this aggregator has been degraded, False if it has
        not, None if this interface is not a known aggregator.
        """
        aggregates = self.get_bundled_interfaces()
        if aggregates:
            return any(not agg.is_oper_up() for agg in aggregates)

    def get_sorted_vlans(self):
        """Returns a queryset of sorted swportvlans"""
        return self.swportvlan_set.select_related('vlan').order_by(
            'vlan__vlan')

    def is_on_maintenace(self):
        """Returns True if the owning Netbox is on maintenance"""
        return self.netbox.is_on_maintenance()

    def has_unignored_unrecognized_neighbors(self):
        """Returns True if this interface has unrecognized neighbors that are
        not ignored
        """
        return self.unrecognizedneighbor_set.filter(
            ignored_since__isnull=True).count() > 0


class InterfaceStack(models.Model):
    """Interface layered stacking relationships"""
    higher = models.ForeignKey(Interface, db_column='higher',
                               related_name='higher_layer')
    lower = models.ForeignKey(Interface, db_column='lower',
                              related_name='lower_layer')

    class Meta(object):
        db_table = u'interface_stack'


class InterfaceAggregate(models.Model):
    """Interface aggregation relationships"""
    aggregator = models.ForeignKey(Interface, db_column='aggregator',
                                   related_name='aggregators')
    interface = models.ForeignKey(Interface, db_column='interface',
                                  related_name='bundled')

    class Meta(object):
        db_table = u'interface_aggregate'


class IanaIftype(models.Model):
    """IANA-registered iftype values"""
    iftype = models.IntegerField(primary_key=True)
    name = VarcharField()
    descr = VarcharField()

    class Meta(object):
        db_table = u'iana_iftype'


class RoutingProtocolAttribute(models.Model):
    """Routing protocol metric as configured on a routing interface"""
    id = models.IntegerField(primary_key=True)
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    name = VarcharField(db_column='protoname')
    metric = models.IntegerField()

    class Meta(object):
        db_table = u'rproto_attr'


class GatewayPeerSession(models.Model):
    """Gateway protocol session decriptor"""
    PROTOCOL_BGP = 1
    PROTOCOL_OSPF = 2
    PROTOCOL_ISIS = 3

    PROTOCOL_CHOICES = (
        (PROTOCOL_BGP, 'BGP'),
        (PROTOCOL_OSPF, 'OSPF'),
        (PROTOCOL_ISIS, 'IS-IS'),
    )

    id = models.AutoField(primary_key=True, db_column='peersessionid')
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    protocol = models.IntegerField(choices=PROTOCOL_CHOICES)
    peer = models.GenericIPAddressField()
    state = VarcharField()
    local_as = models.IntegerField(null=True)
    remote_as = models.IntegerField(null=True)
    adminstatus = VarcharField()

    class Meta(object):
        db_table = u'peersession'

    def get_peer_as_netbox(self):
        """If the peer of this partner is a known Netbox, it is returned.

        :rtype: Netbox

        """
        expr = Q(ip=self.peer) | Q(interface__gwportprefix__gw_ip=self.peer)
        netboxes = Netbox.objects.filter(expr)
        if netboxes:
            return netboxes[0]

    def get_peer_display(self):
        """Returns a display name for the peer.

        Will access the database to see if the peer is a known Netbox.

        """
        peer = self.get_peer_as_netbox()
        return "{} ({})".format(peer, self.peer) if peer else str(self.peer)

    def __repr__(self):
        return ("<GatewayPeerSession: protocol={protocol} netbox={netbox}"
                " peer={peer} state={state} adminstatus={adminstatus}>").format(
            protocol=self.get_protocol_display(),
            netbox=self.netbox,
            peer=self.peer,
            state=self.state,
            adminstatus=self.adminstatus)

    def __str__(self):
        tmpl = "{netbox} {proto} session with {peer}"
        return tmpl.format(netbox=self.netbox,
                           proto=self.get_protocol_display(),
                           peer=self.get_peer_display())


@python_2_unicode_compatible
class Sensor(models.Model):
    """
    This table contains meta-data about available sensors in
    network equipment.

    Information from this table is used to poll metrics and display graphs for
    sensor data.
    """

    UNIT_OTHER = 'other'         # Other than those listed
    UNIT_UNKNOWN = 'unknown'     # unknown measurement, or arbitrary,
                                 # relative numbers
    UNIT_VOLTS_AC = 'voltsAC'    # electric potential
    UNIT_VOLTS_DC = 'voltsDC'    # electric potential
    UNIT_AMPERES = 'amperes'     # electric current
    UNIT_WATTS = 'watts'         # power
    UNIT_DBM = 'dBm'             # power (optics)
    UNIT_HERTZ = 'hertz'         # frequency
    UNIT_CELSIUS = 'celsius'     # temperature
    UNIT_FAHRENHEIT = 'fahrenheit'  # temperature
    UNIT_PERCENT_RELATIVE_HUMIDITY = 'percentRH'  # percent relative humidity
    UNIT_RPM = 'rpm'             # shaft revolutions per minute
    UNIT_CMM = 'cmm'             # cubic meters per minute (airflow)
    UNIT_LPM = 'l/min'           # liters per minute (waterflow)
    UNIT_TRUTHVALUE = 'boolean'  # value takes { true(1), false(2) }
    UNIT_VOLTAMPERES = 'voltsamperes'  # apparent power
    UNIT_VAR = 'var'             # Volt-ampere reactive
    UNIT_WATTHOURS = 'watthours'  # electric energy consumed
    UNIT_VOLTAMPEREHOURS = 'voltamperehours'  # apperant consumed energy
    UNIT_PERCENT = '%'           # relative values
    UNIT_MPS = 'm/s'             # speed
    UNIT_PASCAL = 'pascal'       # pressure
    UNIT_PSI = 'psi'             # pressure
    UNIT_BAR = 'bar'             # pressure
    UNIT_GRAMS = 'grams'         # weight
    UNIT_FEET = 'feet'           # distance
    UNIT_INCHES = 'inches'       # distance
    UNIT_METERS = 'meters'       # distance
    UNIT_DEGREES = 'degrees'     # angle
    UNIT_LUX = 'lux'             # illuminance
    UNIT_GPCM = 'grams/m3'       # gass density?
    UNIT_SECONDS = 'seconds'     # time
    UNIT_MINUTES = 'minutes'     # time

    UNIT_OF_MEASUREMENTS_CHOICES = (
        (UNIT_OTHER, 'Other'),
        (UNIT_UNKNOWN, 'Unknown'),
        (UNIT_VOLTS_AC, 'VoltsAC'),
        (UNIT_VOLTS_DC, 'VoltsDC'),
        (UNIT_AMPERES, 'Amperes'),
        (UNIT_WATTS, 'Watts'),
        (UNIT_DBM, 'dBm'),
        (UNIT_HERTZ, 'Hertz'),
        (UNIT_CELSIUS, 'Celsius'),
        (UNIT_FAHRENHEIT, 'Fahrenheit'),
        (UNIT_PERCENT_RELATIVE_HUMIDITY, 'Relative humidity'),
        (UNIT_RPM, 'Revolutions per minute'),
        (UNIT_CMM, 'Cubic meters per minute'),
        (UNIT_LPM, 'Liters per minute'),
        (UNIT_TRUTHVALUE, 'Boolean'),
        (UNIT_VOLTAMPERES, 'Volt-ampere'),
        (UNIT_VAR, 'Volt-ampere reactive'),
        (UNIT_VOLTAMPEREHOURS, 'Volt-ampere hours'),
        (UNIT_WATTHOURS, 'Watt hours'),
        (UNIT_PERCENT, '%'),
        (UNIT_MPS, 'meters per second'),
        (UNIT_PASCAL, 'pascal'),
        (UNIT_PSI, 'psi'),
        (UNIT_BAR, 'bar'),
        (UNIT_GRAMS, 'gram'),
        (UNIT_FEET, 'Feet'),
        (UNIT_INCHES, 'Inches'),
        (UNIT_METERS, 'Meters'),
        (UNIT_DEGREES, 'Degrees'),
        (UNIT_LUX, 'Lux'),
        (UNIT_GPCM, 'Grams per cubic meter'),
        (UNIT_SECONDS, 'Seconds'),
        (UNIT_MINUTES, 'Minutes'),
    )

    SCALE_YOCTO = 'yocto'  # 10^-24
    SCALE_ZEPTO = 'zepto'  # 10^-21
    SCALE_ATTO = 'atto'    # 10^-18
    SCALE_FEMTO = 'femto'  # 10^-15
    SCALE_PICO = 'pico'    # 10^-12
    SCALE_NANO = 'nano'    # 10^-9
    SCALE_MICRO = 'micro'  # 10^-6
    SCALE_MILLI = 'milli'  # 10^-3
    SCALE_UNITS = 'units'  # 10^0
    SCALE_KILO = 'kilo'    # 10^3
    SCALE_MEGA = 'mega'    # 10^6
    SCALE_GIGA = 'giga'    # 10^9
    SCALE_TERA = 'tera'    # 10^12
    SCALE_EXA = 'exa'      # 10^15
    SCALE_PETA = 'peta'    # 10^18
    SCALE_ZETTA = 'zetta'  # 10^21
    SCALE_YOTTA = 'yotta'  # 10^24

    DATA_SCALE_CHOICES = (
        (SCALE_YOCTO, 'Yocto'),
        (SCALE_ZEPTO, 'Zepto'),
        (SCALE_ATTO, 'Atto'),
        (SCALE_FEMTO, 'Femto'),
        (SCALE_PICO, 'Pico'),
        (SCALE_NANO, 'Nano'),
        (SCALE_MICRO, 'Micro'),
        (SCALE_MILLI, 'Milli'),
        (SCALE_UNITS, 'No unit scaling'),
        (SCALE_KILO, 'Kilo'),
        (SCALE_MEGA, 'Mega'),
        (SCALE_GIGA, 'Giga'),
        (SCALE_TERA, 'Tera'),
        (SCALE_EXA, 'Exa'),
        (SCALE_PETA, 'Peta'),
        (SCALE_ZETTA, 'Zetta'),
        (SCALE_YOTTA, 'Yotta'),
    )

    id = models.AutoField(db_column='sensorid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    interface = models.ForeignKey(Interface, db_column='interfaceid', null=True)
    oid = VarcharField(db_column="oid")
    unit_of_measurement = VarcharField(db_column="unit_of_measurement",
                                       choices=UNIT_OF_MEASUREMENTS_CHOICES)
    data_scale = VarcharField(db_column="data_scale",
                              choices=DATA_SCALE_CHOICES)
    precision = models.IntegerField(db_column="precision")
    human_readable = VarcharField(db_column="human_readable")
    name = VarcharField(db_column="name")
    internal_name = VarcharField(db_column="internal_name")
    mib = VarcharField(db_column="mib")
    display_minimum_user = models.FloatField(db_column="display_minimum_user",
                                             null=True)
    display_maximum_user = models.FloatField(db_column="display_maximum_user",
                                             null=True)
    display_minimum_sys = models.FloatField(db_column="display_minimum_sys",
                                            null=True)
    display_maximum_sys = models.FloatField(db_column="display_maximum_sys",
                                            null=True)

    class Meta(object):
        db_table = 'sensor'
        ordering = ('name',)

    def __str__(self):
        return u"Sensor '{}' on {}".format(
            self.human_readable or self.internal_name,
            self.netbox)

    def get_absolute_url(self):
        return reverse('sensor-details', kwargs={'identifier': self.pk})

    def get_metric_name(self):
        return metric_path_for_sensor(self.netbox.sysname, self.internal_name)

    def get_graph_url(self, time_frame='1day'):
        return get_simple_graph_url([self.get_metric_name()],
                                    time_frame=time_frame)

    def get_display_range(self):
        minimum = 0
        if self.display_minimum_user is not None:
            minimum = self.display_minimum_user
        elif self.display_minimum_sys is not None:
            minimum = self.display_minimum_sys

        maximum = 100
        if self.display_maximum_user is not None:
            maximum = self.display_maximum_user
        elif self.display_maximum_sys is not None:
            maximum = self.display_maximum_sys
        elif self.unit_of_measurement == self.UNIT_CELSIUS:
            maximum = 50

        return [minimum, maximum]

    @property
    def normalized_unit(self):
        """Try to normalize the unit

        The unit_of_measurement is the value reported by the device, and is
        all sorts of stuff like percentRH, Celcius. Here we try to normalize
        those units (in a very basic way).
        """
        units = ['celsius', 'percent']
        for unit in units:
            if unit in self.unit_of_measurement.lower():
                return unit
        return self.unit_of_measurement


@python_2_unicode_compatible
class PowerSupplyOrFan(models.Model):
    STATE_UP = u'y'
    STATE_DOWN = u'n'
    STATE_UNKNOWN = u'u'
    STATE_WARNING = u'w'

    STATE_CHOICES = (
        (STATE_UP, "Up"),
        (STATE_DOWN, "Down"),
        (STATE_UNKNOWN, "Unknown"),
        (STATE_WARNING, "Warning"),
    )

    id = models.AutoField(db_column='powersupplyid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    device = models.ForeignKey(Device, db_column='deviceid')
    name = VarcharField(db_column='name')
    model = VarcharField(db_column='model', null=True)
    descr = VarcharField(db_column='descr', null=True)
    downsince = models.DateTimeField(db_column='downsince', null=True)
    physical_class = VarcharField(db_column='physical_class')
    sensor_oid = VarcharField(db_column='sensor_oid', null=True)
    up = VarcharField(db_column='up', choices=STATE_CHOICES)

    class Meta(object):
        db_table = 'powersupply_or_fan'

    def get_unresolved_alerts(self):
        """Returns a queryset of unresolved psuState alerts for this unit"""
        return self.netbox.get_unresolved_alerts().filter(
            event_type__id__in=['psuState', 'fanState'],
            subid=self.id)

    def is_on_maintenance(self):
        """Returns True if the owning Netbox is on maintenance"""
        return self.netbox.is_on_maintenance()

    def __str__(self):
        return "{name} at {netbox}".format(
            name=self.name or self.descr,
            netbox=self.netbox
        )

    def get_absolute_url(self):
        """Returns a canonical URL to view fan/psu status"""
        base = self.netbox.get_absolute_url()
        return base + "#!sensors"


@python_2_unicode_compatible
class UnrecognizedNeighbor(models.Model):
    id = models.AutoField(primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    remote_id = VarcharField()
    remote_name = VarcharField()
    source = VarcharField()
    since = models.DateTimeField(auto_now_add=True)
    ignored_since = models.DateTimeField()

    class Meta(object):
        db_table = 'unrecognized_neighbor'
        ordering = ('remote_id',)

    def __str__(self):
        return u'%s:%s %s neighbor %s (%s)' % (
            self.netbox.sysname, self.interface.ifname,
            self.source,
            self.remote_id, self.remote_name)


@python_2_unicode_compatible
class IpdevpollJobLog(models.Model):
    id = models.AutoField(primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid', null=False,
                               related_name='job_log')
    job_name = VarcharField(null=False, blank=False)
    end_time = models.DateTimeField(auto_now_add=True, null=False)
    duration = models.FloatField(null=True)
    success = models.NullBooleanField(default=False, null=True)
    interval = models.IntegerField(null=True)

    class Meta(object):
        db_table = 'ipdevpoll_job_log'

    def __str__(self):
        return u"Job %s for %s ended in %s at %s, after %s seconds" % (
            self.job_name, self.netbox.sysname,
            'success' if self.success else 'failure',
            self.end_time, self.duration
            )

    def is_overdue(self):
        """Returns True if the next run if this job is overdue.

        Does _NOT_ check whether the next job has actually run or not,
        just that it should have been run.  If the interval of this job is
        unknown, None is returned.

        """
        if self.interval is not None:
            next_run = self.end_time + dt.timedelta(seconds=self.interval)
            return next_run < dt.datetime.now()

    def previous(self):
        """Returns the log entry of the previous job of the same name for the
         same netbox.

        """
        try:
            prev = IpdevpollJobLog.objects.filter(
                netbox=self.netbox,
                job_name=self.job_name,
                end_time__lt=self.end_time).order_by('-end_time')[0]
            return prev
        except IndexError:
            return None

    def has_result(self):
        """Returns True if this job ran and had an actual result"""
        return self.success is not None

    def get_last_runtimes(self, job_count=30):
        """Get the last runtimes for these jobs on this netbox

        Does not verify that the jobs are sequential, there may be large gaps
        between the actual runs.

        :returns: A list of lists where the first element is local seconds since
                  epoch and second element is the runtime
        """
        jobs = IpdevpollJobLog.objects.filter(
            job_name=self.job_name, netbox=self.netbox).order_by(
                '-end_time')[:job_count]
        runtimes = [
            [int((j.end_time - dt.datetime(1970, 1, 1)).total_seconds()),
             j.duration] for j in jobs]
        runtimes.reverse()
        return runtimes

    def get_absolute_url(self):
        """Returns the Netbox' URL"""
        return self.netbox.get_absolute_url()


class Netbios(models.Model):
    """Model representing netbios names collected by the netbios tracker"""
    import datetime

    id = models.AutoField(db_column='netbiosid', primary_key=True)
    ip = models.GenericIPAddressField()
    mac = models.CharField(max_length=17, blank=False, null=True)
    name = VarcharField()
    server = VarcharField()
    username = VarcharField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = DateTimeInfinityField(default=datetime.datetime.max)

    class Meta(object):
        db_table = 'netbios'


class POEGroup(models.Model):
    """Model representing a group of power over ethernet ports"""
    id = models.AutoField(db_column='poegroupid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    module = models.ForeignKey('Module', db_column='moduleid',
                               null=True)
    index = models.IntegerField()

    STATUS_ON = 1
    STATUS_OFF = 2
    STATUS_FAULTY = 3
    STATUS_CHOICES = (
        (STATUS_ON, 'on'),
        (STATUS_OFF, 'off'),
        (STATUS_FAULTY, 'faulty'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES)
    power = models.IntegerField()

    def get_graph_url(self, time_frame='1day'):
        metric = metric_path_for_power(self.netbox, self.index)
        return get_simple_graph_url([metric],
                                    time_frame=time_frame)

    def get_active_ports(self):
        return self.poeport_set.filter(
            admin_enable=True,
            detection_status=POEPort.STATUS_DELIVERING_POWER)

    @property
    def name(self):
        if self.module:
            return "Module {}".format(self.module.name)
        else:
            return "PoE Group {}".format(self.index)

    class Meta(object):
        db_table = 'poegroup'
        unique_together = (('netbox', 'index'),)
        ordering = ('index',)


class POEPort(models.Model):
    """Model representing a PoE port"""
    id = models.AutoField(db_column='poeportid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    poegroup = models.ForeignKey('POEGroup', db_column='poegroupid')
    interface = models.ForeignKey('Interface', db_column='interfaceid',
                                  null=True)
    admin_enable = models.BooleanField(default=False)
    index = models.IntegerField()

    STATUS_DISABLED = 1
    STATUS_SEARCHING = 2
    STATUS_DELIVERING_POWER = 3
    STATUS_FAULT = 4
    STATUS_TEST = 5
    STATUS_OTHER_FAULT = 6
    STATUS_CHOICES = (
        (STATUS_DISABLED, 'disabled'),
        (STATUS_SEARCHING, 'searching'),
        (STATUS_DELIVERING_POWER, 'delivering power'),
        (STATUS_FAULT, 'fault'),
        (STATUS_TEST, 'test'),
        (STATUS_OTHER_FAULT, 'other fault'),
    )
    detection_status = models.IntegerField(choices=STATUS_CHOICES)

    PRIORITY_LOW = 3
    PRIORITY_HIGH = 2
    PRIORITY_CRITICAL = 1
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, 'low'),
        (PRIORITY_HIGH, 'high'),
        (PRIORITY_CRITICAL, 'critical'),
    )
    priority = models.IntegerField(choices=PRIORITY_CHOICES)

    CLASSIFICATION_CHOICES = (
        (1, 'class0'),
        (2, 'class1'),
        (3, 'class2'),
        (4, 'class3'),
        (5, 'class4'),
    )
    classification = models.IntegerField(choices=CLASSIFICATION_CHOICES)

    class Meta(object):
        db_table = 'poeport'
        unique_together = (('poegroup', 'index'),)
        ordering = ('index',)

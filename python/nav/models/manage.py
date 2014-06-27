# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2012 UNINETT AS
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

# pylint: disable=R0903

import datetime as dt
import IPy
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from itertools import count, groupby

from nav.bitvector import BitVector
from nav.metrics.data import get_metric_average
from nav.metrics.graphs import get_simple_graph_url
from nav.metrics.names import get_all_leaves_below
from nav.metrics.templates import (
    metric_prefix_for_interface,
    metric_prefix_for_ports,
    metric_prefix_for_device,
    metric_path_for_packet_loss,
    metric_path_for_roundtrip_time,
    metric_path_for_sensor
)
import nav.natsort
from nav.models.fields import DateTimeInfinityField, VarcharField, PointField
from nav.models.fields import CIDRField
from nav.models.rrd import RrdDataSource
from django_hstore import hstore
import nav.models.event



#######################################################################
### Netbox-related models

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
    TIME_FRAMES = ('day', 'week', 'month')

    id = models.AutoField(db_column='netboxid', primary_key=True)
    ip = models.IPAddressField(unique=True)
    room = models.ForeignKey('Room', db_column='roomid')
    type = models.ForeignKey('NetboxType', db_column='typeid',
                             blank=True, null=True)
    device = models.ForeignKey('Device', db_column='deviceid')
    sysname = VarcharField(unique=True)
    category = models.ForeignKey('Category', db_column='catid')
    netboxgroups = models.ManyToManyField('NetboxGroup',
                                          through='NetboxCategory')
    organization = models.ForeignKey('Organization', db_column='orgid')
    read_only = VarcharField(db_column='ro', blank=True, null=True)
    read_write = VarcharField(db_column='rw', blank=True, null=True)
    up = models.CharField(max_length=1, choices=UP_CHOICES, default=UP_UP)
    snmp_version = models.IntegerField(verbose_name="SNMP version")
    up_since = models.DateTimeField(db_column='upsince', auto_now_add=True)
    up_to_date = models.BooleanField(db_column='uptodate', default=False)
    discovered = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'netbox'
        verbose_name = 'netbox'
        verbose_name_plural = 'netboxes'
        ordering = ('sysname',)

    def __unicode__(self):
        return self.get_short_sysname()

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
        pktloss_id = metric_path_for_packet_loss(self.sysname)
        rtt_id = metric_path_for_roundtrip_time(self.sysname)

        result = {
            'availability': {
                'data_source': pktloss_id,
            },
            'response_time': {
                'data_source': rtt_id,
            },
        }

        for time_frame in self.TIME_FRAMES:
            avg = get_metric_average([pktloss_id, rtt_id],
                                              start="-1%s" % time_frame)

            # Availability
            pktloss = avg.get(pktloss_id, None)
            if pktloss is not None:
                pktloss = 100 - (pktloss * 100)
            result['availability'][time_frame] = pktloss

            # Response time
            result['response_time'][time_frame] = avg.get(rtt_id, None)

        return result

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
            return self.info_set.get(variable='function').value
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
            return self.sysname

    def get_rrd_data_sources(self):
        """Returns all relevant RRD data sources"""
        return RrdDataSource.objects.filter(rrd_file__netbox=self
            ).exclude(
                Q(rrd_file__subsystem__name__in=('pping', 'serviceping')) |
                Q(rrd_file__key__isnull=False,
                    rrd_file__key__in=('swport', 'gwport', 'interface'))
            ).order_by('description')

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
        except for ports, which are seen as separate.

        :returns: A list of dicts describing the metrics, e.g.:
                  {id:"nav.devices.some-gw.cpu.cpu1.loadavg1min",
                   group="cpu",
                   suffix="cpu1.loadavg1min"}

        """
        exclude = metric_prefix_for_ports(self.sysname)
        base = metric_prefix_for_device(self.sysname)

        nodes = get_all_leaves_below(base, [exclude])
        result = []
        for node in nodes:
            suffix = node.replace(base + '.', '')
            elements = suffix.split('.')
            group = elements[0]
            suffix = '.'.join(elements[1:])
            result.append(dict(id=node, group=group, suffix=suffix))

        return result

class NetboxInfo(models.Model):
    """From NAV Wiki: The netboxinfo table is the place
    to store additional info on a netbox."""

    id = models.AutoField(db_column='netboxinfoid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid',
        related_name='info_set')
    key = VarcharField()
    variable = VarcharField(db_column='var')
    value = models.TextField(db_column='val')

    class Meta:
        db_table = 'netboxinfo'
        unique_together = (('netbox', 'key', 'variable', 'value'),)

    def __unicode__(self):
        return u'%s="%s"' % (self.variable, self.value)


class NetboxPrefix(models.Model):
    """Which prefix a netbox is connected to.

    This models the read-only netboxprefix view.

    """
    netbox = models.OneToOneField('Netbox', db_column='netboxid',
                                  primary_key=True)
    prefix = models.ForeignKey('Prefix', db_column='prefixid',
                               related_name='netbox_set')

    class Meta:
        db_table = 'netboxprefix'
        unique_together = (('netbox', 'prefix'),)

    def __unicode__(self):
        return u'%s at %s' % (self.netbox.sysname, self.prefix.net_address)

    def save(self, *args, **kwargs):
        """Does nothing, since this models a database view."""
        raise Exception("Cannot save to a view.")


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

    class Meta:
        db_table = 'device'

    def __unicode__(self):
        return self.serial or ''


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

    class Meta:
        db_table = 'module'
        verbose_name = 'module'
        ordering = ('netbox', 'module_number', 'name')
        unique_together = (('netbox', 'name'),)

    def __unicode__(self):
        return u'Module {name}, at {netbox}'.format(
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
        return Interface.objects.select_related(
            depth=2).filter(module=self, baseport__isnull=False)

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


class Memory(models.Model):
    """From NAV Wiki: The mem table describes the memory
    (memory and nvram) of a netbox."""

    id = models.AutoField(db_column='memid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    type = VarcharField(db_column='memtype')
    device = VarcharField()
    size = models.IntegerField()
    used = models.IntegerField()

    class Meta:
        db_table = 'mem'
        unique_together = (('netbox', 'type', 'device'),)

    def __unicode__(self):
        if self.used is not None and self.size is not None and self.size != 0:
            return u'%s, %d%% used' % (self.type, self.used * 100 // self.size)
        else:
            return self.type


class Room(models.Model):
    """From NAV Wiki: The room table defines a wiring closes / network room /
    server room."""

    id = models.CharField(db_column='roomid', max_length=30, primary_key=True)
    location = models.ForeignKey('Location', db_column='locationid',
                                 blank=True, null=True)
    description = VarcharField(db_column='descr', blank=True)
    position = PointField(null=True, blank=True, default=None)
    data = hstore.DictionaryField()

    objects = hstore.HStoreManager()

    class Meta:
        db_table = 'room'
        verbose_name = 'room'

    def __unicode__(self):
        return u'%s (%s)' % (self.id, self.description)


class Location(models.Model):
    """From NAV Wiki: The location table defines a group of rooms; i.e. a
    campus."""

    id = models.CharField(db_column='locationid',
        max_length=30, primary_key=True)
    description = VarcharField(db_column='descr')

    class Meta:
        db_table = 'location'
        verbose_name = 'location'

    def __unicode__(self):
        return u'%s (%s)' % (self.id, self.description)


class Organization(models.Model):
    """From NAV Wiki: The org table defines an organization which is in charge
    of a given netbox and is the user of a given prefix."""

    id = models.CharField(db_column='orgid', max_length=30, primary_key=True)
    parent = models.ForeignKey('self', db_column='parent',
                               blank=True, null=True)
    description = VarcharField(db_column='descr', blank=True)
    contact = VarcharField(db_column='contact', blank=True)
    data = hstore.DictionaryField()

    objects = hstore.HStoreManager()

    class Meta:
        db_table = 'org'
        verbose_name = 'organization'
        ordering = ['id']

    def __unicode__(self):
        return u'%s (%s)' % (self.id, self.description)

    def extract_emails(self):
        """Naively extract email addresses from the contact string"""
        contact = self.contact if self.contact else ""
        return re.findall(r'(\b[\w.]+@[\w.]+\b)', contact)


class Category(models.Model):
    """From NAV Wiki: The cat table defines the categories of a netbox
    (GW,GSW,SW,EDGE,WLAN,SRV,OTHER)."""

    id = models.CharField(db_column='catid', max_length=8, primary_key=True)
    description = VarcharField(db_column='descr')
    req_snmp = models.BooleanField()

    class Meta:
        db_table = 'cat'
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __unicode__(self):
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


class NetboxGroup(models.Model):
    """A group that one or more netboxes belong to

    A group is a tag of sorts for grouping netboxes. You can put two netboxes
    in the same group and then use that metainfo in reports and alert profiles.

    This was formerly known as subcat but was altered to netboxgroup because
    the same subcategory could not exist on different categories.

    """

    id = VarcharField(db_column='netboxgroupid', primary_key=True)
    description = VarcharField(db_column='descr')

    class Meta:
        db_table = 'netboxgroup'

    def __unicode__(self):
        return self.id


class NetboxCategory(models.Model):
    """Store the relation between a netbox and its groups"""

    # TODO: This should be a ManyToMany-field in Netbox, but at this time
    # Django only supports specifying the name of the M2M-table, and not the
    # column names.
    id = models.AutoField(primary_key=True)  # Serial for faking a primary key
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    category = models.ForeignKey('NetboxGroup', db_column='category')

    class Meta:
        db_table = 'netboxcategory'
        unique_together = (('netbox', 'category'),)  # Primary key

    def __unicode__(self):
        return u'%s in category %s' % (self.netbox, self.category)


class NetboxType(models.Model):
    """From NAV Wiki: The type table defines the type of a netbox, the
    sysobjectid being the unique identifier."""

    id = models.AutoField(db_column='typeid', primary_key=True)
    vendor = models.ForeignKey('Vendor', db_column='vendorid')
    name = VarcharField(db_column='typename', verbose_name="type name")
    sysobjectid = VarcharField(unique=True)
    description = VarcharField(db_column='descr')

    class Meta:
        db_table = 'type'
        unique_together = (('vendor', 'name'),)

    def __unicode__(self):
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
            return long(enterprise)

#######################################################################
### Device management


class Vendor(models.Model):
    """From NAV Wiki: The vendor table defines vendors. A
    type is of a vendor. A product is of a vendor."""

    id = models.CharField(db_column='vendorid', max_length=15,
                          primary_key=True)

    class Meta:
        db_table = 'vendor'

    def __unicode__(self):
        return self.id

#######################################################################
### Router/topology


class GwPortPrefix(models.Model):
    """Defines IP addresses assigned to Interfaces, with a relation to the
    associated Prefix.

    """
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    prefix = models.ForeignKey('Prefix', db_column='prefixid')
    gw_ip = models.IPAddressField(db_column='gwip', primary_key=True)
    virtual = models.BooleanField(default=False)

    class Meta:
        db_table = 'gwportprefix'

    def __unicode__(self):
        return self.gw_ip

class PrefixManager(models.Manager):
    def contains_ip(self, ipaddr):
        """Gets all prefixes that contain the given IP address,
        ordered by descending network mask length.

        """
        return self.get_query_set().exclude(
            vlan__net_type="loopback"
        ).extra(
            select={'mlen': 'masklen(netaddr)'},
            where=["%s <<= netaddr"],
            params=[ipaddr],
            order_by=["-mlen"]
        ).select_related('vlan')

class Prefix(models.Model):
    """From NAV Wiki: The prefix table stores IP prefixes."""

    objects = PrefixManager()

    id = models.AutoField(db_column='prefixid', primary_key=True)
    net_address = CIDRField(db_column='netaddr', unique=True)
    vlan = models.ForeignKey('Vlan', db_column='vlanid')

    class Meta:
        db_table = 'prefix'

    def __unicode__(self):
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

    class Meta:
        db_table = 'vlan'

    def __unicode__(self):
        result = u''
        if self.vlan:
            result += u'%d' % self.vlan
        else:
            result += u'N/A'
        if self.net_ident:
            result += ' (%s)' % self.net_ident
        return result


class NetType(models.Model):
    """From NAV Wiki: The nettype table defines network type;lan, core, link,
    elink, loopback, closed, static, reserved, scope. The network types are
    predefined in NAV and may not be altered."""

    id = VarcharField(db_column='nettypeid', primary_key=True)
    description = VarcharField(db_column='descr')
    edit = models.BooleanField(default=False)

    class Meta:
        db_table = 'nettype'

    def __unicode__(self):
        return self.id


class Usage(models.Model):
    """From NAV Wiki: The usage table defines the user group (student, staff
    etc). Usage categories are maintained in the edit database tool."""

    id = models.CharField(db_column='usageid',
        max_length=30, primary_key=True)
    description = VarcharField(db_column='descr')

    class Meta:
        db_table = 'usage'

    def __unicode__(self):
        return u'%s (%s)' % (self.id, self.description)


class Arp(models.Model):
    """From NAV Wiki: The arp table contains (ip, mac, time
    start, time end)."""

    id = models.AutoField(db_column='arpid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid', null=True)
    prefix = models.ForeignKey('Prefix', db_column='prefixid', null=True)
    sysname = VarcharField()
    ip = models.IPAddressField()
    # TODO: Create MACAddressField in Django
    mac = models.CharField(max_length=17)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = DateTimeInfinityField()

    class Meta:
        db_table = 'arp'

    def __unicode__(self):
        return u'%s to %s' % (self.ip, self.mac)

#######################################################################
### Switch/topology


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

    class Meta:
        db_table = 'swportvlan'
        unique_together = (('interface', 'vlan'),)

    def __unicode__(self):
        return u'%s, on vlan %s' % (self.interface, self.vlan)


class SwPortAllowedVlan(models.Model):
    """Stores a hexstring that encodes the list of VLANs that are allowed to
    traverse a trunk port.

    """
    interface = models.OneToOneField('Interface', db_column='interfaceid',
                                     primary_key=True)
    hex_string = VarcharField(db_column='hexstring')
    _cached_hex_string = ''
    _cached_vlan_set = None

    class Meta:
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

    def _calculate_allowed_vlans(self):
        octets = [self.hex_string[x:x + 2]
                  for x in xrange(0, len(self.hex_string), 2)]
        string = ''.join(chr(int(o, 16)) for o in octets)
        bits = BitVector(string)
        return set(bits.get_set_bits())

    def __unicode__(self):
        return u'Allowed vlans for swport %s' % self.interface


class SwPortBlocked(models.Model):
    """This table defines the spanning tree blocked ports for a given vlan for
    a given switch port."""

    id = models.AutoField(db_column='swportblockedid', primary_key=True)
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    vlan = models.IntegerField()

    class Meta:
        db_table = 'swportblocked'
        unique_together = (('interface', 'vlan'),)  # Primary key

    def __unicode__(self):
        return '%d, at %s' % (self.vlan, self.interface)


class AdjacencyCandidate(models.Model):
    """A candidate for netbox/interface adjacency.

    Used in the process of building the physical topology of the
    network. AdjacencyCandidate defines a candidate for next hop physical
    neighbor.

    """
    id = models.AutoField(db_column='adjacency_candidateid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    to_netbox = models.ForeignKey('Netbox', db_column='to_netboxid')
    to_interface = models.ForeignKey('Interface', db_column='to_interfaceid',
                                     null=True)
    source = VarcharField()
    miss_count = models.IntegerField(db_column='misscnt', default=0)

    class Meta:
        db_table = 'adjacency_candidate'
        unique_together = (('netbox', 'interface', 'to_netbox', 'source'),)

    def __unicode__(self):
        return u'%s:%s %s candidate %s:%s' % (self.netbox, self.interface,
                                              self.source,
                                              self.to_netbox,
                                              self.to_interface)


class NetboxVtpVlan(models.Model):
    """From NAV Wiki: A help table that contains the vtp vlan database of a
    switch. For certain cisco switches cam information is gathered using a
    community@vlan string. It is then necessary to know all vlans that are
    active on a switch. The vtp vlan table is an extra source of
    information."""

    id = models.AutoField(primary_key=True)  # Serial for faking a primary key
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    vtp_vlan = models.IntegerField(db_column='vtpvlan')

    class Meta:
        db_table = 'netbox_vtpvlan'
        unique_together = (('netbox', 'vtp_vlan'),)

    def __unicode__(self):
        return u'%d, at %s' % (self.vtp_vlan, self.netbox)


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

    class Meta:
        db_table = 'cam'
        unique_together = (('netbox', 'sysname', 'module', 'port',
                            'mac', 'start_time'),)

    def __unicode__(self):
        return u'%s, %s' % (self.mac, self.netbox)


#######################################################################
### Interfaces and related attributes

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
    ifconnectorpresent = models.BooleanField()
    ifpromiscuousmode = models.BooleanField()
    ifalias = VarcharField()

    baseport = models.IntegerField()
    media = VarcharField(null=True)
    vlan = models.IntegerField()
    trunk = models.BooleanField()
    duplex = models.CharField(max_length=1, choices=DUPLEX_CHOICES, null=True)

    to_netbox = models.ForeignKey('Netbox', db_column='to_netboxid', null=True,
        related_name='connected_to_interface')
    to_interface = models.ForeignKey('self', db_column='to_interfaceid',
        null=True, related_name='connected_to_interface')

    gone_since = models.DateTimeField()

    class Meta:
        db_table = u'interface'
        ordering = ('baseport', 'ifname')

    def __init__(self, *args, **kwargs):
        super(Interface, self).__init__(*args, **kwargs)
        # Create cache dictionary
        # FIXME: Replace with real Django caching
        self.time_since_activity_cache = {}

    def __unicode__(self):
        return u'%s at %s' % (self.ifname, self.netbox)

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
            for swpv in self.swportvlan_set.select_related(depth=1)]
        if self.vlan is not None and self.vlan not in vlans:
            vlans.append(self.vlan)
        vlans.sort()
        return vlans

    def get_last_cam_record(self):
        """Returns the newest cam record gotten from this switch port."""
        return self.netbox.cam_set.filter(ifindex=self.ifindex).latest(
            'end_time')

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

    def get_rrd_data_sources(self):
        """Returns all relevant RRD data sources"""
        return RrdDataSource.objects.filter(
                rrd_file__key='interface', rrd_file__value=str(self.id)
            ).order_by('description')

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

    def below_me(self):
        """Returns interfaces stacked with this one on a layer below"""
        return Interface.objects.filter(lower_layer__higher=self)

    def above_me(self):
        """Returns interfaces stacked with this one on a layer above"""
        return Interface.objects.filter(higher_layer__lower=self)

    def get_sorted_vlans(self):
        """Returns a queryset of sorted swportvlans"""
        return self.swportvlan_set.select_related('vlan').order_by(
            'vlan__vlan')


class InterfaceStack(models.Model):
    """Interface layered stacking relationships"""
    higher = models.ForeignKey(Interface, db_column='higher',
                               related_name='higher_layer')
    lower = models.ForeignKey(Interface, db_column='lower',
                              related_name='lower_layer')

    class Meta:
        db_table = u'interface_stack'


class IanaIftype(models.Model):
    """IANA-registered iftype values"""
    iftype = models.IntegerField(primary_key=True)
    name = VarcharField()
    descr = VarcharField()

    class Meta:
        db_table = u'iana_iftype'


class RoutingProtocolAttribute(models.Model):
    """Routing protocol metric as configured on a routing interface"""
    id = models.IntegerField(primary_key=True)
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    name = VarcharField(db_column='protoname')
    metric = models.IntegerField()

    class Meta:
        db_table = u'rproto_attr'


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
    UNIT_HERTZ = 'hertz'         # frequency
    UNIT_CELSIUS = 'celsius'     # temperature
    UNIT_PERCENT_RELATIVE_HUMIDITY = 'percentRH'  # percent relative humidity
    UNIT_RPM = 'rpm'             # shaft revolutions per minute
    UNIT_CMM = 'cmm'             # cubic meters per minute (airflow)
    UNIT_TRUTHVALUE = 'boolean'  # value takes { true(1), false(2) }

    UNIT_OF_MEASUREMENTS_CHOICES = (
        (UNIT_OTHER, 'Other'),
        (UNIT_UNKNOWN, 'Unknown'),
        (UNIT_VOLTS_AC, 'VoltsAC'),
        (UNIT_VOLTS_DC, 'VoltsDC'),
        (UNIT_AMPERES, 'Amperes'),
        (UNIT_WATTS, 'Watts'),
        (UNIT_HERTZ, 'Hertz'),
        (UNIT_CELSIUS, 'Celsius'),
        (UNIT_PERCENT_RELATIVE_HUMIDITY, 'Relative humidity'),
        (UNIT_RPM, 'Revolutions per minute'),
        (UNIT_CMM, 'Cubic meters per minute'),
        (UNIT_TRUTHVALUE, 'Boolean'),
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

    class Meta:
        db_table = 'sensor'

    def get_metric_name(self):
        return metric_path_for_sensor(self.netbox.sysname, self.internal_name)

    def get_graph_url(self, time_frame='1day'):
        return get_simple_graph_url([self.get_metric_name()],
                                    time_frame=time_frame)


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

    class Meta:
        db_table = 'powersupply_or_fan'

    def get_unresolved_alerts(self):
        """Returns a queryset of unresolved psuState alerts for this unit"""
        return self.netbox.get_unresolved_alerts().filter(
            event_type__id__in=['psuState', 'fanState'],
            subid=self.id)

class UnrecognizedNeighbor(models.Model):
    id = models.AutoField(primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    remote_id = VarcharField()
    remote_name = VarcharField()
    source = VarcharField()
    since = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'unrecognized_neighbor'

    def __unicode__(self):
        return u'%s:%s %s neighbor %s (%s)' % (
            self.netbox.sysname, self.interface.ifname,
            self.source,
            self.remote_id, self.remote_name)


class IpdevpollJobLog(models.Model):
    id = models.AutoField(primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid', null=False,
                               related_name='job_log')
    job_name = VarcharField(null=False, blank=False)
    end_time = models.DateTimeField(auto_now_add=True, null=False)
    duration = models.FloatField(null=True)
    success = models.BooleanField(default=False, null=False)
    interval = models.IntegerField(null=True)

    class Meta:
        db_table = 'ipdevpoll_job_log'

    def __unicode__(self):
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


class Netbios(models.Model):
    """Model representing netbios names collected by the netbios tracker"""
    import datetime

    id = models.AutoField(db_column='netbiosid', primary_key=True)
    ip = models.IPAddressField()
    mac = models.CharField(max_length=17, blank=False, null=True)
    name = VarcharField()
    server = VarcharField()
    username = VarcharField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = DateTimeInfinityField(default=datetime.datetime.max)

    class Meta:
        db_table = 'netbios'

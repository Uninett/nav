# -*- coding: utf-8 -*-
#
# Copyright (C) 2007,2008 UNINETT AS
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

import datetime as dt
import IPy
import time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q

import nav.natsort
from nav.models.fields import DateTimeInfinityField

# Choices used in Interface model and 'ipdevinfo' for determining interface status
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


#######################################################################
### Netbox-related models

class Netbox(models.Model):
    """From MetaNAV: The netbox table is the heart of the heart so to speak,
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
    type = models.ForeignKey('NetboxType', db_column='typeid', null=True)
    device = models.ForeignKey('Device', db_column='deviceid')
    sysname = models.CharField(unique=True, max_length=-1)
    category = models.ForeignKey('Category', db_column='catid')
    subcategories = models.ManyToManyField('Subcategory',
        through='NetboxCategory')
    organization = models.ForeignKey('Organization', db_column='orgid')
    read_only = models.CharField(db_column='ro', max_length=-1)
    read_write = models.CharField(db_column='rw', max_length=-1)
    prefix = models.ForeignKey('Prefix', db_column='prefixid', null=True)
    up = models.CharField(max_length=1, choices=UP_CHOICES, default=UP_UP)
    snmp_version = models.IntegerField()
    up_since = models.DateTimeField(db_column='upsince')
    up_to_date = models.BooleanField(db_column='uptodate')
    discovered = models.DateTimeField()

    class Meta:
        db_table = 'netbox'
        ordering = ('sysname',)

    def __unicode__(self):
        return self.get_short_sysname()

    def get_absolute_url(self):
        kwargs={
            'name': self.sysname,
        }
        return reverse('ipdevinfo-details-by-name', kwargs=kwargs)

    def last_updated(self):
        try:
            # XXX: Netboxes with multiple values for lastUpdated in NetboxInfo
            # have been observed. Using the highest value.
            value = self.info_set.filter(variable='lastUpdated').order_by(
                '-value')[0].value
            value = int(value) / 1000.0
            return dt.datetime.fromtimestamp(value)
        except IndexError:
            return None
        except ValueError:
            return '(Invalid value in DB)'

    def get_gwports(self):
        return Interface.objects.filter(netbox=self, gwportprefix__isnull=False).distinct()
    
    def get_gwports_sorted(self):
        """Returns gwports naturally sorted by interface name"""

        ports = self.get_gwports().select_related('module', 'netbox')
        interface_names = [p.ifname for p in ports]
        unsorted = dict(zip(interface_names, ports))
        interface_names.sort(key=nav.natsort.split)
        sorted_ports = [unsorted[i] for i in interface_names]
        return sorted_ports

    def get_swports(self):
        return Interface.objects.filter(netbox=self, baseport__isnull=False).distinct()
    
    def get_swports_sorted(self):
        """Returns swports naturally sorted by interface name"""

        ports = self.get_swports().select_related('module', 'netbox')
        interface_names = [p.ifname for p in ports]
        unsorted = dict(zip(interface_names, ports))
        interface_names.sort(key=nav.natsort.split)
        sorted_ports = [unsorted[i] for i in interface_names]
        return sorted_ports

    def get_availability(self):
        from nav.models.rrd import RrdDataSource

        def average(rds, time_frame):
            from nav.rrd import presenter
            rrd = presenter.presentation()
            rrd.timeLast(time_frame)
            rrd.addDs(rds.id)
            value = rrd.average(onErrorReturn=None, onNanReturn=None)
            if not value:
                return None
            else:
                return value[0]

        try:
            data_sources = RrdDataSource.objects.filter(
                rrd_file__subsystem='pping', rrd_file__netbox=self)
            # XXX: Multiple identical data sources in the database have been
            # observed. Using the result with highest primary key.
            # FIXME: Should probably check the mtime of the RRD files on disk
            # and use the newest one.
            data_source_status = data_sources.filter(name='STATUS'
                ).order_by('-pk')[0]
            data_source_response_time = data_sources.filter(
                name='RESPONSETIME').order_by('-pk')[0]
        except IndexError:
            return None

        result = {
            'availability': {
                'data_source': data_source_status,
            },
            'response_time': {
                'data_source': data_source_response_time,
            },
        }

        for time_frame in self.TIME_FRAMES:
            # Availability
            value = average(data_source_status, time_frame)
            if value is not None:
                value = 100 - (value * 100)
            result['availability'][time_frame] = value

            # Response time
            value = average(data_source_response_time, time_frame)
            result['response_time'][time_frame] = value

        return result

    def get_uplinks(self):
        result = []

        for iface in self.connected_to_interface.all():
            if iface.swportvlan_set.filter(
                direction=SwPortVlan.DIRECTION_DOWN).count():
                result.append({
                    'other': iface,
                    'this': iface.to_interface,
                })

        return result

    def get_function(self):
        try:
            return self.info_set.get(variable='function').value
        except NetboxInfo.DoesNotExist:
            return None

    def get_filtered_prefix(self):
        if self.prefix.vlan.net_type.description in (
            'scope', 'private', 'reserved'):
            return None
        else:
            return self.prefix

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

        from nav.models.rrd import RrdDataSource
        return RrdDataSource.objects.filter(rrd_file__netbox=self
            ).exclude(
                Q(rrd_file__subsystem__name__in=('pping', 'serviceping')) |
                Q(rrd_file__key__isnull=False,
                    rrd_file__key__in=('swport', 'gwport', 'interface'))
            ).order_by('description')

class NetboxInfo(models.Model):
    """From MetaNAV: The netboxinfo table is the place to store additional info
    on a netbox."""

    id = models.AutoField(db_column='netboxinfoid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid',
        related_name='info_set')
    key = models.CharField(max_length=-1)
    variable = models.CharField(db_column='var', max_length=-1)
    value = models.TextField(db_column='val')

    class Meta:
        db_table = 'netboxinfo'
        unique_together = (('netbox', 'key', 'variable', 'value'),)

    def __unicode__(self):
        return u'%s="%s"' % (self.variable, self.value)

class Device(models.Model):
    """From MetaNAV: The device table contains all physical devices in the
    network. As opposed to the netbox table, the device table focuses on the
    physical box with its serial number. The device may appear as different net
    boxes or may appear in different modules throughout its lifetime."""

    id = models.AutoField(db_column='deviceid', primary_key=True)
    serial = models.CharField(unique=True, max_length=-1, null=True)
    hardware_version = models.CharField(db_column='hw_ver', max_length=-1, null=True)
    firmware_version = models.CharField(db_column='fw_ver', max_length=-1, null=True)
    software_version = models.CharField(db_column='sw_ver', max_length=-1, null=True)
    discovered = models.DateTimeField(default=dt.datetime.now)

    class Meta:
        db_table = 'device'

    def __unicode__(self):
        return self.serial

class Module(models.Model):
    """From MetaNAV: The module table defines modules. A module is a part of a
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
    name = models.CharField(max_length=-1)
    model = models.CharField(max_length=-1)
    description = models.CharField(db_column='descr', max_length=-1)
    up = models.CharField(max_length=1, choices=UP_CHOICES, default=UP_UP)
    down_since = models.DateTimeField(db_column='downsince')

    class Meta:
        db_table = 'module'
        ordering = ('netbox', 'module_number', 'name')
        unique_together = (('netbox', 'name'),)

    def __unicode__(self):
        return u'%d, at %s' % (self.name or self.module_number, self.netbox)

    def get_absolute_url(self):
        kwargs={
            'netbox_sysname': self.netbox.sysname,
            'module_name': self.name,
        }
        return reverse('ipdevinfo-module-details', kwargs=kwargs)

    def get_gwports(self):
        return Interface.objects.select_related(depth=2). \
            filter(module=self, gwportprefix__isnull=False).distinct()

    def get_gwports_sorted(self):
        """Returns gwports naturally sorted by interface name"""

        ports = self.get_gwports()
        interface_names = [p.ifname for p in ports]
        unsorted = dict(zip(interface_names, ports))
        interface_names.sort(key=nav.natsort.split)
        sorted_ports = [unsorted[i] for i in interface_names]
        return sorted_ports

    def get_swports(self):
        return Interface.objects.select_related(depth=2).filter(module=self, baseport__isnull=False)

    def get_swports_sorted(self):
        """Returns swports naturally sorted by interface name"""

        ports = self.get_swports()
        interface_names = [p.ifname for p in ports]
        unsorted = dict(zip(interface_names, ports))
        interface_names.sort(key=nav.natsort.split)
        sorted_ports = [unsorted[i] for i in interface_names]
        return sorted_ports

class Memory(models.Model):
    """From MetaNAV: The mem table describes the memory (memory and nvram) of a
    netbox."""

    id = models.AutoField(db_column='memid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    type = models.CharField(db_column='memtype', max_length=-1)
    device = models.CharField(max_length=-1)
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
    """From MetaNAV: The room table defines a wiring closes / network room /
    server room."""

    id = models.CharField(db_column='roomid', max_length=30, primary_key=True)
    location = models.ForeignKey('Location', db_column='locationid')
    description = models.CharField(db_column='descr', max_length=-1)
    optional_1 = models.CharField(db_column='opt1', max_length=-1)
    optional_2 = models.CharField(db_column='opt2', max_length=-1)
    optional_3 = models.CharField(db_column='opt3', max_length=-1)
    optional_4 = models.CharField(db_column='opt4', max_length=-1)

    class Meta:
        db_table = 'room'

    def __unicode__(self):
        return u'%s (%s)' % (self.id, self.description)

class Location(models.Model):
    """From MetaNAV: The location table defines a group of rooms; i.e. a
    campus."""

    id = models.CharField(db_column='locationid',
        max_length=30, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)

    class Meta:
        db_table = 'location'

    def __unicode__(self):
        return self.description

class Organization(models.Model):
    """From MetaNAV: The org table defines an organization which is in charge
    of a given netbox and is the user of a given prefix."""

    id = models.CharField(db_column='orgid', max_length=30, primary_key=True)
    parent = models.ForeignKey('self', db_column='parent', null=True)
    description = models.CharField(db_column='descr', max_length=-1)
    optional_1 = models.CharField(db_column='opt1', max_length=-1)
    optional_2 = models.CharField(db_column='opt2', max_length=-1)
    optional_3 = models.CharField(db_column='opt3', max_length=-1)

    class Meta:
        db_table = 'org'

    def __unicode__(self):
        return u'%s (%s)' % (self.id, self.description)

class Category(models.Model):
    """From MetaNAV: The cat table defines the categories of a netbox
    (GW,GSW,SW,EDGE,WLAN,SRV,OTHER)."""

    id = models.CharField(db_column='catid', max_length=8, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    req_snmp = models.BooleanField()

    class Meta:
        db_table = 'cat'

    def __unicode__(self):
        return u'%s (%s)' % (self.id, self.description)

    def is_gw(self):
        return self.id == 'GW'

    def is_gsw(self):
        return self.id == 'GSW'

    def is_sw(self):
        return self.id == 'SW'

    def is_edge(self):
        return self.id == 'EDGE'

    def is_srv(self):
        return self.id == 'SRV'

    def is_other(self):
        return self.id == 'OTHER'

class Subcategory(models.Model):
    """From MetaNAV: The subcat table defines subcategories within a category.
    A category may have many subcategories. A subcategory belong to one and
    only one category."""

    id = models.CharField(db_column='subcatid', max_length=-1, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    category = models.ForeignKey('Category', db_column='catid')

    class Meta:
        db_table = 'subcat'

    def __unicode__(self):
        try:
            return u'%s, sub of %s' % (self.description, self.category)
        except Category.DoesNotExist:
            return self.description

class NetboxCategory(models.Model):
    """From MetaNAV: A netbox may be in many subcategories. This relation is
    defined here."""

    # TODO: This should be a ManyToMany-field in Netbox, but at this time
    # Django only supports specifying the name of the M2M-table, and not the
    # column names.
    id = models.AutoField(primary_key=True) # Serial for faking a primary key
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    category = models.ForeignKey('Subcategory', db_column='category')

    class Meta:
        db_table = 'netboxcategory'
        unique_together = (('netbox', 'category'),) # Primary key

    def __unicode__(self):
        return u'%s in category %s' % (self.netbox, self.category)

class NetboxType(models.Model):
    """From MetaNAV: The type table defines the type of a netbox, the
    sysobjectid being the unique identifier."""

    id = models.AutoField(db_column='typeid', primary_key=True)
    vendor = models.ForeignKey('Vendor', db_column='vendorid')
    name = models.CharField(db_column='typename', max_length=-1)
    sysobjectid = models.CharField(unique=True, max_length=-1)
    cdp = models.BooleanField(default=False)
    tftp = models.BooleanField(default=False)
    cs_at_vlan = models.BooleanField()
    chassis = models.BooleanField(default=True)
    description = models.CharField(db_column='descr', max_length=-1)

    class Meta:
        db_table = 'type'
        unique_together = (('vendor', 'name'),)

    def __unicode__(self):
        return u'%s (%s from %s)' % (self.name, self.description, self.vendor)

#######################################################################
### Device management

class Vendor(models.Model):
    """From MetaNAV: The vendor table defines vendors. A type is of a vendor. A
    product is of a vendor."""

    id = models.CharField(db_column='vendorid', max_length=15, primary_key=True)

    class Meta:
        db_table = 'vendor'

    def __unicode__(self):
        return self.id

#######################################################################
### Router/topology

class GwPortPrefix(models.Model):
    """From MetaNAV: The gwportprefix table defines the router port IP
    addresses, one or more. HSRP is also supported."""

    interface = models.ForeignKey('Interface', db_column='interfaceid')
    prefix = models.ForeignKey('Prefix', db_column='prefixid')
    gw_ip = models.IPAddressField(db_column='gwip', primary_key=True)
    hsrp = models.BooleanField(default=False)

    class Meta:
        db_table = 'gwportprefix'

    def __unicode__(self):
        return self.gw_ip

class Prefix(models.Model):
    """From MetaNAV: The prefix table stores IP prefixes."""

    id = models.AutoField(db_column='prefixid', primary_key=True)
    # TODO: Create CIDRField in Django
    net_address = models.TextField(db_column='netaddr', unique=True)
    vlan = models.ForeignKey('Vlan', db_column='vlanid')

    class Meta:
        db_table = 'prefix'

    def __unicode__(self):
        if self.vlan:
            return u'%s (vlan %s)' % (self.net_address, self.vlan)
        else:
            return self.net_address

    def get_prefix_length(self):
        ip = IPy.IP(self.net_address)
        return ip.prefixlen()

class Vlan(models.Model):
    """From MetaNAV: The vlan table defines the IP broadcast domain / vlan. A
    broadcast domain often has a vlan value, it may consist of many IP
    prefixes, it is of a network type, it is used by an organization (org) and
    has a user group (usage) within the org."""

    id = models.AutoField(db_column='vlanid', primary_key=True)
    vlan = models.IntegerField()
    net_type = models.ForeignKey('NetType', db_column='nettype')
    organization = models.ForeignKey('Organization', db_column='orgid',
        null=True)
    usage = models.ForeignKey('Usage', db_column='usageid', null=True)
    net_ident = models.CharField(db_column='netident', max_length=-1)
    description = models.CharField(max_length=-1)

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
    """From MetaNAV: The nettype table defines network type;lan, core, link,
    elink, loopback, closed, static, reserved, scope. The network types are
    predefined in NAV and may not be altered."""

    id = models.CharField(db_column='nettypeid',
        max_length=-1, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    edit = models.BooleanField(default=False)

    class Meta:
        db_table = 'nettype'

    def __unicode__(self):
        return self.id

class Usage(models.Model):
    """From MetaNAV: The usage table defines the user group (student, staff
    etc). Usage categories are maintained in the edit database tool."""

    id = models.CharField(db_column='usageid',
        max_length=30, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)

    class Meta:
        db_table = 'usage'

    def __unicode__(self):
        return u'%s (%s)' % (self.id, self.description)

class Arp(models.Model):
    """From MetaNAV: The arp table contains (ip, mac, time start, time end)."""

    id = models.AutoField(db_column='arpid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    prefix = models.ForeignKey('Prefix', db_column='prefixid', null=True)
    sysname = models.CharField(max_length=-1)
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
    """From MetaNAV: The swportvlan table defines the vlan values on all switch
    ports. dot1q trunk ports typically have several rows in this table."""

    DIRECTION_UNDEFINED = 'x'
    DIRECTION_UP = 'o'
    DIRECTION_DOWN = 'n'
    DIRECTION_CHOICES = (
        (DIRECTION_UNDEFINED, 'undefined'),
        (DIRECTION_UP, 'up'),
        (DIRECTION_DOWN, 'down'),
    )

    id = models.AutoField(db_column='swportvlanid', primary_key=True)
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    vlan = models.ForeignKey('Vlan', db_column='vlanid')
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES,
        default=DIRECTION_UNDEFINED)

    class Meta:
        db_table = 'swportvlan'
        unique_together = (('swport', 'vlan'),)

    def __unicode__(self):
        return u'%s, on vlan %s' % (self.interface, self.vlan)

class SwPortAllowedVlan(models.Model):
    """From MetaNAV: Stores a hexstring that has “hidden” information about the
    vlans that are allowed to traverse a given trunk."""

    interface = models.OneToOneField('Interface', db_column='interfaceid', primary_key=True)
    hex_string = models.CharField(db_column='hexstring', max_length=-1)

    class Meta:
        db_table = 'swportallowedvlan'

    def __unicode__(self):
        return u'Allowed vlan for swport %s' % self.interface

class SwPortBlocked(models.Model):
    """From MetaNAV: This table defines the spanning tree blocked ports for a
    given vlan for a given switch port."""

    interface = models.ForeignKey('Interface', db_column='interfaceid', primary_key=True)
    # XXX: 'vlan' is not a foreignkey to the vlan table in the database, but
    # it should maybe be a foreign key.
    vlan = models.IntegerField()

    class Meta:
        db_table = 'swportblocked'
        unique_together = (('interface', 'vlan'),) # Primary key

    def __unicode__(self):
        return '%d, at swport %s' % (self.vlan, self.swport)

class SwPortToNetbox(models.Model):
    """From MetaNAV: A help table used in the process of building the physical
    topology of the network. swp_netbox defines the candidates for next hop
    physical neighborship."""

    id = models.AutoField(db_column='swp_netboxid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    ifindex = models.IntegerField()
    to_netbox = models.ForeignKey('Netbox', db_column='to_netboxid',
        related_name='candidate_for_next_hop_set')
    to_interface = models.ForeignKey('Interface', db_column='to_interfaceid', null=True,
        related_name='candidate_for_next_hop_set')
    miss_count = models.IntegerField(db_column='misscnt', default=0)

    class Meta:
        db_table = 'swp_netbox'
        unique_together = (('netbox', 'ifindex', 'to_netbox'),)

    def __unicode__(self):
        return u'%d, %s' % (self.ifindex, self.netbox)

class NetboxVtpVlan(models.Model):
    """From MetaNAV: A help table that contains the vtp vlan database of a
    switch. For certain cisco switches cam information is gathered using a
    community@vlan string. It is then necessary to know all vlans that are
    active on a switch. The vtp vlan table is an extra source of
    information."""

    id = models.AutoField(primary_key=True) # Serial for faking a primary key
    netbox = models.ForeignKey('Netbox', db_column='netboxid')
    vtp_vlan = models.IntegerField(db_column='vtpvlan')

    class Meta:
        db_table = 'netbox_vtpvlan'
        unique_together = (('netbox', 'vtp_vlan'),)

    def __unicode__(self):
        return u'%d, at %s' % (self.vtp_vlan, self.netbox)

class Cam(models.Model):
    """From MetaNAV: The cam table defines (swport, mac, time start, time
    end)"""

    id = models.AutoField(db_column='camid', primary_key=True)
    netbox = models.ForeignKey('Netbox', db_column='netboxid', null=True)
    sysname = models.CharField(max_length=-1)
    ifindex = models.IntegerField()
    module = models.CharField(max_length=4)
    port = models.CharField(max_length=-1)
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
    ifname = models.CharField(max_length=-1)
    ifdescr = models.CharField(max_length=-1)
    iftype = models.IntegerField()
    speed = models.FloatField()
    ifphysaddress = models.CharField(max_length=17, null=True)
    ifadminstatus = models.IntegerField(choices=ADM_STATUS_CHOICES)
    ifoperstatus = models.IntegerField(choices=OPER_STATUS_CHOICES)
    iflastchange = models.IntegerField()
    ifconnectorpresent = models.BooleanField()
    ifpromiscuousmode = models.BooleanField()
    ifalias = models.CharField(max_length=-1)

    baseport = models.IntegerField()
    media = models.CharField(max_length=-1, null=True)
    vlan = models.IntegerField()
    trunk = models.BooleanField()
    duplex = models.CharField(max_length=1, choices=DUPLEX_CHOICES, null=True)

    to_netbox = models.ForeignKey('Netbox', db_column='to_netboxid', null=True,
        related_name='connected_to_interface')
    to_interface = models.ForeignKey('self', db_column='to_interfaceid', null=True,
        related_name='connected_to_interface')

    gone_since = models.DateTimeField()

    class Meta:
        db_table = u'interface'
        ordering = ('baseport', 'ifname')

    def __unicode__(self):
        return u'%s at %s' % (self.ifname, self.netbox)

    def get_absolute_url(self):
        kwargs={
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
        return self.netbox.cam_set.filter(ifindex=self.ifindex).latest(
            'end_time')

    def get_active_time(self, interval):
        """
        Time since last CAM activity on port, looking at CAM entries
        for the last ``interval'' days.

        Returns None if no activity is found, else number of days since last
        activity as a datetime.timedelta object.
        """

        # Create cache dictionary
        # FIXME: Replace with real Django caching
        if not hasattr(self, 'time_since_activity_cache'):
             self.time_since_activity_cache = {}

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

        from nav.models.rrd import RrdDataSource
        return RrdDataSource.objects.filter(
                rrd_file__key='interface', rrd_file__value=str(self.id)
            ).order_by('description')

    def get_link_display(self):
        if self.ifoperstatus == OPER_UP:
            return "Active"
        elif self.ifadminstatus == ADM_DOWN:
            return "Disabled"
        return "Inactive"


class IanaIftype(models.Model):
    """IANA-registered iftype values"""
    iftype = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=-1)
    descr = models.CharField(max_length=-1)

    class Meta:
        db_table = u'iana_iftype'


class RoutingProtocolAttribute(models.Model):
    """Routing protocol metric as configured on a routing interface"""
    id = models.IntegerField(primary_key=True)
    interface = models.ForeignKey('Interface', db_column='interfaceid')
    name = models.CharField(db_column='protoname', max_length=-1)
    metric = models.IntegerField()

    class Meta:
        db_table = u'rproto_attr'

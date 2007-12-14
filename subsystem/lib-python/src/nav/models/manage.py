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

class Location(models.Model):
    id = models.CharField(db_column='locationid',
        max_length=30, primary_key=True)
    descr = models.CharField(max_length=-1)
    class Meta:
        db_table = 'location'

class Room(models.Model):
    id = models.CharField(db_column='roomid', max_length=30, primary_key=True)
    location = models.ForeignKey(Location, db_column='locationid')
    description = models.CharField(db_column='descr', max_length=-1)
    optional_1 = models.CharField(db_column='opt1', max_length=-1)
    optional_2 = models.CharField(db_column='opt2', max_length=-1)
    optional_3 = models.CharField(db_column='opt3', max_length=-1)
    optional_4 = models.CharField(db_column='opt4', max_length=-1)
    class Meta:
        db_table = 'room'

class Vendor(models.Model):
    id = models.CharField(db_column='vendorid', max_length=15, primary_key=True)
    enterpriseid = models.IntegerField()
    class Meta:
        db_table = 'vendor'

class Type(models.Model):
    id = models.IntegerField(db_column='typeid', primary_key=True)
    vendor = models.ForeignKey(Vendor, db_column='vendorid')
    typename = models.CharField(max_length=-1)
    sysobject = models.CharField(db_column='sysobjectid',
        unique=True, max_length=-1)
    cdp = models.BooleanField()
    tftp = models.BooleanField()
    cs_at_vlan = models.BooleanField()
    chassis = models.BooleanField()
    frequency = models.IntegerField()
    descr = models.CharField(max_length=-1)
    class Meta:
        db_table = 'type'

class Product(models.Model):
    id = models.IntegerField(db_column='productid', primary_key=True)
    vendor = models.ForeignKey(Vendor, db_column='vendorid')
    product_number = models.CharField(db_column='productno', max_length=-1)
    description = models.CharField(db_column='descr', max_length=-1)
    class Meta:
        db_table = 'product'

class Organization(models.Model):
    id = models.CharField(db_column='orgid', max_length=30, primary_key=True)
    parent = models.ForeignKey('self', db_column='parent')
    description = models.CharField(db_column='descr', max_length=-1)
    optional_1 = models.CharField(db_column='opt1', max_length=-1)
    optional_2 = models.CharField(db_column='opt2', max_length=-1)
    optional_3 = models.CharField(db_column='opt3', max_length=-1)
    class Meta:
        db_table = 'org'

class DeviceOrder(models.Model):
    id = models.IntegerField(db_column='deviceorderid', primary_key=True)
    registered = models.DateTimeField()
    ordered = models.DateField()
    arrived = models.DateTimeField()
    order_number = models.CharField(db_column='ordernumber', max_length=-1)
    comment = models.CharField(max_length=-1)
    retailer = models.CharField(max_length=-1)
    username = models.CharField(max_length=-1)
    organization = models.ForeignKey(Organization, db_column='orgid')
    product = models.ForeignKey(Product, db_column='productid')
    updated_by = models.CharField(db_column='updatedby', max_length=-1)
    last_updated = models.DateField(db_column='lastupdated')
    class Meta:
        db_table = 'deviceorder'

class Device(models.Model):
    id = models.IntegerField(db_column='deviceid', primary_key=True)
    product = models.ForeignKey(Product, db_column='productid')
    serial = models.CharField(unique=True, max_length=-1)
    hw_ver = models.CharField(max_length=-1)
    fw_ver = models.CharField(max_length=-1)
    sw_ver = models.CharField(max_length=-1)
    auto = models.BooleanField()
    active = models.BooleanField()
    device_order = models.ForeignKey(DeviceOrder, db_column='deviceorderid')
    discovered = models.DateTimeField()
    class Meta:
        db_table = 'device'

class Category(models.Model):
    id = models.CharField(db_column='catid', max_length=8, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    req_snmp = models.BooleanField()
    class Meta:
        db_table = 'cat'

class NetType(models.Model):
    id = models.CharField(db_column='nettypeid',
        max_length=-1, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    edit = models.BooleanField()
    class Meta:
        db_table = 'nettype'

class Usage(models.Model):
    id = models.CharField(db_column='usageid',
        max_length=30, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    class Meta:
        db_table = 'usage'

class Vlan(models.Model):
    id = models.IntegerField(db_column='vlanid', primary_key=True)
    vlan = models.IntegerField()
    net_type = models.ForeignKey(NetType, db_column='nettype')
    organization = models.ForeignKey(Organization, db_column='orgid')
    usage = models.ForeignKey(Usage, db_column='usageid')
    net_ident = models.CharField(db_column='netident', max_length=-1)
    description = models.CharField(max_length=-1)
    class Meta:
        db_table = 'vlan'

class Prefix(models.Model):
    id = models.IntegerField(db_column='prefixid', primary_key=True)
    net_address = models.TextField(db_column='netaddr', unique=True) # FIXME: Create CIDRField
    vlan = models.ForeignKey(Vlan, db_column='vlanid')
    class Meta:
        db_table = 'prefix'

class Netbox(models.Model):
    UP_CHOICES = (
        ('y', 'up'),
        ('n', 'down'),
        ('s', 'shadow'),
    )
    id = models.IntegerField(db_column='netboxid', primary_key=True)
    ip = models.IPAddressField(unique=True)
    room = models.ForeignKey(Room, db_column='roomid')
    type = models.ForeignKey(Type, db_column='typeid')
    device = models.ForeignKey(Device, db_column='deviceid')
    sysname = models.CharField(unique=True, max_length=-1)
    category = models.ForeignKey(Category, db_column='catid')
    subcategory = models.CharField(db_column='subcat', max_length=-1)
    organization = models.ForeignKey(Organization, db_column='orgid')
    read_only = models.CharField(db_column='ro', max_length=-1)
    read_write = models.CharField(db_column='rw', max_length=-1)
    prefix = models.ForeignKey(Prefix, db_column='prefixid')
    up = models.CharField(max_length=1, choices=UP_CHOICES, default='y')
    snmp_version = models.IntegerField()
    snmp_agent = models.CharField(max_length=-1)
    up_since = models.DateTimeField(db_column='upsince')
    up_to_date = models.BooleanField(db_column='uptodate')
    discovered = models.DateTimeField()
    class Meta:
        db_table = 'netbox'

class AlertEngine(models.Model):
    last_alert_queue_id = models.IntegerField(db_column='lastalertqueueid')
    class Meta:
        db_table = 'alertengine'

class Status(models.Model):
    STATEFUL_CHOICES = (
        ('Y', 'stateful'),
        ('N', 'stateless'),
    )
    id = models.IntegerField(db_column='statusid', primary_key=True)
    trap_source = models.CharField(db_column='trapsource', max_length=-1)
    trap = models.CharField(max_length=-1)
    trap_description = models.CharField(db_column='trapdescr', max_length=-1)
    stateful = models.CharField(db_column='tilstandsfull', max_length=1,
        choices=STATEFUL_CHOICES)
    netboxid = models.SmallIntegerField(db_column='boksid')
    from_time = models.DateTimeField(db_column='fra')
    to_time = models.DateTimeField(db_column='til')
    class Meta:
        db_table = 'status'

class NetboxVtpVlan(models.Model):
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    vtp_vlan = models.IntegerField(db_column='vtpvlan')
    class Meta:
        db_table = 'netbox_vtpvlan'

class NetboxInfo(models.Model):
    id = models.IntegerField(db_column='netboxinfoid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    key = models.CharField(max_length=-1)
    var = models.CharField(max_length=-1)
    val = models.TextField()
    class Meta:
        db_table = 'netboxinfo'

class Memory(models.Model):
    id = models.IntegerField(db_column='memid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    type = models.CharField(db_column='memtype', max_length=-1)
    device = models.CharField(max_length=-1)
    size = models.IntegerField()
    used = models.IntegerField()
    class Meta:
        db_table = 'mem'

class Module(models.Model):
    UP_CHOICES = (
        ('y', 'up'),
        ('n', 'down'),
    )
    id = models.IntegerField(db_column='moduleid', primary_key=True)
    device = models.ForeignKey(Device, db_column='deviceid')
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    module_number = models.IntegerField(db_column='module')
    model = models.CharField(max_length=-1)
    description = models.CharField(db_column='descr', max_length=-1)
    up = models.CharField(max_length=1, choices=UP_CHOICES, default='y')
    down_since = models.DateTimeField(db_column='downsince')
    community_suffix = models.CharField(max_length=-1)
    class Meta:
        db_table = 'module'

class SwPort(models.Model):
    LINK_CHOICES = (
        ('y', 'up'), # In old devBrowser: 'Active'
        ('n', 'down (operDown)'), # In old devBrowser: 'Not active'
        ('d', 'down (admDown)'), # In old devBrowser: 'Denied'
    )
    DUPLEX_CHOICES = (
        ('f', 'full duplex'),
        ('h', 'half duplex'),
    )
    id = models.IntegerField(db_column='swportid', primary_key=True)
    module = models.ForeignKey(Module, db_column='moduleid')
    ifindex = models.IntegerField()
    port = models.IntegerField()
    interface = models.CharField(max_length=-1)
    link = models.CharField(max_length=1, choices=LINK_CHOICES)
    speed = models.FloatField()
    duplex = models.CharField(max_length=1, choices=DUPLEX_CHOICES)
    media = models.CharField(max_length=-1)
    vlan = models.IntegerField()
    trunk = models.BooleanField()
    portname = models.CharField(max_length=-1)
    to_netbox = models.ForeignKey(Netbox, db_column='to_netboxid')
    to_swport = models.ForeignKey('self', db_column='to_swportid')
    class Meta:
        db_table = 'swport'

class SwPortAllowedVlan(models.Model):
    swport = models.ForeignKey(SwPort, db_column='swportid')
    hex_string = models.CharField(db_column='hexstring', max_length=-1)
    class Meta:
        db_table = 'swportallowedvlan'

class SwPortBlocked(models.Model):
    swport = models.ForeignKey(SwPort, db_column='swportid')
    vlan = models.IntegerField()
    class Meta:
        db_table = 'swportblocked'

class Cam(models.Model):
    id = models.IntegerField(db_column='camid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    sysname = models.CharField(max_length=-1)
    ifindex = models.IntegerField()
    module = models.CharField(max_length=4)
    port = models.CharField(max_length=-1)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    miss_count = models.IntegerField(db_column='misscnt')
    mac = models.TextField() # This field type is a guess.
    class Meta:
        db_table = 'cam'

class VpNetboxGrpInfo(models.Model):
    id = models.IntegerField(db_column='vp_netbox_grp_infoid', primary_key=True)
    name = models.CharField(max_length=-1)
    hide_icons = models.BooleanField(db_column='hideicons')
    icon_name = models.CharField(db_column='iconname', max_length=-1)
    x = models.IntegerField()
    y = models.IntegerField()
    class Meta:
        db_table = 'vp_netbox_grp_info'

class VpNetboxGrp(models.Model):
    vp_netbox_grp_info = models.ForeignKey(VpNetboxGrpInfo,
        db_column='vp_netbox_grp_infoid')
    pnetboxid = models.IntegerField()
    class Meta:
        db_table = 'vp_netbox_grp'

class VpNetboxXy(models.Model):
    id = models.IntegerField(db_column='vp_netbox_xyid', primary_key=True)
    pnetboxid = models.IntegerField()
    x = models.IntegerField()
    y = models.IntegerField()
    vp_netbox_grp_info = models.ForeignKey(VpNetboxGrpInfo,
        db_column='vp_netbox_grp_infoid')
    class Meta:
        db_table = 'vp_netbox_xy'

class Subsystem(models.Model):
    name = models.CharField(max_length=-1, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    class Meta:
        db_table = 'subsystem'

class RrdFile(models.Model):
    id = models.IntegerField(db_column='rrd_fileid', primary_key=True)
    path = models.CharField(max_length=-1)
    filename = models.CharField(max_length=-1)
    step = models.IntegerField()
    subsystem = models.ForeignKey(Subsystem, db_column='subsystem')
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    key = models.CharField(max_length=-1)
    value = models.CharField(max_length=-1)
    class Meta:
        db_table = 'rrd_file'

class RrdDataSource(models.Model):
    TYPE_CHOICES = (
        ('GAUGE', 'gauge'),
        ('DERIVE', 'derive'),
        ('COUNTER', 'counter'),
        ('ABSOLUTE', 'absolute'),
    )
    DELIMITER_CHOICES = (
        ('>', 'greater than'),
        ('<', 'less than'),
    )
    TRESHOLD_STATE_CHOICES = (
        ('active', 'active'),
        ('inactive', 'inactive'),
    )
    id = models.IntegerField(db_column='rrd_datasourceid', primary_key=True)
    rrd_file = models.ForeignKey(RrdFile, db_column='rrd_fileid')
    name = models.CharField(max_length=-1)
    description = models.CharField(db_column='descr', max_length=-1)
    type = models.CharField(db_column='dstype', max_length=-1,
        choices=TYPE_CHOICES)
    units = models.CharField(max_length=-1)
    threshold = models.CharField(max_length=-1)
    max = models.CharField(max_length=-1)
    delimiter = models.CharField(max_length=1, choices=DELIMITER_CHOICES)
    threshold_state = models.CharField(db_column='thresholdstate',
        max_length=-1, choices=TRESHOLD_STATE_CHOICES)
    class Meta:
        db_table = 'rrd_datasource'

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

class EventQueue(models.Model):
    STATE_CHOICES = (
        ('x', 'stateless'),
        ('s', 'start'),
        ('e', 'end'),
    )
    id = models.IntegerField(db_column='eventqid', primary_key=True)
    source = models.ForeignKey(Subsystem, db_column='source',
        related_name='source_of_events')
    target = models.ForeignKey(Subsystem, db_column='target',
        related_name='target_of_events')
    device = models.ForeignKey(Device, db_column='deviceid')
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    subid = models.CharField(max_length=-1)
    time = models.DateTimeField()
    event_type = models.ForeignKey(EventType, db_column='eventtypeid')
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='x')
    value = models.IntegerField(default=100)
    severity = models.IntegerField(default=50)
    class Meta:
        db_table = 'eventq'

class EventQueueVar(models.Model):
    event_queue = models.ForeignKey(EventQueue, db_column='eventqid',
        related_name='variables')
    variable = models.CharField(db_column='var', max_length=-1)
    value = models.TextField(db_column='val')
    class Meta:
        db_table = 'eventqvar'

class AlertType(models.Model):
    id = models.IntegerField(db_column='alerttypeid', primary_key=True)
    event_type = models.ForeignKey(EventType, db_column='eventtypeid')
    name = models.CharField(db_column='alterttype', max_length=-1)
    description= models.CharField(db_column='alerttypedesc', max_length=-1)
    class Meta:
        db_table = 'alerttype'

class AlertQueue(models.Model):
    id = models.IntegerField(db_column='alertqid', primary_key=True)
    source = models.ForeignKey(Subsystem, db_column='source')
    device = models.ForeignKey(Device, db_column='deviceid')
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    subid = models.CharField(max_length=-1)
    time = models.DateTimeField()
    event_type = models.ForeignKey(EventType, db_column='eventtypeid')
    alert_type = models.ForeignKey(AlertType, db_column='alerttypeid')
    state = models.CharField(max_length=1) # FIXME: Add choices
    value = models.IntegerField()
    severity = models.IntegerField()
    class Meta:
        db_table = 'alertq'

class AlertQueueMessage(models.Model):
    alert_queue = models.ForeignKey(AlertQueue, db_column='alertqid',
        related_name='messages')
    type = models.CharField(db_column='msgtype', max_length=-1)
    language = models.CharField(max_length=-1)
    message = models.TextField(db_column='msg')
    class Meta:
        db_table = 'alertqmsg'

class AlertQueueVariable(models.Model):
    alert_queue = models.ForeignKey(AlertQueue, db_column='alertqid',
        related_name='variables')
    variable = models.CharField(db_column='var', max_length=-1)
    value = models.TextField(db_column='val')
    class Meta:
        db_table = 'alertqvar'

class AlertHistory(models.Model):
    id = models.IntegerField(db_column='alerthistid', primary_key=True)
    source = models.ForeignKey(Subsystem, db_column='source')
    device = models.ForeignKey(Device, db_column='deviceid')
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    subid = models.CharField(max_length=-1)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event_type = models.ForeignKey(EventType, db_column='eventtypeid')
    alert_type = models.ForeignKey(AlertType, db_column='alerttypeid')
    value = models.IntegerField()
    severity = models.IntegerField()
    class Meta:
        db_table = 'alerthist'

class AlertHistoryMessage(models.Model):
    alert_history = models.ForeignKey(AlertHistory, db_column='alerthistid',
        related_name='messages')
    state = models.CharField(max_length=1) # FIXME: Add choices
    type = models.CharField(db_column='msgtype', max_length=-1)
    language = models.CharField(max_length=-1)
    message = models.TextField(db_column='msg')
    class Meta:
        db_table = 'alerthistmsg'

class AlertHistoryVariable(models.Model):
    alert_history = models.ForeignKey(AlertHistory, db_column='alerthistid')
    state = models.CharField(max_length=1) # FIXME: Add choices
    variable = models.CharField(db_column='var', max_length=-1)
    value = models.TextField(db_column='val')
    class Meta:
        db_table = 'alerthistvar'
        unique_together = (('alert_history', 'state', 'variable'),)

class Service(models.Model):
    UP_CHOICES = (
        ('y', 'up'),
        ('n', 'down'),
        ('s', 'shadow'),
    )
    id = models.IntegerField(db_column='serviceid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    active = models.BooleanField()
    handler = models.CharField(max_length=-1)
    version = models.CharField(max_length=-1)
    up = models.CharField(max_length=1, choices=UP_CHOICES, default='y')
    class Meta:
        db_table = 'service'

class ServiceProperty(models.Model):
    service = models.ForeignKey(Service, db_column='serviceid')
    property = models.CharField(max_length=64)
    value = models.CharField(max_length=-1)
    class Meta:
        db_table = 'serviceproperty'

class MaintenanceTask(models.Model):
    id = models.IntegerField(db_column='maint_taskid', primary_key=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField()
    author = models.CharField(max_length=-1)
    state = models.CharField(max_length=-1)
    class Meta:
        db_table = 'maint_task'

class MaintenanceComponent(models.Model):
    maint_task = models.ForeignKey(MaintenanceTask, db_column='maint_taskid')
    key = models.CharField(max_length=-1)
    value = models.CharField(max_length=-1)
    class Meta:
        db_table = 'maint_component'

class SnmpOid(models.Model):
    id = models.IntegerField(db_column='snmpoidid', primary_key=True)
    oid_key = models.CharField(db_column='oidkey', unique=True, max_length=-1)
    snmp_oid = models.CharField(db_column='snmpoid', max_length=-1)
    oid_source = models.CharField(db_column='oidsource', max_length=-1)
    get_next = models.BooleanField(db_column='getnext')
    decode_hex = models.BooleanField(db_column='decodehex')
    match_regex = models.CharField(max_length=-1)
    default_frequency = models.IntegerField(db_column='defaultfreq')
    up_to_date = models.BooleanField(db_column='uptodate')
    description = models.CharField(db_column='descr', max_length=-1)
    oid_name = models.CharField(db_column='oidname', max_length=-1)
    mib = models.CharField(max_length=-1)
    class Meta:
        db_table = 'snmpoid'

class NetboxSnmpOid(models.Model):
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    snmp_oid = models.ForeignKey(SnmpOid, db_column='snmpoidid')
    frequency = models.IntegerField()
    class Meta:
        db_table = 'netboxsnmpoid'

class Subcategory(models.Model):
    id = models.CharField(db_column='subcatid', max_length=-1, primary_key=True)
    description = models.CharField(db_column='descr', max_length=-1)
    category = models.ForeignKey(Category, db_column='catid')
    class Meta:
        db_table = 'subcat'

class NetboxCategory(models.Model):
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    category = models.ForeignKey(Subcategory, db_column='category')
    class Meta:
        db_table = 'netboxcategory'

class GwPort(models.Model):
    LINK_CHOICES = (
        ('y', 'up'), # In old devBrowser: 'Active'
        ('n', 'down (operDown)'), # In old devBrowser: 'Not active'
        ('d', 'down (admDown)'), # In old devBrowser: 'Denied'
    )
    id = models.IntegerField(db_column='gwportid', primary_key=True)
    module = models.ForeignKey(Module, db_column='moduleid')
    ifindex = models.IntegerField()
    link = models.CharField(max_length=1, choices=LINK_CHOICES)
    master_index = models.IntegerField(db_column='masterindex')
    interface = models.CharField(max_length=-1)
    speed = models.FloatField()
    metric = models.IntegerField()
    to_netbox = models.ForeignKey(Netbox, db_column='to_netboxid')
    to_swport = models.ForeignKey(SwPort, db_column='to_swportid')
    port_name = models.CharField(db_column='portname', max_length=-1)
    class Meta:
        db_table = 'gwport'

class GwPortPrefix(models.Model):
    gwport = models.ForeignKey(GwPort, db_column='gwportid')
    prefix = models.ForeignKey(Prefix, db_column='prefixid')
    gw_ip = models.IPAddressField(db_column='gwip', unique=True)
    hsrp = models.BooleanField()
    class Meta:
        db_table = 'gwportprefix'

class SwPortVlan(models.Model):
    DIRECTION_CHOICES = (
        ('u', 'undefined'),
        ('o', 'up'),
        ('d', 'down'),
        ('b', 'both'),
        ('x', 'crossed'),
    )
    id = models.IntegerField(db_column='swportvlanid', primary_key=True)
    swport = models.ForeignKey(SwPort, db_column='swportid')
    vlan = models.ForeignKey(Vlan, db_column='vlanid')
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES,
        default='x')
    class Meta:
        db_table = 'swportvlan'

class Cabling(models.Model):
    id = models.IntegerField(db_column='cablingid', primary_key=True)
    room = models.ForeignKey(Room, db_column='roomid')
    jack = models.CharField(max_length=-1)
    building = models.CharField(max_length=-1)
    target_room = models.CharField(db_column='targetroom', max_length=-1)
    description = models.CharField(db_column='descr', max_length=-1)
    category = models.CharField(max_length=-1)
    class Meta:
        db_table = 'cabling'

class Patch(models.Model):
    id = models.IntegerField(db_column='patchid', primary_key=True)
    swport = models.ForeignKey(SwPort, db_column='swportid')
    cabling = models.ForeignKey(Cabling, db_column='cablingid')
    split = models.CharField(max_length=-1)
    class Meta:
        db_table = 'patch'

class Arp(models.Model):
    id = models.IntegerField(db_column='arpid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    prefix = models.ForeignKey(Prefix, db_column='prefixid')
    sysname = models.CharField(max_length=-1)
    ip = models.IPAddressField()
    mac = models.TextField() # FIXME: Create MACAddressField
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    class Meta:
        db_table = 'arp'

class Message(models.Model):
    id = models.IntegerField(db_column='messageid', primary_key=True)
    title = models.CharField(max_length=-1)
    description = models.TextField()
    tech_description = models.TextField()
    publish_start = models.DateTimeField()
    publish_end = models.DateTimeField()
    author = models.CharField(max_length=-1)
    last_changed = models.DateTimeField()
    replaces_message = models.ForeignKey('self', db_column='replaces_message',
        related_name='replaced_by')
    class Meta:
        db_table = 'message'

class MessageToMaintenanceTask(models.Model):
    message = models.ForeignKey(Message, db_column='messageid',
        related_name='maintenance_tasks')
    maintenance_task = models.ForeignKey(MaintenanceTask,
        db_column='maint_taskid', related_name='messages')
    class Meta:
        db_table = 'message_to_maint_task'

class SwPortToNetbox(models.Model):
    id = models.IntegerField(db_column='swp_netboxid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    ifindex = models.IntegerField()
    to_netbox = models.ForeignKey(Netbox, db_column='to_netboxid',
        related_name='candidate_for_next_hop_set')
    to_swport = models.ForeignKey(SwPort, db_column='to_swportid',
        related_name='candidate_for_next_hop_set')
    miss_count = models.IntegerField(db_column='misscnt')
    class Meta:
        db_table = 'swp_netbox'


#
# Copyright (C) 2012 (SD -311000) UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from nav.models.fields import VarcharField
from nav.models.manage import Interface, Organization
from django.db import models

STATUSES = (
    ('enabled',),
    ('disabled',),
    ('quarantined',)
    )

class Identity(models.Model):
    """
    The table contains a listing for each computer,interface combo Arnold
    has blocked
    """

    id = models.AutoField(db_column='identityid', primary_key=True)
    mac = models.CharField(db_column='mac', max_length=17)
    status = VarcharField(db_column='blocked_status', choices=STATUSES)
    justification = models.ForeignKey('Justification', db_column='blocked_reasonid')
    interface = models.ForeignKey(Interface, db_column='swportid')
    ip = models.IPAddressField(null=True)
    dns = VarcharField(null=True)
    netbios = VarcharField(null=True)
    first_offence = models.DateTimeField(db_column='starttime')
    last_changed = models.DateTimeField(db_column='lastchanged', auto_now_add=True)
    autoenable = models.DateTimeField(null=True)
    autoenablestep = models.IntegerField(null=True)
    mail = VarcharField(null=True)
    organization = models.ForeignKey('Organization', db_column='orgid', null=True)
    keep_closed = models.CharField(db_column='determined', default='n')
    fromvlan = models.IntegerField(null=True)
    tovlan = models.IntegerField(null=True)

    class Meta:
        db_table = 'identity'
        ordering = ('last_changed', )
        verbose_name = 'identity'
        verbose_name_plural = 'identities'
        unique_together = ('mac', 'interface')


class Event(models.Model):
    """A class representing an action taken"""
    id = models.AutoField(db_column='eventid', primary_key=True)
    identity = models.ForeignKey('Identity', db_column='identityid')
    comment = VarcharField(db_column='event_comment', null=True)
    action = VarcharField(db_column='blocked_status', choices=STATUSES)
    justification = models.ForeignKey('Justification', db_column='blocked_reasonid')
    event_time = models.DateTimeField(db_column='eventtime', auto_now_add=True)
    autoenablestep = models.IntegerField(null=True)
    executor = VarcharField(db_column='username')

    class Meta:
        db_table = 'event'
        ordering = ('event_time', )


class Justification(models.Model):
    """Represents the justification for an event"""
    id = models.AutoField(db_column='blocked_reasonid', primary_key=True)
    name = VarcharField()
    description = VarcharField(db_column='comment', null=True)

    class Meta:
        db_table = 'blocked_reason'
        ordering = ('name', )


class QuarantineVlan(models.Model):
    """A quarantine vlan is a vlan where offender are placed"""
    id = models.AutoField(db_column='quarantineid', primary_key=True)
    vlan = models.IntegerField()
    description = VarcharField(null=True)

    class Meta:
        db_table = 'quarantine_vlans'
        ordering = ('vlan',)


class DetentionType(models.Model):
    """A detentiontype is a configuration of an automatic detention"""
    detention_types = ['disable', 'quarantine']

    id = models.AutoField(db_column='blockid', primary_key=True)
    name = VarcharField(db_column='blocktitle')
    description = VarcharField(db_column='blockdesc', null=True)
    mailfile = VarcharField(null=True)
    justification = models.ForeignKey('Justification', db_column='reasonid')
    keep_closed = models.CharField(db_column='determined', default='n')
    incremental = models.CharField(default='n')
    autoenable_time = models.DateTimeField(db_column='blocktime')
    active = models.CharField(default='n')
    last_edited = models.DateTimeField(db_column='lastedited', auto_now_add=True)
    edited_by = VarcharField(db_column='lastedituser')
    inputfile = VarcharField()
    active_on_vlans = VarcharField(db_column='activeonvlans')
    detention_type = VarcharField(db_column='detainmenttype', choices=detention_types)
    quarantine_vlan = models.ForeignKey('QuarantineVlan', db_column='quarantineid')

    class Meta:
        db_table = 'block'
        ordering = ('name', )

#
# Copyright (C) 2012 (SD -311000) Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Model definitions for arnold"""

from django.db import models

from nav.models.fields import VarcharField
from nav.models.manage import Interface

STATUSES = [
    ('enabled', 'Enabled'),
    ('disabled', 'Disabled'),
    ('quarantined', 'Quarantined'),
]

DETENTION_TYPE_CHOICES = [('disable', 'Block'), ('quarantine', 'Quarantine')]

KEEP_CLOSED_CHOICES = [('n', 'Open on move'), ('y', 'All closed')]


class Identity(models.Model):
    """
    The table contains a listing for each computer,interface combo Arnold
    has blocked.
    """

    id = models.AutoField(db_column='identityid', primary_key=True)
    mac = models.CharField(db_column='mac', max_length=17)
    status = VarcharField(db_column='blocked_status', choices=STATUSES)
    justification = models.ForeignKey(
        'Justification',
        on_delete=models.CASCADE,
        db_column='blocked_reasonid',
        related_name="identities",
    )
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        db_column='swportid',
        related_name="arnold_identities",
    )
    ip = models.GenericIPAddressField(null=True, default='0.0.0.0')
    dns = VarcharField(blank=True)
    netbios = VarcharField(blank=True)
    first_offence = models.DateTimeField(db_column='starttime', auto_now_add=True)
    last_changed = models.DateTimeField(db_column='lastchanged', auto_now=True)
    autoenable = models.DateTimeField(null=True)
    autoenablestep = models.IntegerField(null=True, default=2)
    mail = VarcharField(blank=True)
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        db_column='orgid',
        null=True,
        related_name="arnold_identities",
    )
    keep_closed = models.CharField(
        db_column='determined', default='n', choices=KEEP_CLOSED_CHOICES, max_length=1
    )
    fromvlan = models.IntegerField(null=True)
    tovlan = models.ForeignKey(
        'QuarantineVlan',
        on_delete=models.CASCADE,
        db_column='tovlan',
        to_field='vlan',
        null=True,
        default=None,
        related_name="identities",
    )
    # If the interface does not exist any longer in the database, the user
    # needs a hint of what interface was blocked as information as ifname
    # and netbox naturally no longer exists based on interfaceid.
    # This fields solves this by storing the textual representation of the
    # interface, that can be displayed if the situation occurs.
    # The format is "interface.ifname at interface.netbox.sysname"
    textual_interface = VarcharField(default='')

    def __str__(self):
        try:
            interface = self.interface
        except Interface.DoesNotExist:
            interface = "N/A"
        return "%s/%s %s" % (self.ip, self.mac, interface)

    class Meta(object):
        db_table = 'identity'
        ordering = ('last_changed',)
        verbose_name = 'identity'
        verbose_name_plural = 'identities'
        unique_together = ('mac', 'interface')


class Event(models.Model):
    """A class representing an action taken"""

    id = models.AutoField(db_column='eventid', primary_key=True)
    identity = models.ForeignKey(
        'Identity',
        on_delete=models.CASCADE,
        db_column='identityid',
        related_name="events",
    )
    comment = VarcharField(db_column='event_comment', blank=True)
    action = VarcharField(db_column='blocked_status', choices=STATUSES)
    justification = models.ForeignKey(
        'Justification',
        on_delete=models.CASCADE,
        db_column='blocked_reasonid',
        related_name="events",
    )
    event_time = models.DateTimeField(db_column='eventtime', auto_now_add=True)
    autoenablestep = models.IntegerField(null=True)
    executor = VarcharField(db_column='username')

    def __str__(self):
        return "%s: %s" % (self.action, self.event_time)

    class Meta(object):
        db_table = 'event'
        ordering = ('event_time',)


class Justification(models.Model):
    """Represents the justification for an event"""

    id = models.AutoField(db_column='blocked_reasonid', primary_key=True)
    name = VarcharField()
    description = VarcharField(db_column='comment', blank=True)

    def __str__(self):
        return self.name

    class Meta(object):
        db_table = 'blocked_reason'
        ordering = ('name',)


class QuarantineVlan(models.Model):
    """A quarantine vlan is a vlan where offenders are placed"""

    id = models.AutoField(db_column='quarantineid', primary_key=True)
    vlan = models.IntegerField(unique=True)
    description = VarcharField(blank=True)

    def __str__(self):
        return "%s - %s" % (self.vlan, self.description)

    class Meta(object):
        db_table = 'quarantine_vlans'
        ordering = ('vlan',)


class DetentionProfile(models.Model):
    """A detention profile is a configuration used by an automatic detention"""

    id = models.AutoField(db_column='blockid', primary_key=True)
    name = VarcharField(db_column='blocktitle')
    description = VarcharField(db_column='blockdesc', blank=True)
    mailfile = VarcharField(blank=True)
    justification = models.ForeignKey(
        'Justification',
        on_delete=models.CASCADE,
        db_column='reasonid',
        related_name="detention_profiles",
    )
    keep_closed = models.CharField(
        db_column='determined', default='n', choices=KEEP_CLOSED_CHOICES, max_length=1
    )
    incremental = models.CharField(default='n', max_length=1)
    duration = models.IntegerField(db_column='blocktime')
    active = models.CharField(default='n', max_length=1)
    last_edited = models.DateTimeField(db_column='lastedited', auto_now_add=True)
    edited_by = VarcharField(db_column='lastedituser')
    inputfile = VarcharField(blank=True)
    active_on_vlans = VarcharField(db_column='activeonvlans')
    detention_type = VarcharField(
        db_column='detainmenttype', choices=DETENTION_TYPE_CHOICES
    )
    quarantine_vlan = models.ForeignKey(
        'QuarantineVlan',
        on_delete=models.CASCADE,
        db_column='quarantineid',
        null=True,
        related_name="detention_profiles",
    )

    def __str__(self):
        return self.name

    class Meta(object):
        db_table = 'block'
        ordering = ('name',)

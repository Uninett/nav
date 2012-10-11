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

from django.db import models
from nav.models.fields import VarcharField
from nav.models.manage import Interface

STATUSES = (
    ('enabled',),
    ('disabled',),
    ('quarantined',)
    )

class Computer(models.Model):
    """The table contains a listing for each computer Arnold has blocked"""

    id = models.AutoField(db_column='identityid', primary_key=True)
    ip = models.IPAddressField(db_column='ip', null=True)
    mac = models.CharField(db_column='mac', max_length=17)
    dns = VarcharField(null=True)
    netbios = VarcharField(null=True)
    status = models.ForeignKey('Status')

    class Meta:
        db_table = 'identity'
        verbose_name = 'identity'
        verbose_name_plural = 'identities'
        ordering = ('', )



class Status(models.Model):
    id = models.AutoField(primary_key=True)
    name = VarcharField()
    description = VarcharField()


class Event(models.Model):
    """A class representing an action taken"""
    id = models.AutoField(primary_key=True)
    justification = models.ForeignKey('Justification', db_column='blocked_reasonid')
    interface = models.ForeignKey(Interface, db_column='swportid')
    event_time = models.DateTimeField(auto_now_add=True)
    action = VarcharField(choices=STATUSES)
    identity = models.ForeignKey('Identity')
    mail = VarcharField(null=True)
    fromvlan = models.IntegerField(null=True)
    tovlan = models.IntegerField(null=True)

    class Meta:
        db_table = 'action'


class Justification(models.Model):
    id = models.AutoField(db_column='blocked_reasonid', primary_key=True)
    name = VarcharField(db_column='name'),
    description = VarcharField(db_column='comment', null=True)

    class Meta:
        db_table = 'blocked_reason'
        ordering = ('name', )


class QuarantineVlan(models.Model):
    id = models.AutoField(db_column='quarantineid', primary_key=True)
    vlan = models.IntegerField(db_column='vlan')
    description = VarcharField(db_column='description', null=True)

    class Meta:
        db_table = 'quarantine_vlans'
        ordering = ('vlan',)


class DetentionType(models.Model):
    id = models.AutoField(db_column='blockid', primary_key=True)
    name = VarcharField(db_column='blocktitle')
    description = VarcharField(db_column='blockdesc', null=True)

    class Meta:
        db_table = 'block'
        ordering = ('name', )

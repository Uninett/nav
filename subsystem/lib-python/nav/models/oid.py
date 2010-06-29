# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 UNINETT AS
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

from django.db import models

from nav.models.manage import Netbox

class SnmpOid(models.Model):
    """From MetaNAV: The snmpoid table defines all OIDs used during snmp data
    gathering and/or Cricket data collection."""

    id = models.AutoField(db_column='snmpoidid', primary_key=True)
    oid_key = models.CharField(db_column='oidkey', unique=True, max_length=-1)
    snmp_oid = models.CharField(db_column='snmpoid', max_length=-1)
    oid_source = models.CharField(db_column='oidsource', max_length=-1)
    get_next = models.BooleanField(db_column='getnext', default=True)
    decode_hex = models.BooleanField(db_column='decodehex', default=False)
    match_regex = models.CharField(max_length=-1)
    default_frequency = models.IntegerField(db_column='defaultfreq',
        default=21600)
    up_to_date = models.BooleanField(db_column='uptodate', default=False)
    description = models.CharField(db_column='descr', max_length=-1)
    oid_name = models.CharField(db_column='oidname', max_length=-1)
    mib = models.CharField(max_length=-1)

    class Meta:
        db_table = 'snmpoid'

    def __unicode__(self):
        return u'%s, at OID %s' % (self.oid_key, self.snmp_oid)

class NetboxSnmpOid(models.Model):
    """From MetaNAV: The netboxsnmpoid table defines which netboxes answers to
    which snmpoids."""

    id = models.AutoField(primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    snmp_oid = models.ForeignKey(SnmpOid, db_column='snmpoidid')
    frequency = models.IntegerField()

    class Meta:
        db_table = 'netboxsnmpoid'
        unique_together = (('netbox', 'snmp_oid'),)

    def __unicode__(self):
        return u'%s, answers to %s' % (self.netbox, self.snmp_oid)

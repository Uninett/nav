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

from nav.models.event import Subsystem
from nav.models.manage import Netbox

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

# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2011 UNINETT AS
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
from django.core.urlresolvers import reverse

from nav.models.event import Subsystem
from nav.models.manage import Netbox
from nav.models.fields import VarcharField

class RrdFile(models.Model):
    """From MetaNAV: The rrd_file contains meta information on all RRD files
    that NAV uses. Each RRD file has statistics for a certain netbox."""

    id = models.AutoField(db_column='rrd_fileid', primary_key=True)
    path = VarcharField()
    filename = VarcharField()
    step = models.IntegerField()
    subsystem = models.ForeignKey(Subsystem, db_column='subsystem')
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    key = VarcharField()
    value = VarcharField()

    class Meta:
        db_table = 'rrd_file'

    def __unicode__(self):
        return u'%s/%s' % (self.path, self.filename)

    def get_file_path(self):
        return u'%s/%s' % (self.path, self.filename)

class RrdDataSource(models.Model):
    """From MetaNAV: An rrd_file consists of a set of data sources defined in
    this table. A data source is a data set, i.e. outOctets for a given switch
    port on a given switch."""

    TYPE_GAUGE = 'GAUGE'
    TYPE_DERIVE = 'DERIVE'
    TYPE_COUNTER = 'COUNTER'
    TYPE_ABSOLUTE = 'ABSOLUTE'
    TYPE_CHOICES = (
        (TYPE_GAUGE, 'gauge'),
        (TYPE_DERIVE, 'derive'),
        (TYPE_COUNTER, 'counter'),
        (TYPE_ABSOLUTE, 'absolute'),
    )
    DELIMITER_GT = '>'
    DELIMITER_LT = '<'
    DELIMITER_CHOICES = (
        (DELIMITER_GT, 'greater than'),
        (DELIMITER_LT, 'less than'),
    )
    TRESHOLD_STATE_ACTIVE = 'active'
    TRESHOLD_STATE_INACTIVE = 'inactive'
    TRESHOLD_STATE_CHOICES = (
        (TRESHOLD_STATE_ACTIVE, 'active'),
        (TRESHOLD_STATE_INACTIVE, 'inactive'),
    )

    id = models.AutoField(db_column='rrd_datasourceid', primary_key=True)
    rrd_file = models.ForeignKey(RrdFile, db_column='rrd_fileid')
    name = VarcharField()
    description = VarcharField(db_column='descr')
    type = VarcharField(db_column='dstype', choices=TYPE_CHOICES)
    units = VarcharField()
    threshold = VarcharField()
    max = VarcharField()
    delimiter = models.CharField(max_length=1, choices=DELIMITER_CHOICES)
    threshold_state = VarcharField(db_column='thresholdstate',
                                   choices=TRESHOLD_STATE_CHOICES)

    class Meta:
        db_table = 'rrd_datasource'

    def __unicode__(self):
        return u'%s (%s), for RRD file %s' % (
            self.name, self.description, self.rrd_file)

    def get_absolute_url(self):
        return reverse('rrdviewer-rrd-by-ds', kwargs={
            'rrddatasource_id': self.id,
        })

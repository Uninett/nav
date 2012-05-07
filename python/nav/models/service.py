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

from nav.models.manage import Netbox
from nav.models.fields import VarcharField

class Service(models.Model):
    """From NAV Wiki: The service table defines the services on a netbox that
    serviceMon monitors."""

    UP_UP = 'y'
    UP_DOWN = 'n'
    UP_SHADOW = 's'
    UP_CHOICES = (
        (UP_UP, 'up'),
        (UP_DOWN, 'down'),
        (UP_SHADOW, 'shadow'),
    )
    TIME_FRAMES = ('day', 'week', 'month')

    id = models.AutoField(db_column='serviceid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    active = models.BooleanField(default=True)
    handler = VarcharField(verbose_name='service')
    version = VarcharField()
    up = models.CharField(max_length=1, choices=UP_CHOICES, default=UP_UP)

    class Meta:
        db_table = 'service'
        ordering = ('handler',)

    def __unicode__(self):
        return u'%s, at %s' % (self.handler, self.netbox)

    def get_statistics(self):
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
                rrd_file__key='serviceid', rrd_file__value=str(self.id))
            data_source_status = None
            data_source_response_time = None
            for ds in data_sources:
                if ds.name == 'STATUS':
                    data_source_status = ds
                if ds.name == 'RESPONSETIME':
                    data_source_response_time = ds
        except RrdDataSource.DoesNotExist:
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

class ServiceProperty(models.Model):
    """From NAV Wiki: Each service may have an additional set of attributes.
    They are defined here."""

    id = models.AutoField(primary_key=True) # Serial for faking a primary key
    service = models.ForeignKey(Service, db_column='serviceid')
    property = models.CharField(max_length=64)
    value = VarcharField()

    class Meta:
        db_table = 'serviceproperty'
        unique_together = (('service', 'property'),) # Primary key

    def __unicode__(self):
        return u'%s=%s, for %s' % (self.property, self.value, self.service)

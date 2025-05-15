# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2011-2015 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
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

from nav.metrics.data import get_metric_average
from nav.metrics.templates import (
    metric_path_for_service_availability,
    metric_path_for_service_response_time,
)

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
    netbox = models.ForeignKey(
        Netbox,
        on_delete=models.CASCADE,
        db_column='netboxid',
        related_name="services",
    )
    active = models.BooleanField(default=True)
    handler = VarcharField(verbose_name='service')
    version = VarcharField()
    up = models.CharField(max_length=1, choices=UP_CHOICES, default=UP_UP)

    class Meta(object):
        db_table = 'service'
        ordering = ('handler',)

    def __str__(self):
        return "{handler} at {netbox}".format(handler=self.handler, netbox=self.netbox)

    def get_statistics(self):
        args = (self.netbox.sysname, self.handler, self.id)
        avail_id = metric_path_for_service_availability(*args)
        rtime_id = metric_path_for_service_response_time(*args)

        result = {
            'availability': {
                'data_source': avail_id,
            },
            'response_time': {
                'data_source': rtime_id,
            },
        }

        for time_frame in self.TIME_FRAMES:
            avg = get_metric_average([avail_id, rtime_id], start="-1%s" % time_frame)

            # Availability
            pktloss = avg.get(avail_id, None)
            if pktloss is not None:
                pktloss = 100 - (pktloss * 100)
            result['availability'][time_frame] = pktloss

            # Response time
            result['response_time'][time_frame] = avg.get(rtime_id, None)

        return result

    def is_on_maintenance(self):
        """
        Returns True if this service, or its owning Netbox, is currently on
        maintenance.
        """
        states = self.netbox.get_unresolved_alerts('maintenanceState').filter(
            variables__variable='service', subid=self.id
        )
        if states.count() < 1:
            return self.netbox.is_on_maintenance()
        else:
            return True

    def last_downtime_ended(self):
        """
        Returns the end_time of the last known serviceState alert.

        :returns: A datetime object if a serviceState alert was found,
                  otherwise None
        """
        try:
            lastdown = self.netbox.alert_history_set.filter(
                event_type__id='serviceState', end_time__isnull=False
            ).order_by("-end_time")[0]
        except IndexError:
            return
        else:
            return lastdown.end_time

    def get_handler_description(self):
        """Returns the description of the handler

        The description is defined in the service checker
        """
        classname = "{}Checker".format(str(self.handler).capitalize())
        modulename = "nav.statemon.checker.{}".format(classname)
        checker = __import__(modulename, globals(), locals(), [classname], 0)
        klass = getattr(checker, classname)
        return getattr(klass, 'DESCRIPTION', '')

    description = property(get_handler_description)


class ServiceProperty(models.Model):
    """From NAV Wiki: Each service may have an additional set of attributes.
    They are defined here."""

    id = models.AutoField(primary_key=True)  # Serial for faking a primary key
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        db_column='serviceid',
        related_name="properties",
    )
    property = models.CharField(max_length=64)
    value = VarcharField()

    class Meta(object):
        db_table = 'serviceproperty'
        unique_together = (('service', 'property'),)  # Primary key

    def __str__(self):
        return '%s=%s, for %s' % (self.property, self.value, self.service)

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

from django.db import models

from nav.models.manage import Netbox

class Service(models.Model):
    """From MetaNAV: The service table defines the services on a netbox that
    serviceMon monitors."""

    UP_UP = 'y'
    UP_DOWN = 'n'
    UP_SHADOW = 's'
    UP_CHOICES = (
        (UP_UP, 'up'),
        (UP_DOWN, 'down'),
        (UP_SHADOW, 'shadow'),
    )
    id = models.IntegerField(db_column='serviceid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    active = models.BooleanField(default=True)
    handler = models.CharField(max_length=-1)
    version = models.CharField(max_length=-1)
    up = models.CharField(max_length=1, choices=UP_CHOICES, default=UP_UP)
    class Meta:
        db_table = 'service'

class ServiceProperty(models.Model):
    """From MetaNAV: Each service may have an additional set of attributes.
    They are defined here."""

    service = models.ForeignKey(Service, db_column='serviceid')
    property = models.CharField(max_length=64)
    value = models.CharField(max_length=-1)
    class Meta:
        db_table = 'serviceproperty'
        unique_together = (('service', 'property'),) # Primary key

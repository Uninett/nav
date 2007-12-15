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

from nav.models.manage import Netbox

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

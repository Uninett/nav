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

class Sensor(models.Model):
    """
    This table contains meta-data about available sensors in
    network-equipment.

    Information in this table is used to make configurations for
    Cricket,- and Cricket maintain the resulting RRD-files for
    statistics.
    """

    id = models.AutoField(db_column='sensor_id', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    oid = VarcharField(db_column="oid")
    unit_of_measurement = VarcharField(db_column="unit_of_measurement")
    data_scale = VarcharField(db_column="data_scale")
    human_readable = VarcharField(db_column="human_readable")

    class Meta:
        db_table = 'sensor'

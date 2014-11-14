#
# Copyright (C) 2014 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Template tags specifically tailored for sensor manipulation"""

from django import template
from nav.models.manage import Sensor

register = template.Library()


@register.filter
def get_graph_url(obj, time_frame):
    return obj.get_graph_url(time_frame=time_frame)


@register.filter
def get_sensor(netbox, internal_name):
    """
    Return the sensor that matches the filter

    :param netbox: An instance of a netbox
    :type netbox: nav.models.manage.Netbox
    :param internal_name: filter based on internal name
    :type internal_name: basestring
    """
    try:
        return netbox.sensor_set.get(internal_name__icontains=internal_name)
    except Sensor.DoesNotExist:
        return Sensor.objects.none()


@register.filter
def get_sensors(netbox, internal_name):
    """
    Gets the sensors from the netbox that matches the internal_name
    :param netbox: An instance of a netbox
    :type netbox: nav.models.manage.Netbox
    :param internal_name: filter on this internal_name
    :type internal_name: basestring
    """
    return netbox.sensor_set.filter(
        internal_name__icontains=internal_name).order_by('internal_name')


@register.filter
def get_value(some_dictionary, key):
    """The most common template filter ever"""
    return some_dictionary.get(key)

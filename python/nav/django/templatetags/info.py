#
# Copyright (C) 2012-2019 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Template tags used in info subsystem"""

from datetime import datetime, timedelta
import time

from django import template
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def time_since(timestamp):
    """Convert a timestamp to human readable time since"""

    mapping = {'minute': 'min', 'hour': 'hr', 'week': 'wk', 'month': 'mo', 'year': 'yr'}

    if timestamp is None:
        return "Never"

    if _is_more_or_less_now(timestamp):
        return "Now"
    else:
        text = timesince(timestamp)
        for key, replacement in mapping.items():
            text = text.replace(key, replacement)

        return text


@register.filter
def days_since(timestamp):
    """Convert a timestamp to human readable time using days"""
    if timestamp is None:
        return "Never"

    if _is_more_or_less_now(timestamp):
        return "Now"
    elif timestamp.date() == datetime.now().date():
        return "Today"
    elif timestamp.date() == datetime.now().date() - timedelta(days=1):
        return "Yesterday"
    else:
        return "%s days" % (datetime.now().date() - timestamp.date()).days


def _is_more_or_less_now(timestamp):
    interval = datetime.now() - timestamp
    less_than_a_minute = interval.total_seconds() < 60
    return timestamp == datetime.max or less_than_a_minute


@register.filter
def is_max_timestamp(timestamp):
    """Check if timestamp is max"""
    if timestamp == datetime.max:
        return True
    else:
        return False


@register.filter
def run(function, arg):
    """Run a function with given argument"""
    return function(arg)


@register.filter
def get_attr(value, arg):
    """Lookup attribute on object

    value: an object instance - i.e. interface
    arg: i.e. id

    Supports chaining (arg = netbox.sysname)
    If nothing is found, return empty string
    """
    if arg.count('.'):
        return find_attr(value, arg.split('.'))
    else:
        return getattr(value, arg, "")


def find_attr(obj, attrlist):
    """Recursive search for attributes in attrlist"""
    try:
        attr = getattr(obj, attrlist[0])
    except AttributeError:
        return ""

    if len(attrlist) > 1:
        return find_attr(attr, attrlist[1:])
    else:
        return attr


@register.filter
def lookup(value, key):
    """Lookup key in a dictionary"""
    return value.get(key, value)


@register.filter
def interval(value):
    """Create a human readable interval

    Arguments:
    value -- a number of seconds

    """
    return time.strftime('%H:%M:%S', time.gmtime(value))


@register.filter
def add_interval(value, seconds):
    """Create a new timestamp based on value and interval

    Arguments:
    value -- a datetime object
    interval -- interval in seconds

    """

    try:
        return value + timedelta(seconds=seconds)
    except TypeError:
        return value


@register.filter
def get_graph_url(obj, time_frame):
    return obj.get_graph_url(time_frame=time_frame)


@register.filter
def get_netbox_availability(netbox, time_frame):
    """Get availability for a given netbox and time frame
    :type netbox: nav.models.manage.Netbox
    :type time_frame: basestring
    """
    availability = netbox.get_availability()
    try:
        return "%.2f%%" % availability["availability"][time_frame]
    except (KeyError, TypeError):
        return "N/A"


@register.filter
def get_value(something, key):
    """Gets value from something using key"""
    try:
        return something.get(key)
    except AttributeError:
        pass


@register.filter
def sortdict(dictionary, reverse=False):
    """Returns a list of sorted dictionary items"""
    return sorted(dictionary.items(), reverse=bool(reverse))


@register.filter
def is_list(value):
    """Returns True if the value is a list"""
    return isinstance(value, list)


@register.filter
def dunderless(mapping):
    """
    Returns a mapping with all elements of the input mapping except for ones whose key
    starts with dunder
    """
    mapping = {k: v for k, v in mapping.items() if not k.startswith('__')}
    return mapping

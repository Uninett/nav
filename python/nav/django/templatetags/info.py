"""Template tags used in info subsystem"""
import time
from django import template
from datetime import datetime, timedelta
from django.utils.timesince import timesince

# pylint: disable=C0103
register = template.Library()


@register.filter
def time_since(timestamp):
    """Convert a timestamp to human readable time since"""

    mapping = {'minute': 'min',
               'hour': 'hr',
               'week': 'wk',
               'month': 'mo',
               'year': 'yr'}

    if timestamp is None:
        return "Never"

    if timestamp == datetime.max or timesince(timestamp) == "0 minutes":
        return "Now"
    else:
        text = timesince(timestamp)
        for key in mapping.keys():
            text = text.replace(key, mapping[key])

        return text


@register.filter
def days_since(timestamp):
    """Convert a timestamp to human readable time using days"""
    if timestamp is None:
        return "Never"

    if timestamp == datetime.max or timesince(timestamp) == "0 minutes":
        return "Now"
    elif timestamp.date() == datetime.now().date():
        return "Today"
    elif timestamp.date() == datetime.now().date() - timedelta(days=1):
        return "Yesterday"
    else:
        return "%s days" % (datetime.now().date() - timestamp.date()).days


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

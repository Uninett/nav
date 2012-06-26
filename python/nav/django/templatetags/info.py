"""Template tags used in info subsystem"""
from django import template
from datetime import datetime
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def time_since(timestamp):
    """Convert a timestamp to human readable time since"""

    lookup = {'minute': 'min',
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
        for key in lookup.keys():
            text = text.replace(key, lookup[key])

        return text

@register.filter
def is_max_timestamp(timestamp):
    """Check if timestamp is max"""
    if timestamp == datetime.max:
        return True
    else:
        return False


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
def split(value, char):
    """Splits the value on char"""
    return value.split(char)

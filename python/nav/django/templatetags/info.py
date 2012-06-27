"""Template tags used in info subsystem"""
from django import template
from datetime import datetime
from django.utils.timesince import timesince

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
def lookup(value, key):
    """Lookup key in a dictionary"""
    return value.get(key, value)

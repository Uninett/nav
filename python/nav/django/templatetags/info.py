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

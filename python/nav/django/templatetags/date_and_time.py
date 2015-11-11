"""Template filters and tags for helping with dates and datetimes"""
# pylint: disable=W0702,C0103
from django import template
from nav.django.settings import DATETIME_FORMAT
from django.template.defaultfilters import date
from datetime import timedelta

register = template.Library()

@register.filter
def default_datetime(value):
    """Returns the date as represented by the default datetime format"""
    try:
        v = date(value, DATETIME_FORMAT)
    except:
        return value

    return v


@register.filter
def remove_microseconds(delta):
    """Removes microseconds from timedelta"""
    try:
        return delta - timedelta(microseconds=delta.microseconds)
    except:
        return delta

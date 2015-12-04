"""Time and date related tags and filters"""
# pylint: disable=C0103, W0702

from django import template
from nav.django.settings import DATETIME_FORMAT, SHORT_TIME_FORMAT
from django.template.defaultfilters import date, time

register = template.Library()


@register.filter
def default_datetime(value):
    try:
        v = date(value, DATETIME_FORMAT)
    except:
        return value

    return v


@register.filter
def short_time_format(value):
    """Returns the value formatted as a short time format

    The SHORT_TIME_FORMAT is a custom format not available in the template
    """
    try:
        return time(value, SHORT_TIME_FORMAT)
    except:
        return value

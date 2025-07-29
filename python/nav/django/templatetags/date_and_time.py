"""Template filters and tags for helping with dates and datetimes"""

from datetime import timedelta
from django import template
from django.template.defaultfilters import date, time
from nav.django.settings import DATETIME_FORMAT, SHORT_TIME_FORMAT

register = template.Library()


@register.filter
def default_datetime(value):
    """Returns the date as represented by the default datetime format"""
    try:
        v = date(value, DATETIME_FORMAT)
    except Exception:  # noqa: BLE001
        return value

    return v


@register.filter
def short_time_format(value):
    """Returns the value formatted as a short time format

    The SHORT_TIME_FORMAT is a custom format not available in the template
    """
    try:
        return time(value, SHORT_TIME_FORMAT)
    except Exception:  # noqa: BLE001
        return value


@register.filter
def remove_microseconds(delta):
    """Removes microseconds from timedelta"""
    try:
        return delta - timedelta(microseconds=delta.microseconds)
    except Exception:  # noqa: BLE001
        return delta

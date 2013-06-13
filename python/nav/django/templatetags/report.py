"""Template tags used in report subsystem"""

# TODO: Change the name of this file

from datetime import timedelta

from django import template


register = template.Library()


@register.filter
def get_item(value, arg):
    return value.get(arg)


@register.filter
def time_from_seconds(value):
    return str(timedelta(seconds=value))


get_item.is_safe = True
time_from_seconds.is_safe = True




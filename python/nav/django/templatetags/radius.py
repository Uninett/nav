from datetime import timedelta

from django import template


register = template.Library()


@register.filter
def time_from_seconds(value):
    if value:
        return str(timedelta(seconds=value))
    else:
        return ''


time_from_seconds.is_safe = True
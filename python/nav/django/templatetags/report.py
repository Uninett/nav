"""Template tags used in report subsystem"""

from django import template


register = template.Library()


@register.filter
def get_item(value, arg):
    return value.get(arg)


get_item.is_safe = True

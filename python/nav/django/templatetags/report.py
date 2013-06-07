"""Template tags used in report subsystem"""

from django import template


register = template.Library()


@register.filter(is_safe=True)
def get_item(value, arg):
    return value.get(arg)

"""Template tags used in report subsystem"""
from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter
def get_item(value, arg):
    return value.get(arg)


@register.filter
@stringfilter
def escapeslash(value):
    return value.replace('/', '%2F')


get_item.is_safe = True





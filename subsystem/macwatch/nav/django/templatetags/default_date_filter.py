from django import template
from nav.django.settings import DATETIME_FORMAT
from django.template.defaultfilters import date

register = template.Library()

@register.filter
def default_datetime(value):
    try:
        v = date(value, DATETIME_FORMAT)
    except:
        return value
    
    return v

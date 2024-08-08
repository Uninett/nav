"""Template tags used in report subsystem"""

from django import template
from django.template.defaultfilters import stringfilter
from django.urls import reverse
from urllib.parse import urlencode


register = template.Library()


@register.filter(is_safe=True)
def get_item(value, arg):
    return value.get(arg)


@register.filter
@stringfilter
def escapeslash(value):
    return value.replace("/", "%2F")


@register.simple_tag
def report(name, **kwargs):
    """Returns a URL to a named report with the given kwargs as a search filter"""
    base = reverse("report-by-name", kwargs={"report_name": name})
    report_args = {k: v for k, v in kwargs.items() if v is not None}
    if report_args:
        return "{}?{}".format(base, urlencode(report_args))
    return base

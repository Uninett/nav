"""Template filters for string manipulation"""

import re

from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()

# A url ends at whitespace, a quote or an angle bracket in the surrounding text
_URL_PATTERN = re.compile(r"""(https?://[^\s"'<>]+)""")


@register.filter
def shorten_ifname(ifname):  # pragma: nocover
    """Shorten ifname and indicate shortening with ellipsis"""
    matchobject = re.match(r'([a-zA-Z]{2})\D+(.*/\d+)$', ifname)
    if matchobject:
        return "...".join(matchobject.groups())
    return ifname


@register.filter(needs_autoescape=True)
def deep_urlize(value, autoescape=True):
    """Convert anything that looks like an url to a link.

    When autoescaping is on, any text around the urls is escaped. The result is
    then safe to render even when the value comes from untrusted data.
    """
    if not value:
        return value
    escape = conditional_escape if autoescape else str
    parts = _URL_PATTERN.split(str(value))
    # re.split puts the captured urls at the odd indexes
    return mark_safe(
        "".join(
            format_html('<a href="{0}">{0}</a>', part) if index % 2 else escape(part)
            for index, part in enumerate(parts)
        )
    )


@register.filter
def starts_with(value, arg):
    """Check if a string starts with the given argument"""
    return str(value).startswith(str(arg))

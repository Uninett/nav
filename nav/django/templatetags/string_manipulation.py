"""Template filters for string manipulation"""
import re

from django import template

register = template.Library()


@register.filter
def shorten_ifname(ifname):  # pragma: nocover
    """Shorten ifname and indicate shortening with ellipsis"""
    matchobject = re.match(r'([a-zA-Z]{2})\D+(.*/\d+)$', ifname)
    if matchobject:
        return "...".join(matchobject.groups())
    return ifname


@register.filter
def deep_urlize(value):
    """Convert anything that looks like an url to an href tag"""
    if value:
        return re.sub(r'(https?://[^" ]+)', r'<a href="\1">\1</a>', value)
    return value

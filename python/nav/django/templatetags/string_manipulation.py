"""Template filters for string manipulation"""
from django import template
import re

register = template.Library()


@register.filter
def shorten_ifname(ifname):
    """Shorten ifname and indicate shortening with ellipsis"""
    matchobject = re.match(r'([a-zA-Z]{2})\D+(.*/\d+)$', ifname)
    if matchobject:
        return "...".join(matchobject.groups())
    return ifname


@register.filter
def add_zwsp(value, separator="|"):
    """Add Zero Width space after the given separator"""
    return ("%s%s" % (separator, "&#8203;")).join(value.split(separator))


@register.filter
def deep_urlize(value):
    """Convert anything that looks like an url to an href tag"""
    if value:
        return re.sub(r'(https?://[^" ]+)', r'<a href="\1">\1</a>', value)
    return value

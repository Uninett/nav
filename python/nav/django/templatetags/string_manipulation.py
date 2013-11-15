from django import template
import re

register = template.Library()

@register.filter
def shorten_ifname(ifname):
    """Shorten ifname and indicate shortening with ellipsis"""
    matchobject = re.match('([a-zA-Z]{2})\D+(.*/\d+)$', ifname)
    if matchobject:
        return "...".join(matchobject.groups())
    return ifname

@register.filter
def add_zwsp(value, separator="|"):
    """Add Zero Width space after the given separator"""
    return ("%s%s" % (separator, "&#8203;")).join(value.split(separator))

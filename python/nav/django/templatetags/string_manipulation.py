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

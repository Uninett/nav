from django import template
from datetime import date

register = template.Library()

@register.filter
def time_since(delta):
    """ Convert a timedelta to human readable format """
    minute = 60
    hour = 60 * minute

    if delta is None:
        return ""

    if delta.days > 365:
        return "More than a year ago"
    elif delta.days > 0:
        return "%s days ago" % delta.days
    elif delta.seconds > hour:
        # Round to nearest hour
        return "%s hours ago" % int(round((float(delta.seconds) / hour)))
    elif delta.seconds > 60:
        # Round to nearest minute
        return "%s minutes ago" % int(round((float(delta.seconds) / minute)))
    elif delta.seconds > 0:
        return "%s seconds ago" % delta.seconds
    else:
        return "Active now"

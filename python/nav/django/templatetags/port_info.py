from django import template
register = template.Library()

from nav.models.manage import SwPortVlan

DIRECTIONS = dict((v, k) for k, v in SwPortVlan.DIRECTION_CHOICES)


@register.filter
def get_direction_class(direction):
    if DIRECTIONS[direction] == SwPortVlan.DIRECTION_DOWN:
        return 'fa-arrow-circle-o-down'
    elif DIRECTIONS[direction] == SwPortVlan.DIRECTION_UP:
        return 'fa-arrow-circle-o-up'
    elif DIRECTIONS[direction] == SwPortVlan.DIRECTION_UNDEFINED:
        return 'fa-question'
    elif DIRECTIONS[direction] == SwPortVlan.DIRECTION_BLOCKED:
        return 'fa-ban'

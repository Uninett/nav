from typing import Optional

from django import template
from nav.models.manage import (
    BOTH_RELATION,
    LAG_RELATION,
    STACK_RELATION,
    SwPortVlan,
)

register = template.Library()

DIRECTIONS = dict((v, k) for k, v in SwPortVlan.DIRECTION_CHOICES)

# Human-readable labels for an interface's relation to its parent in the
# layered aggregate/stack topology tree, used both for the hover tooltip and
# the screen-reader text so the wording stays in one place.
TOPOLOGY_RELATION_LABELS = {
    LAG_RELATION: "Member of link aggregate (LAG)",
    STACK_RELATION: "Layered below (ifStack)",
    BOTH_RELATION: "Bundled and layered (LAG + ifStack)",
}


@register.filter
def topology_relation_label(relation: Optional[str]) -> str:
    """Returns the human-readable label for a topology tree node's relation."""
    return TOPOLOGY_RELATION_LABELS.get(relation, "")


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

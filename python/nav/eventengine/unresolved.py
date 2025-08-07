#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Loading and caching of unresolved alert states from the database"""

import logging

from nav.models.event import AlertHistory
from nav.models.fields import INFINITY

_logger = logging.getLogger(__name__)
_unresolved_alerts_map = {}


def get_map():
    """Returns a cached dictionary of unresolved AlertHistory entries"""
    return _unresolved_alerts_map


def update():
    """Updates the map of unresolved alerts from the database"""
    global _unresolved_alerts_map
    unresolved = AlertHistory.objects.filter(end_time__gte=INFINITY)
    _unresolved_alerts_map = dict((alert.get_key(), alert) for alert in unresolved)


def refers_to_unresolved_alert(event):
    """Verifies whether an event appears to refer to a currently
    unresolved alert state.

    :returns: An AlertHistory object for the matched unresolved alert,
              or False if none was found.

    """
    try:
        result = _unresolved_alerts_map[event.get_key()]
        return result
    except KeyError:
        _logger.debug(
            "no match for (%r) %r among list of unresolved alerts",
            event.get_key(),
            event,
        )
        _logger.debug("unresolved map contains: %r", _unresolved_alerts_map)
        return False

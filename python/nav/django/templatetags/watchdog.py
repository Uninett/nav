#
# Copyright (C) 2014 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Template tags and filters for watchdog templates"""

from django import template
from nav.watchdog.tests import STATUS_UNKNOWN, STATUS_NOT_OK, STATUS_OK

register = template.Library()


@register.filter
def map_to_class(status):
    """Map a status to a css class"""
    mapping = {
        STATUS_NOT_OK: 'alert',
        STATUS_OK: 'success',
        STATUS_UNKNOWN: ''
    }

    return mapping.get(status, '')


@register.filter
def map_to_faclass(status):
    """Return Font Awesome class based on status"""
    mapping = {
        STATUS_NOT_OK: 'fa-exclamation',
        STATUS_OK: 'fa-check'
    }

    return mapping.get(status, '')

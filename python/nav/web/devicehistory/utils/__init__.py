# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Device history utility functions."""

from nav.models.event import AlertType


def get_event_and_alert_types():
    alert_types = (
        AlertType.objects.select_related('event_type')
        .all()
        .order_by('event_type__id', 'name')
    )
    event_types = {}
    for a in alert_types:
        if a.event_type.id not in event_types:
            event_types[a.event_type.id] = [
                ('e_%s' % a.event_type.id, 'All %s' % a.event_type.id)
            ]
        event_types[a.event_type.id].append(('a_%s' % a.name, a.name))

    # Quick fix for use in django forms - create list of tuples to
    # create optgroups.
    result = [('all', 'All')]
    result.extend(event_types.items())
    return result

#
# Copyright (C) 2017 UNINETT AS
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

"""Controllers for the event info pages"""

import datetime
import operator
import itertools

from django.shortcuts import get_object_or_404, render

from nav.models.event import AlertHistory
from nav.web import utils


def get_context():
    """Returns common context"""

    navpath = (('Home', '/'), ('Event details', ''),)
    return {
        'navpath': navpath,
        'title': utils.create_title(navpath)
    }


def main(request):
    """Main controller"""

    context = get_context()
    return render(request, 'info/event/base.html', context)


def render_event(request, event_id):
    """Renders details about a single event"""

    event = get_object_or_404(AlertHistory, pk=event_id)

    related_netbox_events = AlertHistory.objects.filter(
        netbox=event.netbox).order_by('-start_time')[:10]
    related_type_events = AlertHistory.objects.filter(
        alert_type=event.alert_type).order_by('-start_time')[:10]

    context = get_context()
    context.update({
        'event': event,
        'is_module_or_chassis': is_module_or_chassis(event),
        'related_netbox_events': related_netbox_events,
        'related_type_events': related_type_events,
        'messages': get_messages(event)
    })
    return render(request, 'info/event/details.html', context)


def is_module_or_chassis(event):
    return (event.event_type.pk == 'moduleState' or
            event.event_type.pk == 'chassisState')


def get_messages(event):
    """Filter messages and group by type"""
    msgs = event.messages.filter(language='en')
    keyfunc = operator.attrgetter('state')
    return {k: sorted(g, key=operator.attrgetter('type'))
            for k, g in itertools.groupby(msgs, key=keyfunc)}

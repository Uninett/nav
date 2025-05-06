#
# Copyright (C) 2008-2011 Uninett AS
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
from functools import reduce
from collections import OrderedDict

from django.core.paginator import InvalidPage

from django.db.models import Q

from nav.models.event import AlertHistory, AlertHistoryMessage
from nav.models.manage import (
    Netbox,
    Device,
    Location,
    Room,
    Module,
    NetboxGroup,
    Organization,
    Category,
)

LOCATION_GROUPING = {
    'order_by': 'netbox__room__location__description',
    'group_by': lambda a: a.netbox.room.location.description,
}
ROOM_GROUPING = {
    'order_by': 'netbox__room__id',
    'group_by': lambda a: a.netbox.room.id,
}
DEVICE_GROUPING = {
    'order_by': 'netbox__room__description',
    'group_by': lambda a: a.device.serial,
}
NETBOX_GROUPING = {
    'order_by': 'netbox__sysname',
    'group_by': lambda a: a.netbox.sysname,
}
DATE_GROUPING = {
    'order_by': None,
    'group_by': lambda a: a.start_time.date().isoformat(),
}
GROUPINGS = {
    'location': LOCATION_GROUPING,
    'room': ROOM_GROUPING,
    'device': DEVICE_GROUPING,
    'netbox': NETBOX_GROUPING,
    'datetime': DATE_GROUPING,
}


def get_selected_types(selected_type):
    selected_types = {'event': None, 'alert': None}
    if selected_type and selected_type.find('_') != -1:
        kind, name = selected_type.split('_', 1)
        kind = 'event' if kind == 'e' else 'alert'
        selected_types[kind] = name
    return selected_types


def fetch_history(selection, form):
    def type_query_filter(selected_types):
        # FIXME Selecting multiple is not accutally possible from the GUI.
        # Remove option for multiple and make it simpler?
        type_filter = []
        if selected_types['event']:
            type_filter.append(Q(event_type=selected_types['event']))
        if selected_types['alert']:
            type_filter.append(Q(alert_type__name=selected_types['alert']))
        return type_filter

    def make_selection_filter(and_mode=False):
        dicts = {
            '%s__in' % (arg if arg != 'netbox' else 'id'): selection[arg]
            for arg in (
                'netbox',
                'room',
                'room__location',
                'organization',
                'category',
                'modules',
                'groups',
            )
            if selection[arg]
        }
        filters = [Q(**dicts)]

        combinator = lambda x, y: (x & y) if and_mode else (x | y)
        return reduce(combinator, filters) if filters else None

    from_date = form.cleaned_data['from_date']
    to_date = form.cleaned_data['to_date']
    selected_types = get_selected_types(form.cleaned_data['eventtype'])
    order_by = form.cleaned_data['group_by']

    type_filter = type_query_filter(selected_types)
    order_by_keys = ['-start_time', '-end_time']
    if GROUPINGS[order_by]['order_by']:
        order_by_keys.insert(0, GROUPINGS[order_by]['order_by'])

    # Find all netbox ids and device ids that belongs to
    #   - selected netboxes
    #   - selected rooms
    #   - selected locations
    #   - selected organizations
    #   - selected categories
    netbox = Netbox.objects.all()
    selection_filter = make_selection_filter(
        selection['mode'] and selection['mode'][0] == 'and'
    )
    if selection_filter:
        netbox = netbox.filter(selection_filter)

    # Find device ids that belongs to
    #   - selected devices
    device = Device.objects.filter(modules__in=selection['modules'])

    # Find alert history that belongs to the netbox and device ids we found in
    # the previous two queries.
    #
    # Time limit is done in raw SQL to make sure all parantheses are right.
    history = (
        AlertHistory.objects.select_related(
            'event_type',
            'alert_type',
            'device',
            'netbox',
            'netbox__room',
            'netbox__room__location',
            'netbox__organization',
            'netbox__category',
        )
        .filter(
            Q(netbox__in=[n.id for n in netbox]) | Q(device__in=[d.id for d in device]),
            *type_filter,
        )
        .extra(
            where=[
                '''
            (
                (end_time IS NULL AND start_time >= %s AND start_time <= %s) OR
                (end_time = 'infinity' AND start_time < %s) OR
                (end_time >= %s AND start_time < %s)
            )
           ''',
            ],
            params=[from_date, to_date, to_date, from_date, to_date],
        )
        .order_by(*order_by_keys)
    )

    return history


def get_page(paginator, page):
    try:
        history = paginator.page(page)
    except InvalidPage:
        history = paginator.page(paginator.num_pages)
    return history


def get_messages_for_history(alert_history):
    msgs = AlertHistoryMessage.objects.filter(
        alert_history__in=[h.id for h in alert_history],
        language='en',
    ).values('alert_history', 'message', 'type', 'state')
    return msgs


def group_history_and_messages(history, messages, group_by=None):
    grouped_history = OrderedDict()
    for a in history:
        a.extra_messages = {}
        for m in messages:
            if a.id == m['alert_history']:
                if m['state'] not in a.extra_messages:
                    a.extra_messages[m['state']] = {
                        'sms': None,
                        'email': None,
                        'jabber': None,
                    }
                a.extra_messages[m['state']][m['type']] = m['message']

        try:
            key = GROUPINGS[group_by]['group_by'](a)
        except AttributeError:
            key = None

        if key not in grouped_history:
            grouped_history[key] = []
        grouped_history[key].append(a)
    return grouped_history


def describe_search_params(selection):
    data = {}
    for arg, model in (
        ('loc', Location),
        ('room', Room),
        ('netbox', Netbox),
        ('groups', NetboxGroup),
        ('module', Module),
        ('organization', Organization),
        ('category', Category),
    ):
        if arg in selection and selection[arg]:
            name = getattr(model, '_meta').verbose_name
            data[name] = _get_data_to_search_terms(selection, arg, model)

    # Special case with netboxes
    if Netbox._meta.verbose_name not in data:
        data[Netbox._meta.verbose_name] = ["All IP devices selected."]

    return data


def _get_data_to_search_terms(selection, key_string, model):
    """Creates a human-readable list of things that were selected by the
    search terms.

    If all existing objects of a given model are selected, they are summarized
    in a single 'all X selected' statement.

    """
    selected_objects = len(selection[key_string])
    if selected_objects == model.objects.all().count():
        return ["All {} selected.".format(model._meta.verbose_name_plural)]
    else:
        return model.objects.filter(id__in=selection[key_string])


def add_descendants(parents):
    """Add all descendants of the parents

    :param parents: A list of Location keys
    :type parents: list<string>
    :returns: A list of unique Location keys with all descendants added
    """
    locations = parents
    for location_key in parents:
        try:
            location = Location.objects.get(pk=location_key)
        except Location.DoesNotExist:
            pass
        else:
            locations.extend([location.pk for location in location.get_descendants()])
    return list(set(locations))

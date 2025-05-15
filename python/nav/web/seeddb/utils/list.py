# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
# Copyright (C) 2022 Sikt
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

"""Functions for rendering seeddb list views"""

from collections import defaultdict
from functools import reduce

from django.db.models import Model
from django.shortcuts import render
from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse

from nav.django.utils import get_verbose_name


def render_list(
    request,
    queryset,
    value_list,
    edit_url=None,
    edit_url_attr='pk',
    filter_form=None,
    template='seeddb/list.html',
    extra_context=None,
    add_descriptions=False,
    add_related=None,
):
    """Renders a Seed DB list.

    Parameters:
     - request: HttpRequest object from Django
     - queryset: A queryset containing all objects that should appear in the
                 list.
     - value_list: Tuple with field names used in Django's `value_list`
                   queryset method.
     - edit_url: Named URL to the edit page.
     - edit_url_attr: Attribute used to make the URL to the edit page.
     - filter_form: Form used to filter the queryset.
     - template: Path to the template used.
     - extra_context: A dictionary containing all additional context that
                      should be used in the template.
    """

    if not extra_context:
        extra_context = {}

    queryset = _filter_query(filter_form, queryset)

    if not edit_url:
        rows, datakeys = _process_objects(queryset, value_list)
    else:
        rows, datakeys = _process_objects(queryset, value_list, edit_url, edit_url_attr)

    labels = _label(queryset.model, value_list, datakeys)
    if add_descriptions:
        _add_descriptions(rows, queryset)
    if add_related is not None:
        add_related(rows)

    context = {
        'object_list': rows,
        'labels': labels,
        'filter_form': filter_form,
        'sub_active': {'list': True},
    }

    # Update extra_context with context.
    # Doing it this way makes sure that the context dictionary overrides any
    # user-supplied data, not the other way around.
    extra_context.update(context)
    return render(request, template, extra_context)


def _filter_query(filter_form, queryset):
    """Apply filter_form to queryset."""
    if filter_form and filter_form.is_valid():
        # Convert UI fieldname to DB lookup
        mapper = getattr(filter_form, "map_formfieldname_to_queryname", lambda x: x)
        filter_data = filter_form.cleaned_data.items()
        query_filter = {mapper(key): value for key, value in filter_data if value}
        queryset = queryset.filter(**query_filter)
    return queryset


def _process_objects(queryset, value_list, edit_url=None, edit_url_attr=None):
    """Packs values into a format the template understands.

    A list contains each row.
    Each row is a dictionary with following keys:
     - pk: The primary key.
     - url: URL to the edit page.
     - values_list: A list with the values that should be displayed in the
                    table.
    """
    # pick up which values are dictionaries and make note of their existing keys
    datakeys = defaultdict(set)
    for obj in queryset:
        for attr in value_list:
            value = _getattr(obj, attr)
            if isinstance(value, dict):
                datakeys[attr].update(value)
    datakeys = {k: list(sorted(v)) for k, v in datakeys.items()}

    def _getvalues(obj):
        for attr in value_list:
            value = _getattr(obj, attr)
            if attr in datakeys:
                for key in datakeys[attr]:
                    yield value.get(key, None)
            elif isinstance(value, tuple):
                # this only normally happens with tuples of Decimal values in Rooms
                yield ", ".join(str(v) for v in value)
            else:
                yield value

    rows = []
    for obj in queryset:
        row = {
            'pk': obj.pk,
            'values_list': list(_getvalues(obj)),
            'model': obj,
        }
        if edit_url and edit_url_attr:
            key = _getattr(obj, edit_url_attr)
            row['url'] = reverse(edit_url, args=(key,))
        rows.append(row)
    return rows, datakeys


def _getattr(obj, attr):
    """Deep getattr for Django double underscore specs.

    Should conform to the bassackwards ways of SeedDB at large.
    """
    try:
        value = reduce(getattr, attr.split('__'), obj)
        if isinstance(value, Model):
            return value.pk
        else:
            return value
    except AttributeError:
        pass


def _label(model, value_list, datakeys=None):
    """Make labels for the table head.
    Returns a list of tuples. Each tuple contains the verbose label and a key
    that can be used for sort parameters in the URL.
    """
    attrs = []
    labels = []
    for value in value_list:
        if value in datakeys:
            labels.extend(datakeys[value])
            attrs.extend(datakeys[value])
        else:
            attrs.append(value)
            try:
                labels.append(get_verbose_name(model, value))
            except FieldDoesNotExist:
                labels.append(value)
    return zip(labels, attrs)


def _add_descriptions(rows, queryset):
    """Adds a description key to all objects"""
    for row in rows:
        model = row['model']
        row['description'] = getattr(model, 'description', '')

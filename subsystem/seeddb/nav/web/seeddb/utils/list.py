# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.django.utils import get_verbose_name

ITEMS_PER_PAGE = 100

def render_list(request, queryset, value_list, edit_url, edit_url_attr='pk', \
        filter_form=None, template='seeddb/list.html', extra_context={}):
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

    order_by = request.GET.get('sort')
    order_by = _get_order_by(order_by, value_list)
    order_by_meta = _order_by_meta(order_by)

    queryset = _filter_query(filter_form, queryset)
    queryset = queryset.order_by(order_by)

    # Get values specified in value_list from the queryset.
    # Also make sure that the primary key and the edit_url_attr appears.
    value_queryset = queryset.values('pk', edit_url_attr, *value_list)

    per_page = request.GET.get('per_page', ITEMS_PER_PAGE)
    if per_page == 'all':
        per_page = value_queryset.count()
    else:
        per_page = _get_num(request.GET, 'per_page', ITEMS_PER_PAGE)
    page_num = _get_num(request.GET, 'page', 1)

    page = _paginate(value_queryset, per_page, page_num)
    objects = _process_objects(page, value_list, edit_url, edit_url_attr)
    labels = _label(queryset.model, value_list)

    context = {
        'object_list': objects,
        'labels': labels,
        'current_sort': order_by,
        'current_sort_label': order_by_meta['current_sort_label'],
        'other_sort': order_by_meta['other_sort'],
        'sort_asc': order_by_meta['sort_asc'],
        'filter_form': filter_form,
        'page': page,
        'sub_active': {'list': True},
    }
    # Update extra_context with context.
    # Doing it this way makes sure that the context dictionary overrides any
    # user-supplied data, not the other way around.
    extra_context.update(context)
    return render_to_response(template,
        extra_context, RequestContext(request))

def _get_num(get, key, default=1):
    """Returns a number identified by key from the dictionary get.
    Defaults to default.

    Parameters:
     - get: A dictionary
     - key: The key used to lookup the given value in get.
     - default: The default value.
    """
    try:
        num = int(get.get(key, default))
    except ValueError:
        num = default
    return num

def _filter_query(filter_form, queryset):
    """Apply filter_form to queryset.
    """
    if filter_form and filter_form.is_valid():
        query_filter = dict([(key, value) for key, value in filter_form.cleaned_data.items() if value])
        queryset = queryset.filter(**query_filter)
    return queryset

def _get_order_by(order_by, value_list):
    """Check if the specified order is valid.
    Returns order_by if it's valid, else it returns the first value in value_list.
    """
    if not order_by or order_by.find('-') not in (-1, 0) or order_by.lstrip('-') not in value_list:
        order_by = value_list[0]
    return order_by

def _order_by_meta(order_by):
    """Populates a dictionary with meta information about the current ordering
    given by order_by.
    """
    sort_asc = '-' not in order_by
    return {
        'sort_asc': sort_asc,
        'current_sort_label': order_by.lstrip('-'),
        'other_sort': sort_asc and '-' + order_by or order_by.lstrip('-'),
    }

def _paginate(value_qs, per_page, page_num):
    """Apply pagination to the queryset.
    """
    paginator = Paginator(value_qs, per_page)
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        page = paginator.page(paginator.num_pages)
    return page

def _process_objects(page, value_list, edit_url, edit_url_attr):
    """Packs values into a format the template understands.

    A list contains each row.
    Each row is a dictionary with following keys:
     - pk: The primary key.
     - url: URL to the edit page.
     - values_list: A list with the values that should be displayed in the
                    table.
    """
    objects = []
    for obj in page.object_list:
        row = {
            'pk': obj['pk'],
            'url': reverse(edit_url, args=(obj[edit_url_attr],)),
            'values_list': [obj[attr] for attr in value_list],
        }
        objects.append(row)
    return objects

def _label(model, value_list):
    """Make labels for the table head.
    Returns a list of tuples. Each tuple contains the verbose label and a key
    that can be used for sort parameters in the URL.
    """
    labels = [get_verbose_name(model, value) for value in value_list]
    return zip(labels, value_list)

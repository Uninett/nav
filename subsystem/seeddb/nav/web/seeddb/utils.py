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
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.django.utils import get_verbose_name

def render_seeddb_list(request, queryset, value_list, edit_url, edit_url_attr='pk', extra_context={}):
    """Renders a list from the supplied queryset.

       Parameters:
         - request: django request object
         - queryset: a queryset with all objects that should be rendered in the
           list
         - value_list: tuple with field names, the fields from the queryset
           that should appear in the list
         - edit_url: a url (that works with reverse()) to the edit page
         - edit_url_attr: the name of the field that should be used in the
           reverse url lookup, defaults to 'pk'
         - extra_context: everything else that should be in the template
    """
    # Get the sort order. Default to the first object in value_list.
    order_by = request.GET.get('sort')
    if not order_by or order_by.find('-') not in (-1, 0) or order_by.lstrip('-') not in value_list:
        order_by = value_list[0]

    # Get a ValuesQuerySet. Make sure 'pk' and the edit_url_attr appears in the
    # result.
    query_values = queryset.order_by(order_by).values('pk', edit_url_attr, *value_list)

    object_list = list()
    for object in query_values:
        row = {
            'pk': object['pk'],
            'url': reverse(edit_url, args=(object[edit_url_attr],)),
            'values_list': [object[attr] for attr in value_list],
        }
        object_list.append(row)

    # Get verbose names from fields in value_list. We shall use 'em as labels.
    labels = [get_verbose_name(queryset.model, value) for value in value_list]

    info_dict =  {
        'object_list': object_list,
        'labels': zip(labels, value_list),
        'current_sort': order_by.lstrip('-'),
        'sort_asc': "-" not in order_by,
    }
    extra_context.update(info_dict)
    return render_to_response(
        'seeddb/list.html',
        extra_context,
        RequestContext(request)
    )

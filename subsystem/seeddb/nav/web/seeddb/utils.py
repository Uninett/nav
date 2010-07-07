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
from django.http import HttpResponseRedirect

from nav.django.utils import get_verbose_name
from nav.web.message import new_message, Messages

ITEMS_PER_PAGE = 100

def get_page_num(get):
    try:
        page_num = int(get.get('page', '1'))
    except ValueError:
        page_num = 1
    return page_num

def get_page(paginator, page_num):
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        page = paginator.page(paginator.num_pages)
    return page

def render_seeddb_list(request, queryset, value_list, edit_url, edit_url_attr='pk', filter_form=None, extra_context={}):
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
         - filter_form: A form instance used to filter the queryset.
         - extra_context: everything else that should be in the template
    """
    # Apply filters
    if filter_form and filter_form.is_valid():
        filter = dict([(key, val) for key, val in filter_form.cleaned_data.items() if val])
        queryset = queryset.filter(**filter)

    # Get the sort order. Default to the first object in value_list.
    order_by = request.GET.get('sort')
    if not order_by or order_by.find('-') not in (-1, 0) or order_by.lstrip('-') not in value_list:
        order_by = value_list[0]

    # Get a ValuesQuerySet. Make sure 'pk' and the edit_url_attr appears in the
    # result.
    query_values = queryset.order_by(order_by).values('pk', edit_url_attr, *value_list)

    # Get the correct page
    paginator = Paginator(query_values, ITEMS_PER_PAGE)
    page_num = get_page_num(request.GET)
    page = get_page(paginator, page_num)

    object_list = list()
    for object in page.object_list:
        row = {
            'pk': object['pk'],
            'url': reverse(edit_url, args=(object[edit_url_attr],)),
            'values_list': [object[attr] for attr in value_list],
        }
        object_list.append(row)

    # Get verbose names from fields in value_list. We shall use 'em as labels.
    labels = [get_verbose_name(queryset.model, value) for value in value_list]

    sort_asc = "-" not in order_by
    info_dict =  {
        'object_list': object_list,
        'labels': zip(labels, value_list),
        'current_sort_label': order_by.lstrip('-'),
        'current_sort': order_by,
        'other_sort': sort_asc and "-" + order_by or order_by.lstrip('-'),
        'sort_asc': sort_asc,
        'filter_form': filter_form,
        'page': page,
    }
    extra_context.update(info_dict)
    return render_to_response(
        'seeddb/list.html',
        extra_context,
        RequestContext(request)
    )

def get_object(object_class, object_id):
    if not object_id:
        return None
    return object_class.objects.get(id=object_id)

def get_form(request, form_class, object):
    if request.method == 'POST':
        form = form_class(request.POST, instance=object)
    else:
        form = form_class(instance=object)
    return form

def should_update_primary_key(object, form):
    return object and object.id != form.cleaned_data['id']

def primary_key_update(object, form):
    from django.db import connection
    cur = connection.cursor()

    table = object._meta.db_table
    pk_col = object._meta.get_field('id').db_column
    old_pk_val = getattr(object, object._meta.get_field('id').attname)
    new_pk_val = form.cleaned_data['id']

    sql = 'UPDATE "%s" ' % table
    sql += 'SET "%s" = %%s ' % pk_col
    sql += 'WHERE "%s" = %%s' % pk_col

    params = (new_pk_val, old_pk_val)
    cur.execute(sql, params)

    return new_pk_val

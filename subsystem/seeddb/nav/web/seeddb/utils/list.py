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
from nav.models.manage import Netbox, Room

from nav.web.seeddb.forms import *

ITEMS_PER_PAGE = 100
TITLE_DEFAULT = 'NAV - Seed Database'
NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def get_num(get, key, default=1):
    try:
        return int(get.get(key, default))
    except ValueError:
        return default

class SeeddbList(object):
    model = None
    value_list = None
    edit_url = ''
    edit_url_attr = 'pk'
    filter_form_model = None
    template = 'seeddb/list.html'
    title = TITLE_DEFAULT
    caption = ''
    navpath = NAVPATH_DEFAULT
    tab_template = ''

    def __init__(self, request):
        self.request = request
        self.queryset = self.model.objects.all()

        if self.filter_form_model:
            self.filter_form = self.filter_form_model(request.GET)

    def __call__(self, extra_context={}):
        queryset = self.queryset
        queryset = self._filter_query(queryset)
        queryset = self._order_query(queryset)

        value_queryset = queryset.values('pk', self.edit_url_attr, *self.value_list)
        page = self._paginate(value_queryset)
        objects = self._process_objects(page)
        labels = self._label()

        context = {
            'object_list': objects,
            'labels': labels,
            'current_sort': self.order_by,
            'current_sort_label': self.current_sort_label,
            'other_sort': self.other_sort,
            'sort_asc': self.sort_asc,
            'filter_form': self.filter_form,
            'page': page,
            'active': {'list': True},
            'title': self.title,
            'caption': self.caption,
            'navpath': self.navpath,
            'tab_template': self.tab_template,
        }
        extra_context.update(context)
        return render_to_response(self.template,
            extra_context, RequestContext(self.request))

    def _filter_query(self, queryset):
        if self.filter_form and self.filter_form.is_valid():
            filter = dict([(key, value) for key, value in self.filter_form.cleaned_data.items() if value])
            queryset = queryset.filter(**filter)
        return queryset

    def _order_query(self, queryset):
        order_by = self.request.GET.get('sort')
        if not order_by or order_by.find('-') not in (-1, 0) or order_by.lstrip('-') not in self.value_list:
            order_by = self.value_list[0]

        self.order_by = order_by
        self.sort_asc = '-' not in order_by
        self.current_sort_label = order_by.lstrip('-')
        self.other_sort = self.sort_asc and '-' + order_by or order_by.lstrip('-')

        return queryset.order_by(self.order_by)

    def _paginate(self, value_qs):
        self.per_page = self.request.GET.get('per_page', ITEMS_PER_PAGE)
        if self.per_page == 'all':
            self.per_page = value_qs.count()
        else:
            self_per_page = get_num(self.request.GET, 'per_page', ITEMS_PER_PAGE)
        self.page_num = get_num(self.request.GET, 'page', 1)

        paginator = Paginator(value_qs, self.per_page)
        try:
            page = paginator.page(self.page_num)
        except InvalidPage:
            page = paginator.page(paginator.num_pages)
        return page

    def _process_objects(self, page):
        objects = []
        for object in page.object_list:
            row = {
                'pk': object['pk'],
                'url': reverse(self.edit_url, args=(object[self.edit_url_attr],)),
                'values_list': [object[attr] for attr in self.value_list],
            }
            objects.append(row)
        return objects

    def _label(self):
        labels = [get_verbose_name(self.model, value) for value in self.value_list]
        return zip(labels, self.value_list)

class NetboxList(SeeddbList):
    model = Netbox
    value_list = (
        'sysname', 'room', 'ip', 'category', 'organization', 'read_only',
        'read_write', 'type__name', 'device__serial')
    edit_url = 'seeddb-netbox-edit'
    edit_url_attr = 'sysname'
    filter_form_model = NetboxFilterForm
    title = TITLE_DEFAULT + ' - IP Devices'
    caption = 'IP Devices'
    navpath = NAVPATH_DEFAULT + [('IP Devices', None)]
    tab_template = 'seeddb/tabs_netbox.html'

class RoomList(SeeddbList):
    model = Room
    value_list = (
        'id', 'location', 'description', 'optional_1', 'optional_2',
        'optional_3', 'optional_4')
    edit_url = 'seeddb-room-edit'
    edit_url_attr = 'pk'
    filter_form_model = RoomFilterForm
    title = TITLE_DEFAULT + ' - Rooms'
    caption = 'Rooms'
    navpath = NAVPATH_DEFAULT + [('Rooms', None)]
    tab_template = 'seeddb/tabs_room.html'

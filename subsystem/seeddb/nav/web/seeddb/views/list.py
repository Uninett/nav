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
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix
from nav.models.service import Service

from nav.web.seeddb.forms import NetboxFilterForm, RoomFilterForm
from nav.web.seeddb.utils import get_verbose_name

ITEMS_PER_PAGE = 100
TITLE_DEFAULT = 'NAV - Seed Database'
NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def get_num(get, key, default=1):
    try:
        num = int(get.get(key, default))
    except ValueError:
        num = default
    return num

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

    def __new__(cls, request):
        obj = super(SeeddbList, cls).__new__(cls)
        return obj(request)

    def __call__(self, request):
        self.request = request
        self.queryset = self._init_queryset(self.model)

        self.filter_form = None
        if self.filter_form_model:
            self.filter_form = self.filter_form_model(request.GET)

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
        return render_to_response(self.template,
            context, RequestContext(self.request))

    def _init_queryset(self, model):
        return model.objects.all()

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
            self.per_page = get_num(self.request.GET, 'per_page', ITEMS_PER_PAGE)
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

class ServiceList(SeeddbList):
    model = Service
    value_list = ('netbox__sysname', 'handler', 'version')
    edit_url = 'seeddb-service-edit'
    title = TITLE_DEFAULT + ' - Services'
    caption = 'Services'
    navpath = NAVPATH_DEFAULT + [('Services', None)]
    tab_template = 'seeddb/tabs_service.html'

class RoomList(SeeddbList):
    model = Room
    value_list = (
        'id', 'location', 'description', 'optional_1', 'optional_2',
        'optional_3', 'optional_4')
    edit_url = 'seeddb-room-edit'
    filter_form_model = RoomFilterForm
    title = TITLE_DEFAULT + ' - Rooms'
    caption = 'Rooms'
    navpath = NAVPATH_DEFAULT + [('Rooms', None)]
    tab_template = 'seeddb/tabs_room.html'

class LocationList(SeeddbList):
    model = Location
    value_list = ('id', 'description')
    edit_url = 'seeddb-location-edit'
    title = TITLE_DEFAULT + ' - Locations'
    caption = 'Locations'
    navpath = NAVPATH_DEFAULT + [('Locations', None)]
    tab_template = 'seeddb/tabs_location.html'

class OrganizationList(SeeddbList):
    model = Organization
    value_list = (
        'id', 'parent', 'description', 'optional_1', 'optional_2',
        'optional_3')
    edit_url = 'seeddb-organization-edit'
    title = TITLE_DEFAULT + ' - Organizations'
    caption = 'Organizations'
    navpath = NAVPATH_DEFAULT + [('Organizations', None)]
    tab_template = 'seeddb/tabs_organization.html'

class UsageList(SeeddbList):
    model = Usage
    value_list = ('id', 'description')
    edit_url = 'seeddb-usage-edit'
    title = TITLE_DEFAULT + ' - Usage categories'
    caption = 'Usage categories'
    navpath = NAVPATH_DEFAULT + [('Usage categories', None)]
    tab_template = 'seeddb/tabs_usage.html'

class NetboxTypeList(SeeddbList):
    model = NetboxType
    value_list = (
        'name', 'vendor', 'description', 'sysobjectid', 'frequency', 'cdp',
        'tftp')
    edit_url = 'seeddb-type-edit'
    title = TITLE_DEFAULT + ' - Types'
    caption = 'Types'
    navpath = NAVPATH_DEFAULT + [('Types', None)]
    tab_template = 'seeddb/tabs_type.html'

class VendorList(SeeddbList):
    model = Vendor
    value_list = ('id',)
    edit_url = 'seeddb-vendor-edit'
    title = TITLE_DEFAULT + ' - Vendors'
    caption = 'Vendors'
    navpath = NAVPATH_DEFAULT + [('Vendors', None)]
    tab_template = 'seeddb/tabs_vendor.html'

class SubcategoryList(SeeddbList):
    model = Subcategory
    value_list = ('id', 'category', 'description')
    edit_url = 'seeddb-subcategory-edit'
    title = TITLE_DEFAULT + ' - Subcategories'
    caption = 'Subcategories'
    navpath = NAVPATH_DEFAULT + [('Subcategories', None)]
    tab_template = 'seeddb/tabs_subcategory.html'

class VlanList(SeeddbList):
    model = Vlan
    value_list = (
        'id', 'vlan', 'net_type', 'organization', 'usage', 'net_ident',
        'description')
    edit_url = 'seeddb-vlan-edit'
    title = TITLE_DEFAULT + ' - Vlan'
    caption = 'Vlan'
    navpath = NAVPATH_DEFAULT + [('Vlan', None)]
    tab_template = 'seeddb/tabs_vlan.html'

class PrefixList(SeeddbList):
    model = Prefix
    value_list = (
        'net_address', 'vlan__net_type', 'vlan__organization',
        'vlan__net_ident', 'vlan__usage', 'vlan__description', 'vlan__vlan')
    edit_url = 'seeddb-prefix-edit'
    title = TITLE_DEFAULT + ' - Prefix'
    caption = 'Prefix'
    navpath = NAVPATH_DEFAULT + [('Prefix', None)]
    tab_template = 'seeddb/tabs_prefix.html'

    def _init_queryset(self, model):
        return model.objects.filter(vlan__net_type__edit=True)

class CablingList(SeeddbList):
    model = Cabling
    value_list = (
        'room', 'jack', 'building', 'target_room', 'category', 'description')
    edit_url = 'seeddb-cabling-edit'
    title = TITLE_DEFAULT + ' - Cabling'
    caption = 'Cabling'
    navpath = NAVPATH_DEFAULT + [('Cabling', None)]
    tab_template = 'seeddb/tabs_cabling.html'

class PatchList(SeeddbList):
    model = Patch
    value_list = (
        'interface__netbox', 'interface__module', 'interface__baseport',
        'cabling__room', 'cabling__jack', 'split')
    edit_url = 'seeddb-patch-edit'
    title = TITLE_DEFAULT + ' - Patch'
    caption = 'Patch'
    navpath = NAVPATH_DEFAULT + [('Patch', None)]
    tab_template = 'seeddb/tabs_patch.html'

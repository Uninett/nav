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

from django.conf.urls.defaults import *

from nav.web.seeddb.views import *
from nav.web.seeddb.views.common import *

dummy = lambda *args, **kwargs: None

urlpatterns = patterns('',
    url(r'^$', index,
        name='seeddb-index'),

    # Netbox
    url(r'^netbox/$', NetboxList,
        name='seeddb-netbox'),
    url(r'^netbox/edit/(?P<netbox_sysname>[\w\d.-]+)/', netbox_edit,
        name='seeddb-netbox-edit'),
    url(r'^netbox/add/$', netbox_edit,
        name='seeddb-netbox-edit'),
    url(r'^netbox/bulk/$', dummy,
        name='seeddb-netbox-bulk'),

    # Service
    url(r'^service/$', ServiceList,
        name='seeddb-service'),
    url(r'^service/edit/(?P<service>[\d]+)$', ServiceEdit,
        name='seeddb-service-edit'),
    url(r'^service/add/$', ServiceEdit,
        name='seeddb-service-edit'),
    url(r'^service/bulk/$', dummy,
        name='seeddb-service-bulk'),

    # Room
    url(r'^room/$', RoomList,
        name='seeddb-room'),
    url(r'^room/edit/(?P<room_id>[\w\d_-]+)/$', RoomEdit,
        name='seeddb-room-edit'),
    url(r'^room/add/$', RoomEdit,
        name='seeddb-room-edit'),
    url(r'^room/bulk/$', dummy,
        name='seeddb-room-bulk'),
    url(r'^room/move/$', room_move,
        name='seeddb-room-move'),

    # Location
    url(r'^location/$', LocationList,
        name='seeddb-location'),
    url(r'^location/edit/(?P<location_id>[\w\d_-]+)/$', LocationEdit,
        name='seeddb-location-edit'),
    url(r'^location/add/$', LocationEdit,
        name='seeddb-location-edit'),
    url(r'^location/bulk/$', dummy,
        name='seeddb-location-bulk'),

    # Organization
    url(r'^organization/$', OrganizationList,
        name='seeddb-organization'),
    url(r'^organization/edit/(?P<organization_id>[\w\d_-]+)/$', OrganizationEdit,
        name='seeddb-organization-edit'),
    url(r'^organization/add/$', OrganizationEdit,
        name='seeddb-organization-edit'),
    url(r'^organization/bulk/$', dummy,
        name='seeddb-organization-bulk'),

    # Usage category
    url(r'^usage/$', UsageList,
        name='seeddb-usage'),
    url(r'^usage/edit/(?P<usage_id>[\w\d_-]+)/$', UsageEdit,
        name='seeddb-usage-edit'),
    url(r'^usage/add/$', UsageEdit,
        name='seeddb-usage-edit'),
    url(r'^usage/bulk/$', dummy,
        name='seeddb-usage-bulk'),

    # Type
    url(r'^type/$', NetboxTypeList,
        name='seeddb-type'),
    url(r'^type/edit/(?P<type_id>[\d]+)/$', NetboxTypeEdit,
        name='seeddb-type-edit'),
    url(r'^type/add/$', NetboxTypeEdit,
        name='seeddb-type-edit'),
    url(r'^type/bulk/$', dummy,
        name='seeddb-type-bulk'),

    # Vendor
    url(r'^vendor/$', VendorList,
        name='seeddb-vendor'),
    url(r'^vendor/edit/(?P<vendor_id>[\w\d]+)/$', VendorEdit,
        name='seeddb-vendor-edit'),
    url(r'^vendor/add/$', VendorEdit,
        name='seeddb-vendor-edit'),
    url(r'^vendor/bulk/$', dummy,
        name='seeddb-vendor-bulk'),

    # SNMPoid

    # Subcategory
    url(r'^subcategory/$', SubcategoryList,
        name='seeddb-subcategory'),
    url(r'^subcategory/edit/(?P<subcategory_id>[\w\d-]+)/$', SubcategoryEdit,
        name='seeddb-subcategory-edit'),
    url(r'^subcategory/add/$', SubcategoryEdit,
        name='seeddb-subcategory-edit'),
    url(r'^subcategory/bulk/$', dummy,
        name='seeddb-subcategory-bulk'),

    # Vlan
    url(r'^vlan/$', VlanList,
        name='seeddb-vlan'),
    url(r'^vlan/edit/(?P<vlan_id>[\d]+)/$', VlanEdit,
        name='seeddb-vlan-edit'),

    # Prefix
    url(r'^prefix/$', PrefixList,
        name='seeddb-prefix'),
    url(r'^prefix/edit/(?P<prefix_id>[\d]+)/$', PrefixEdit,
        name='seeddb-prefix-edit'),
    url(r'^prefix/add/$', PrefixEdit,
        name='seeddb-prefix-edit'),
    url(r'^prefix/bulk/$', dummy,
        name='seeddb-prefix-bulk'),

    # Cabling
    url(r'^cabling/$', CablingList,
        name='seeddb-cabling'),
    url(r'^cabling/edit/(?P<cabling>[\d]+)/$', CablingEdit,
        name='seeddb-cabling-edit'),
    url(r'^cabling/add/$', CablingEdit,
        name='seeddb-cabling-edit'),
    url(r'^cabling/bulk/$', dummy,
        name='seeddb-cabling-bulk'),

    # Patch
    url(r'^patch/$', PatchList,
        name='seeddb-patch'),
    url(r'^patch/edit/(?P<patch>[\d]+)/$', PatchEdit,
        name='seeddb-patch-edit'),
    url(r'^patch/add/$', PatchEdit,
        name='seeddb-patch-edit'),
    url(r'^patch/bulk/$', dummy,
        name='seeddb-patch-bulk'),
)

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

dummy = lambda *args, **kwargs: None

urlpatterns = patterns('',
    url(r'^$', index,
        name='seeddb-index'),

    # Netbox
    url(r'^netbox/$', netbox_list,
        name='seeddb-netbox'),
    url(r'^netbox/edit/(?P<netbox_sysname>[\w\d.-]+)/', dummy,
        name='seeddb-netbox-edit'),
    url(r'^netbox/add/$', dummy,
        name='seeddb-netbox-edit'),
    url(r'^netbox/bulk/$', dummy,
        name='seeddb-netbox-bulk'),

    # Service
    url(r'^service/$', service_list,
        name='seeddb-service'),
    url(r'^service/edit/(?P<service>[\d]+)$', dummy,
        name='seeddb-service-edit'),
    url(r'^service/add/$', dummy,
        name='seeddb-service-edit'),
    url(r'^service/bulk/$', dummy,
        name='seeddb-service-bulk'),

    # Room
    url(r'^room/$', room_list,
        name='seeddb-room'),
    url(r'^room/edit/(?P<room_id>[\w\d_-]+)/$', room_edit,
        name='seeddb-room-edit'),
    url(r'^room/add/$', room_edit,
        name='seeddb-room-edit'),
    url(r'^room/bulk/$', dummy,
        name='seeddb-room-bulk'),

    # Location
    url(r'^location/$', location_list,
        name='seeddb-location'),
    url(r'^location/edit/(?P<location_id>[\w\d_-]+)/$', location_edit,
        name='seeddb-location-edit'),
    url(r'^location/add/$', location_edit,
        name='seeddb-location-edit'),
    url(r'^location/bulk/$', dummy,
        name='seeddb-location-bulk'),

    # Organization
    url(r'^organization/$', organization_list,
        name='seeddb-organization'),
    url(r'^organization/edit/(?P<organization_id>[\w\d_-]+)/$', organization_edit,
        name='seeddb-organization-edit'),
    url(r'^organization/add/$', organization_edit,
        name='seeddb-organization-edit'),
    url(r'^organization/bulk/$', dummy,
        name='seeddb-organization-bulk'),

    # Usage category
    url(r'^usage/$', usage_list,
        name='seeddb-usage'),
    url(r'^usage/edit/(?P<usage_id>[\w\d_-]+)/$', usage_edit,
        name='seeddb-usage-edit'),
    url(r'^usage/add/$', usage_edit,
        name='seeddb-usage-edit'),
    url(r'^usage/bulk/$', dummy,
        name='seeddb-usage-bulk'),

    # Type
    url(r'^type/$', type_list,
        name='seeddb-type'),
    url(r'^type/edit/(?P<type>[\d]+)/$', dummy, 
        name='seeddb-type-edit'),
    url(r'^type/add/$', dummy,
        name='seeddb-type-edit'),
    url(r'^type/bulk/$', dummy,
        name='seeddb-type-bulk'),

    # Vendor
    url(r'^vendor/$', vendor_list,
        name='seeddb-vendor'),
    url(r'^vendor/edit/(?P<vendor>[\w\d]+)/$', dummy,
        name='seeddb-vendor-edit'),
    url(r'^vendor/add/$', dummy,
        name='seeddb-vendor-edit'),
    url(r'^vendor/bulk/$', dummy,
        name='seeddb-vendor-bulk'),

    # SNMPoid

    # Subcategory
    url(r'^subcategory/$', subcategory_list,
        name='seeddb-subcategory'),
    url(r'^subcategory/edit/(?P<subcategory>[\w\d-]+)/$', dummy,
        name='seeddb-subcategory-edit'),
    url(r'^subcategory/add/$', dummy,
        name='seeddb-subcategory-edit'),
    url(r'^subcategory/bulk/$', dummy,
        name='seeddb-subcategory-bulk'),

    # Vlan
    url(r'^vlan/$', vlan_list,
        name='seeddb-vlan'),
    url(r'^vlan/edit/(?P<vlan>[\d]+)/$', dummy,
        name='seeddb-vlan-edit'),

    # Prefix
    url(r'^prefix/$', prefix_list,
        name='seeddb-prefix'),
    url(r'^prefix/edit/(?P<prefix>[\d]+)/$', dummy,
        name='seeddb-prefix-edit'),
    url(r'^prefix/add/$', dummy,
        name='seeddb-prefix-edit'),
    url(r'^prefix/bulk/$', dummy,
        name='seeddb-prefix-bulk'),

    # Cabling
    url(r'^cabling/$', cabling_list,
        name='seeddb-cabling'),
    url(r'^cabling/edit/(?P<cabling>[\d]+)/$', dummy,
        name='seeddb-cabling-edit'),
    url(r'^cabling/add/$', dummy,
        name='seeddb-cabling-edit'),
    url(r'^cabling/bulk/$', dummy,
        name='seeddb-cabling-bulk'),

    # Patch
    url(r'^patch/$', patch_list,
        name='seeddb-patch'),
    url(r'^patch/edit/(?P<patch>[\d]+)/$', dummy,
        name='seeddb-patch-edit'),
    url(r'^patch/add/$', dummy,
        name='seeddb-patch-edit'),
    url(r'^patch/bulk/$', dummy,
        name='seeddb-patch-bulk'),
)

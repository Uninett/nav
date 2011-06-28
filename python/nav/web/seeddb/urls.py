#
# Copyright (C) 2011 UNINETT AS
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
"""SeedDB Django URL config"""

from django.conf.urls.defaults import patterns, url

from nav.web.seeddb.page import index
from nav.web.seeddb.page.room import room, room_edit, room_bulk
from nav.web.seeddb.page.location import location, location_edit, location_bulk
from nav.web.seeddb.page.organization import organization, organization_edit
from nav.web.seeddb.page.organization import organization_bulk
from nav.web.seeddb.page.usage import usage, usage_edit, usage_bulk
from nav.web.seeddb.page.netboxtype import netboxtype, netboxtype_edit
from nav.web.seeddb.page.netboxtype import netboxtype_bulk
from nav.web.seeddb.page.vendor import vendor, vendor_edit, vendor_bulk
from nav.web.seeddb.page.subcategory import subcategory, subcategory_edit
from nav.web.seeddb.page.subcategory import subcategory_bulk
from nav.web.seeddb.page.vlan import vlan_list, vlan_edit
from nav.web.seeddb.page.prefix import prefix, prefix_edit, prefix_bulk
from nav.web.seeddb.page.cabling import cabling, cabling_edit, cabling_bulk
from nav.web.seeddb.page.patch import patch, patch_edit, patch_bulk
from nav.web.seeddb.page.netbox import netbox, netbox_bulk
from nav.web.seeddb.page.netbox.edit import netbox_edit
from nav.web.seeddb.page.service import service, service_bulk
from nav.web.seeddb.page.service.edit import service_edit

urlpatterns = patterns('',
    url(r'^$', index,
        name='seeddb-index'),

    # Netbox
    url(r'^netbox/$', netbox,
        name='seeddb-netbox'),
    url(r'^netbox/edit/(?P<netbox_id>(\d+))/', netbox_edit,
        name='seeddb-netbox-edit'),
    url(r'^netbox/add/$', netbox_edit,
        name='seeddb-netbox-edit'),
    url(r'^netbox/bulk/$', netbox_bulk,
        name='seeddb-netbox-bulk'),

    # Service
    url(r'^service/$', service,
        name='seeddb-service'),
    url(r'^service/edit/(?P<service_id>[\d]+)$', service_edit,
        name='seeddb-service-edit'),
    url(r'^service/add/$', service_edit,
        name='seeddb-service-edit'),
    url(r'^service/bulk/$', service_bulk,
        name='seeddb-service-bulk'),

    # Room
    url(r'^room/$', room,
        name='seeddb-room'),
    url(r'^room/edit/(?P<room_id>[^/]+)/$', room_edit,
        name='seeddb-room-edit'),
    url(r'^room/add/$', room_edit,
        name='seeddb-room-edit'),
    url(r'^room/bulk/$', room_bulk,
        name='seeddb-room-bulk'),

    # Location
    url(r'^location/$', location,
        name='seeddb-location'),
    url(r'^location/edit/(?P<location_id>[^/]+)/$', location_edit,
        name='seeddb-location-edit'),
    url(r'^location/add/$', location_edit,
        name='seeddb-location-edit'),
    url(r'^location/bulk/$', location_bulk,
        name='seeddb-location-bulk'),

    # Organization
    url(r'^organization/$', organization,
        name='seeddb-organization'),
    url(r'^organization/edit/(?P<organization_id>[^/]+)/$', organization_edit,
        name='seeddb-organization-edit'),
    url(r'^organization/add/$', organization_edit,
        name='seeddb-organization-edit'),
    url(r'^organization/bulk/$', organization_bulk,
        name='seeddb-organization-bulk'),

    # Usage category
    url(r'^usage/$', usage,
        name='seeddb-usage'),
    url(r'^usage/edit/(?P<usage_id>[^/]+)/$', usage_edit,
        name='seeddb-usage-edit'),
    url(r'^usage/add/$', usage_edit,
        name='seeddb-usage-edit'),
    url(r'^usage/bulk/$', usage_bulk,
        name='seeddb-usage-bulk'),

    # Type
    url(r'^type/$', netboxtype,
        name='seeddb-type'),
    url(r'^type/edit/(?P<type_id>[\d]+)/$', netboxtype_edit,
        name='seeddb-type-edit'),
    url(r'^type/add/$', netboxtype_edit,
        name='seeddb-type-edit'),
    url(r'^type/bulk/$', netboxtype_bulk,
        name='seeddb-type-bulk'),

    # Vendor
    url(r'^vendor/$', vendor,
        name='seeddb-vendor'),
    url(r'^vendor/edit/(?P<vendor_id>[^/]+)/$', vendor_edit,
        name='seeddb-vendor-edit'),
    url(r'^vendor/add/$', vendor_edit,
        name='seeddb-vendor-edit'),
    url(r'^vendor/bulk/$', vendor_bulk,
        name='seeddb-vendor-bulk'),

    # SNMPoid

    # Subcategory
    url(r'^subcategory/$', subcategory,
        name='seeddb-subcategory'),
    url(r'^subcategory/edit/(?P<subcategory_id>[^/]+)/$', subcategory_edit,
        name='seeddb-subcategory-edit'),
    url(r'^subcategory/add/$', subcategory_edit,
        name='seeddb-subcategory-edit'),
    url(r'^subcategory/bulk/$', subcategory_bulk,
        name='seeddb-subcategory-bulk'),

    # Vlan
    url(r'^vlan/$', vlan_list,
        name='seeddb-vlan'),
    url(r'^vlan/edit/(?P<vlan_id>[\d]+)/$', vlan_edit,
        name='seeddb-vlan-edit'),

    # Prefix
    url(r'^prefix/$', prefix,
        name='seeddb-prefix'),
    url(r'^prefix/edit/(?P<prefix_id>[\d]+)/$', prefix_edit,
        name='seeddb-prefix-edit'),
    url(r'^prefix/add/$', prefix_edit,
        name='seeddb-prefix-edit'),
    url(r'^prefix/bulk/$', prefix_bulk,
        name='seeddb-prefix-bulk'),

    # Cabling
    url(r'^cabling/$', cabling,
        name='seeddb-cabling'),
    url(r'^cabling/edit/(?P<cabling_id>[\d]+)/$', cabling_edit,
        name='seeddb-cabling-edit'),
    url(r'^cabling/add/$', cabling_edit,
        name='seeddb-cabling-edit'),
    url(r'^cabling/bulk/$', cabling_bulk,
        name='seeddb-cabling-bulk'),

    # Patch
    url(r'^patch/$', patch,
        name='seeddb-patch'),
    url(r'^patch/edit/(?P<patch_id>[\d]+)/$', patch_edit,
        name='seeddb-patch-edit'),
    url(r'^patch/add/$', patch_edit,
        name='seeddb-patch-edit'),
    url(r'^patch/bulk/$', patch_bulk,
        name='seeddb-patch-bulk'),
)

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
"""SeedDB Django URL config"""

from django.urls import path
from django.urls import re_path

from nav.web.seeddb import page
from nav.web.seeddb.page import netbox
from nav.web.seeddb.page.netbox import edit as netbox_edit
from nav.web.seeddb.page import service
from nav.web.seeddb.page.service import edit as service_edit
from nav.web.seeddb.page import room
from nav.web.seeddb.page.management_profile import (
    management_profile,
    management_profile_edit,
    management_profile_delete,
    management_profile_bulk,
)
from nav.web.seeddb.page import location
from nav.web.seeddb.page import organization
from nav.web.seeddb.page import usage
from nav.web.seeddb.page import netboxtype
from nav.web.seeddb.page import vendor
from nav.web.seeddb.page import netboxgroup
from nav.web.seeddb.page import vlan
from nav.web.seeddb.page import prefix
from nav.web.seeddb.page import cabling
from nav.web.seeddb.page import patch


urlpatterns = [
    path('', page.index, name='seeddb-index'),
    # Netbox
    path('netbox/', netbox.netbox, name='seeddb-netbox'),
    re_path(
        r'^netbox/edit/(?P<netbox_id>(\d+))/',
        netbox_edit.netbox_edit,
        name='seeddb-netbox-edit',
    ),
    re_path(
        r'^netbox/delete/(?P<object_id>(\d+))/',
        netbox.netbox_delete,
        name='seeddb-netbox-delete',
    ),
    path(
        'netbox/add/<path:suggestion>',
        netbox_edit.netbox_edit,
        name='seeddb-netbox-add-suggestion',
    ),
    path('netbox/add/', netbox_edit.netbox_edit, name='seeddb-netbox-edit'),
    re_path(
        r'^netbox/(?P<action>copy)/(?P<netbox_id>(\d+))/',
        netbox_edit.netbox_edit,
        name='seeddb-netbox-copy',
    ),
    path('netbox/bulk/', netbox.netbox_bulk, name='seeddb-netbox-bulk'),
    path(
        'netbox/check-connectivity/load/',
        netbox_edit.load_connectivity_test_results,
        name='seeddb-netbox-check-connectivity-load',
    ),
    path(
        'netbox/check-connectivity/',
        netbox_edit.check_connectivity,
        name='seeddb-netbox-check-connectivity',
    ),
    re_path(
        r'^netbox/validate-ip-address/',
        netbox_edit.validate_ip_address,
        name='seeddb-netbox-validate-ip-address',
    ),
    # Management Profile
    path('management-profile/', management_profile, name='seeddb-management-profile'),
    path(
        'management-profile/edit/<str:management_profile_id>/',
        management_profile_edit,
        name='seeddb-management-profile-edit',
    ),
    path(
        'management-profile/delete/<str:object_id>/',
        management_profile_delete,
        name='seeddb-management-profile-delete',
    ),
    path(
        'management-profile/add/',
        management_profile_edit,
        name='seeddb-management-profile-edit',
    ),
    path(
        'management-profile/bulk/',
        management_profile_bulk,
        name='seeddb-management-profile-bulk',
    ),
    # Service
    path('service/', service.service, name='seeddb-service'),
    path(
        'service/edit/<int:service_id>',
        service_edit.service_edit,
        name='seeddb-service-edit',
    ),
    path(
        'service/delete/<int:object_id>',
        service.service_delete,
        name='seeddb-service-delete',
    ),
    path('service/add/', service_edit.service_edit, name='seeddb-service-edit'),
    path('service/bulk/', service.service_bulk, name='seeddb-service-bulk'),
    # Room
    path('room/', room.room, name='seeddb-room'),
    path('room/edit/<path:room_id>/', room.room_edit, name='seeddb-room-edit'),
    path('room/delete/<path:object_id>/', room.room_delete, name='seeddb-room-delete'),
    re_path(
        r'^room/(?P<action>copy)/(?P<room_id>.+)/$',
        room.room_edit,
        name='seeddb-room-copy',
    ),
    path('room/add/', room.room_edit, name='seeddb-room-edit'),
    path('room/add/<str:lat>/<str:lon>/', room.room_edit, name='seeddb-room-edit'),
    path('room/bulk/', room.room_bulk, name='seeddb-room-bulk'),
    # Location
    path('location/', location.location, name='seeddb-location'),
    path(
        'location/edit/<path:location_id>/',
        location.location_edit,
        name='seeddb-location-edit',
    ),
    path(
        'location/delete/<path:object_id>/',
        location.location_delete,
        name='seeddb-location-delete',
    ),
    path('location/add/', location.location_edit, name='seeddb-location-edit'),
    re_path(
        r'^location/(?P<action>copy)/(?P<location_id>.+)/$',
        location.location_edit,
        name='seeddb-location-copy',
    ),
    path('location/bulk/', location.location_bulk, name='seeddb-location-bulk'),
    # Organization
    path('organization/', organization.organization, name='seeddb-organization'),
    path(
        'organization/edit/<path:organization_id>/',
        organization.organization_edit,
        name='seeddb-organization-edit',
    ),
    path(
        'organization/delete/<path:object_id>/',
        organization.organization_delete,
        name='seeddb-organization-delete',
    ),
    path(
        'organization/add/',
        organization.organization_edit,
        name='seeddb-organization-edit',
    ),
    path(
        'organization/bulk/',
        organization.organization_bulk,
        name='seeddb-organization-bulk',
    ),
    # Usage category
    path('usage/', usage.usage, name='seeddb-usage'),
    path('usage/edit/<path:usage_id>/', usage.usage_edit, name='seeddb-usage-edit'),
    path(
        'usage/delete/<path:object_id>/',
        usage.usage_delete,
        name='seeddb-usage-delete',
    ),
    path('usage/add/', usage.usage_edit, name='seeddb-usage-edit'),
    path('usage/bulk/', usage.usage_bulk, name='seeddb-usage-bulk'),
    # Type
    path('type/', netboxtype.netboxtype, name='seeddb-type'),
    path(
        'type/edit/<int:type_id>/',
        netboxtype.netboxtype_edit,
        name='seeddb-type-edit',
    ),
    path(
        'type/delete/<int:object_id>/',
        netboxtype.netboxtype_delete,
        name='seeddb-type-delete',
    ),
    path('type/add/', netboxtype.netboxtype_edit, name='seeddb-type-edit'),
    path('type/bulk/', netboxtype.netboxtype_bulk, name='seeddb-type-bulk'),
    # Vendor
    path('vendor/', vendor.vendor, name='seeddb-vendor'),
    path('vendor/add/', vendor.vendor_edit, name='seeddb-vendor-edit'),
    path('vendor/bulk/', vendor.vendor_bulk, name='seeddb-vendor-bulk'),
    # Netbox Group
    path('netboxgroup/', netboxgroup.netboxgroup, name='seeddb-netboxgroup'),
    path(
        'netboxgroup/edit/<path:netboxgroup_id>/',
        netboxgroup.netboxgroup_edit,
        name='seeddb-netboxgroup-edit',
    ),
    path(
        'netboxgroup/delete/<path:object_id>/',
        netboxgroup.netboxgroup_delete,
        name='seeddb-netboxgroup-delete',
    ),
    path(
        'netboxgroup/add/',
        netboxgroup.netboxgroup_edit,
        name='seeddb-netboxgroup-edit',
    ),
    path(
        'netboxgroup/bulk/',
        netboxgroup.netboxgroup_bulk,
        name='seeddb-netboxgroup-bulk',
    ),
    # Vlan
    path('vlan/', vlan.vlan_list, name='seeddb-vlan'),
    path('vlan/edit/<int:vlan_id>/', vlan.vlan_edit, name='seeddb-vlan-edit'),
    # Prefix
    path('prefix/', prefix.get_prefix_view, name='seeddb-prefix'),
    path(
        'prefix/edit/<int:prefix_id>/',
        prefix.prefix_edit,
        name='seeddb-prefix-edit',
    ),
    path(
        'prefix/delete/<int:object_id>/',
        prefix.prefix_delete,
        name='seeddb-prefix-delete',
    ),
    path('prefix/add/', prefix.prefix_edit, name='seeddb-prefix-edit'),
    path('prefix/bulk/', prefix.prefix_bulk, name='seeddb-prefix-bulk'),
    # Cabling
    path('cabling/', cabling.cabling, name='seeddb-cabling'),
    path('cabling/edit/', cabling.cabling_edit, name='seeddb-cabling-edit'),
    path(
        'cabling/delete/<int:object_id>/',
        cabling.cabling_delete,
        name='seeddb-cabling-delete',
    ),
    path('cabling/add/', cabling.cabling_edit, name='seeddb-cabling-add'),
    path('cabling/bulk/', cabling.cabling_bulk, name='seeddb-cabling-bulk'),
    # Patch
    path('patch/', patch.patch, name='seeddb-patch'),
    path('patch/edit/', patch.patch_edit, name='seeddb-patch-edit'),
    path(
        'patch/edit/show-modal/',
        patch.patch_show_modal,
        name='seeddb-show-patch-modal',
    ),
    path('patch/delete/', patch.patch_delete, name='seeddb-patch-delete'),
    path('patch/bulk/', patch.patch_bulk, name='seeddb-patch-bulk'),
    # XXX: too greedy
    re_path(r'^patch/save/', patch.patch_save, name='seeddb-patch-save'),
    re_path(r'^patch/remove/', patch.patch_remove, name='seeddb-patch-remove'),
    re_path(r'^patch/loadcell/', patch.load_cell, name='seeddb-patch-load-cell'),
]

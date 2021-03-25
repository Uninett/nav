#
# Copyright (C) 2011 Uninett AS
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

from django.conf.urls import url

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
    url(r'^$', page.index, name='seeddb-index'),
    # Netbox
    url(r'^netbox/$', netbox.netbox, name='seeddb-netbox'),
    url(
        r'^netbox/edit/(?P<netbox_id>(\d+))/',
        netbox_edit.netbox_edit,
        name='seeddb-netbox-edit',
    ),
    url(
        r'^netbox/delete/(?P<object_id>(\d+))/',
        netbox.netbox_delete,
        name='seeddb-netbox-delete',
    ),
    url(
        r'^netbox/add/(?P<suggestion>.+)$',
        netbox_edit.netbox_edit,
        name='seeddb-netbox-add-suggestion',
    ),
    url(r'^netbox/add/$', netbox_edit.netbox_edit, name='seeddb-netbox-edit'),
    url(
        r'^netbox/(?P<action>copy)/(?P<netbox_id>(\d+))/',
        netbox_edit.netbox_edit,
        name='seeddb-netbox-copy',
    ),
    url(r'^netbox/bulk/$', netbox.netbox_bulk, name='seeddb-netbox-bulk'),
    url(
        r'^netbox/get-read-only-variables/$',
        netbox_edit.get_read_only_variables,
        name='seeddb-netbox-get-readonly',
    ),
    url(
        r'^netbox/get-address-info/',
        netbox_edit.get_address_info,
        name='seeddb-netbox-get-address-info',
    ),
    # Management Profile
    url(r'^management-profile/$', management_profile, name='seeddb-management-profile'),
    url(
        r'^management-profile/edit/(?P<management_profile_id>.+)/$',
        management_profile_edit,
        name='seeddb-management-profile-edit',
    ),
    url(
        r'^management-profile/delete/(?P<object_id>.+)/$',
        management_profile_delete,
        name='seeddb-management-profile-delete',
    ),
    url(
        r'^management-profile/add/$',
        management_profile_edit,
        name='seeddb-management-profile-edit',
    ),
    url(
        r'^management-profile/bulk/$',
        management_profile_bulk,
        name='seeddb-management-profile-bulk',
    ),
    # Service
    url(r'^service/$', service.service, name='seeddb-service'),
    url(
        r'^service/edit/(?P<service_id>[\d]+)$',
        service_edit.service_edit,
        name='seeddb-service-edit',
    ),
    url(
        r'^service/delete/(?P<object_id>[\d]+)$',
        service.service_delete,
        name='seeddb-service-delete',
    ),
    url(r'^service/add/$', service_edit.service_edit, name='seeddb-service-edit'),
    url(r'^service/bulk/$', service.service_bulk, name='seeddb-service-bulk'),
    # Room
    url(r'^room/$', room.room, name='seeddb-room'),
    url(r'^room/edit/(?P<room_id>.+)/$', room.room_edit, name='seeddb-room-edit'),
    url(
        r'^room/delete/(?P<object_id>.+)/$', room.room_delete, name='seeddb-room-delete'
    ),
    url(
        r'^room/(?P<action>copy)/(?P<room_id>.+)/$',
        room.room_edit,
        name='seeddb-room-copy',
    ),
    url(r'^room/add/$', room.room_edit, name='seeddb-room-edit'),
    url(
        r'^room/add/(?P<lat>.+)/(?P<lon>.+)/$', room.room_edit, name='seeddb-room-edit'
    ),
    url(r'^room/bulk/$', room.room_bulk, name='seeddb-room-bulk'),
    # Location
    url(r'^location/$', location.location, name='seeddb-location'),
    url(
        r'^location/edit/(?P<location_id>.+)/$',
        location.location_edit,
        name='seeddb-location-edit',
    ),
    url(
        r'^location/delete/(?P<object_id>.+)/$',
        location.location_delete,
        name='seeddb-location-delete',
    ),
    url(r'^location/add/$', location.location_edit, name='seeddb-location-edit'),
    url(
        r'^location/(?P<action>copy)/(?P<location_id>.+)/$',
        location.location_edit,
        name='seeddb-location-copy',
    ),
    url(r'^location/bulk/$', location.location_bulk, name='seeddb-location-bulk'),
    # Organization
    url(r'^organization/$', organization.organization, name='seeddb-organization'),
    url(
        r'^organization/edit/(?P<organization_id>.+)/$',
        organization.organization_edit,
        name='seeddb-organization-edit',
    ),
    url(
        r'^organization/delete/(?P<object_id>.+)/$',
        organization.organization_delete,
        name='seeddb-organization-delete',
    ),
    url(
        r'^organization/add/$',
        organization.organization_edit,
        name='seeddb-organization-edit',
    ),
    url(
        r'^organization/bulk/$',
        organization.organization_bulk,
        name='seeddb-organization-bulk',
    ),
    # Usage category
    url(r'^usage/$', usage.usage, name='seeddb-usage'),
    url(r'^usage/edit/(?P<usage_id>.+)/$', usage.usage_edit, name='seeddb-usage-edit'),
    url(
        r'^usage/delete/(?P<object_id>.+)/$',
        usage.usage_delete,
        name='seeddb-usage-delete',
    ),
    url(r'^usage/add/$', usage.usage_edit, name='seeddb-usage-edit'),
    url(r'^usage/bulk/$', usage.usage_bulk, name='seeddb-usage-bulk'),
    # Type
    url(r'^type/$', netboxtype.netboxtype, name='seeddb-type'),
    url(
        r'^type/edit/(?P<type_id>[\d]+)/$',
        netboxtype.netboxtype_edit,
        name='seeddb-type-edit',
    ),
    url(
        r'^type/delete/(?P<object_id>[\d]+)/$',
        netboxtype.netboxtype_delete,
        name='seeddb-type-delete',
    ),
    url(r'^type/add/$', netboxtype.netboxtype_edit, name='seeddb-type-edit'),
    url(r'^type/bulk/$', netboxtype.netboxtype_bulk, name='seeddb-type-bulk'),
    # Vendor
    url(r'^vendor/$', vendor.vendor, name='seeddb-vendor'),
    url(r'^vendor/add/$', vendor.vendor_edit, name='seeddb-vendor-edit'),
    url(r'^vendor/bulk/$', vendor.vendor_bulk, name='seeddb-vendor-bulk'),
    # Netbox Group
    url(r'^netboxgroup/$', netboxgroup.netboxgroup, name='seeddb-netboxgroup'),
    url(
        r'^netboxgroup/edit/(?P<netboxgroup_id>.+)/$',
        netboxgroup.netboxgroup_edit,
        name='seeddb-netboxgroup-edit',
    ),
    url(
        r'^netboxgroup/delete/(?P<object_id>.+)/$',
        netboxgroup.netboxgroup_delete,
        name='seeddb-netboxgroup-delete',
    ),
    url(
        r'^netboxgroup/add/$',
        netboxgroup.netboxgroup_edit,
        name='seeddb-netboxgroup-edit',
    ),
    url(
        r'^netboxgroup/bulk/$',
        netboxgroup.netboxgroup_bulk,
        name='seeddb-netboxgroup-bulk',
    ),
    # Vlan
    url(r'^vlan/$', vlan.vlan_list, name='seeddb-vlan'),
    url(r'^vlan/edit/(?P<vlan_id>[\d]+)/$', vlan.vlan_edit, name='seeddb-vlan-edit'),
    # Prefix
    url(r'^prefix/$', prefix.get_prefix_view, name='seeddb-prefix'),
    url(
        r'^prefix/edit/(?P<prefix_id>[\d]+)/$',
        prefix.prefix_edit,
        name='seeddb-prefix-edit',
    ),
    url(
        r'^prefix/delete/(?P<object_id>[\d]+)/$',
        prefix.prefix_delete,
        name='seeddb-prefix-delete',
    ),
    url(r'^prefix/add/$', prefix.prefix_edit, name='seeddb-prefix-edit'),
    url(r'^prefix/bulk/$', prefix.prefix_bulk, name='seeddb-prefix-bulk'),
    # Cabling
    url(r'^cabling/$', cabling.cabling, name='seeddb-cabling'),
    url(r'^cabling/edit/$', cabling.cabling_edit, name='seeddb-cabling-edit'),
    url(
        r'^cabling/delete/(?P<object_id>[\d]+)/$',
        cabling.cabling_delete,
        name='seeddb-cabling-delete',
    ),
    url(r'^cabling/add/$', cabling.cabling_edit, name='seeddb-cabling-add'),
    url(r'^cabling/bulk/$', cabling.cabling_bulk, name='seeddb-cabling-bulk'),
    # Patch
    url(r'^patch/$', patch.patch, name='seeddb-patch'),
    url(r'^patch/edit/$', patch.patch_edit, name='seeddb-patch-edit'),
    url(r'^patch/delete/$', patch.patch_delete, name='seeddb-patch-delete'),
    url(r'^patch/bulk/$', patch.patch_bulk, name='seeddb-patch-bulk'),
    url(r'^patch/save/', patch.patch_save, name='seeddb-patch-save'),
    url(r'^patch/remove/', patch.patch_remove, name='seeddb-patch-remove'),
    url(r'^patch/loadcell/', patch.load_cell, name='seeddb-patch-load-cell'),
]

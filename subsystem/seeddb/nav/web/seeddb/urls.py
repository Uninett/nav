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
    url(r'^netbox/(?P<netbox_sysname>[\w\d.-]+)/', dummy,
        name='seeddb-netbox-edit'),

    # Service
    url(r'service/$', service_list,
        name='seeddb-service'),
    url(r'service/(?P<service>[\d]+)', dummy,
        name='seeddb-service-edit'),

    # Room
    url(r'room/$', room_list,
        name='seeddb-room'),
    url(r'room/(?P<room>[\w\d.-]+)/', dummy,
        name='seeddb-room-edit'),

    # Location
    url(r'^location/$', location_list,
        name='seeddb-location'),
    url(r'^location/(?P<location>[\w\d]+)/', dummy,
        name='seeddb-location-edit'),

    # Organization
    url(r'organization/$', organization_list,
        name='seeddb-organization'),
    url(r'organization/(?P<organization>[\w\d]+)/', dummy,
        name='seeddb-organization-edit'),

    # Usage category
    url(r'usage/$', usage_list,
        name='seeddb-usage'),
    url(r'usage/(?P<usage>[\w\d]+)/', dummy,
        name='seeddb-usage-edit'),

    # Type
    url(r'type/$', type_list,
        name='seeddb-type'),
    url(r'type/(?P<type>[\d]+)/', dummy, 
        name='seeddb-type-edit'),

    # Vendor
    url(r'vendor/$', vendor_list,
        name='seeddb-vendor'),
    url(r'vendor/(?P<vendor>[\w\d]+)/', dummy,
        name='seeddb-vendor-edit'),

    # SNMPoid

    # Subcategory
    url(r'subcategory/$', subcategory_list,
        name='seeddb-subcategory'),
    url(r'subcategory/(?P<subcategory>[\w\d-]+)/', dummy,
        name='seeddb-subcategory-edit'),

    # Vlan
    url(r'vlan/$', vlan_list,
        name='seeddb-vlan'),
    url(r'vlan/(?P<vlan>[\d]+)/', dummy,
        name='seeddb-vlan-edit'),

    # Prefix
    url(r'prefix/$', prefix_list,
        name='seeddb-prefix'),
    url(r'prefix/(?P<prefix>[\d]+)/', dummy,
        name='seeddb-prefix-edit'),

    # Cabling
    url(r'cabling/$', cabling_list,
        name='seeddb-cabling'),
    url(r'cabling/(?P<cabling>[\d]+)/', dummy,
        name='seeddb-cabling-edit'),

    # Patch
    url(r'patch/$', patch_list,
        name='seeddb-patch'),
    url(r'patch/(?P<patch>[\d]+)/', dummy,
        name='seeddb-patch-edit'),
)

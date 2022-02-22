# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008, 2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Alert Profiles url config."""

# pylint: disable=W0614,W0401

from django.urls import re_path
from nav.web.alertprofiles import views


urlpatterns = [
    # Overview
    re_path(r'^$', views.overview, name='alertprofiles-overview'),
    # User settings
    re_path(r'^profile/$', views.show_profile, name='alertprofiles-profile'),
    re_path(r'^profile/new/$', views.profile_new, name='alertprofiles-profile-new'),
    re_path(
        r'^profile/(?P<profile_id>\d+)/$',
        views.profile_detail,
        name='alertprofiles-profile-detail',
    ),
    re_path(r'^profile/save/$', views.profile_save, name='alertprofiles-profile-save'),
    re_path(
        r'^profile/remove/$', views.profile_remove, name='alertprofiles-profile-remove'
    ),
    re_path(
        r'^profile/time-period/(?P<time_period_id>\d+)/$',
        views.profile_time_period,
        name='alertprofiles-profile-timeperiod',
    ),
    re_path(
        r'^profile/time-period/(?P<time_period_id>\d+)/subscriptions/$',
        views.profile_time_period_setup,
        name='alertprofiles-profile-timeperiod-setup',
    ),
    re_path(
        r'^profile/time-period/add/$',
        views.profile_time_period_add,
        name='alertprofiles-profile-timeperiod-add',
    ),
    re_path(
        r'^profile/time-period/remove/$',
        views.profile_time_period_remove,
        name='alertprofiles-profile-timeperiod-remove',
    ),
    re_path(
        r'^profile/time-period/subscription/(?P<subscription_id>\d+)$',
        views.profile_time_period_subscription_edit,
        name='alertprofiles-profile-timeperiod-subscription',
    ),
    re_path(
        r'^profile/time-period/subscription/add/$',
        views.profile_time_period_subscription_add,
        name='alertprofiles-profile-timeperiod-subscription-add',
    ),
    re_path(
        r'^profile/time-period/subscription/remove/$',
        views.profile_time_period_subscription_remove,
        name='alertprofiles-profile-timeperiod-subscription-remove',
    ),
    re_path(
        r'^language/save/$', views.language_save, name='alertprofiles-language-save'
    ),
    re_path(r'^sms/$', views.sms_list, name='alertprofiles-sms'),
    # Alert address
    re_path(r'^address/$', views.address_list, name='alertprofiles-address'),
    re_path(
        r'^address/(?P<address_id>\d+)/$',
        views.address_detail,
        name='alertprofiles-address-detail',
    ),
    re_path(r'^address/new/$', views.address_detail, name='alertprofiles-address-new'),
    re_path(r'^address/save/$', views.address_save, name='alertprofiles-address-save'),
    re_path(
        r'^address/remove/$', views.address_remove, name='alertprofiles-address-remove'
    ),
    # Filters
    re_path(r'^filters/$', views.filter_list, name='alertprofiles-filters'),
    re_path(
        r'^filters/(?P<filter_id>\d+)/$',
        views.filter_detail,
        name='alertprofiles-filters-detail',
    ),
    re_path(r'^filters/new/$', views.filter_detail, name='alertprofiles-filters-new'),
    re_path(r'^filters/save/$', views.filter_save, name='alertprofiles-filters-save'),
    re_path(
        r'^filters/remove/$', views.filter_remove, name='alertprofiles-filters-remove'
    ),
    re_path(
        r'^filters/add-expression/$',
        views.filter_addexpression,
        name='alertprofiles-filters-addexpression',
    ),
    re_path(
        r'^filters/save-expression/$',
        views.filter_saveexpression,
        name='alertprofiles-filters-saveexpression',
    ),
    re_path(
        r'^filters/remove-expression/$',
        views.filter_removeexpression,
        name='alertprofiles-filters-removeexpression',
    ),
    # Filter groups
    re_path(
        r'^filter-groups/$', views.filter_group_list, name='alertprofiles-filter_groups'
    ),
    re_path(
        r'^filter-groups/(?P<filter_group_id>\d+)/$',
        views.filter_group_detail,
        name='alertprofiles-filter_groups-detail',
    ),
    re_path(
        r'^filter-groups/new/$',
        views.filter_group_detail,
        name='alertprofiles-filter_groups-new',
    ),
    re_path(
        r'^filter-groups/save/$',
        views.filter_group_save,
        name='alertprofiles-filter_groups-save',
    ),
    re_path(
        r'^filter-groups/remove/$',
        views.filter_group_remove,
        name='alertprofiles-filter_groups-remove',
    ),
    re_path(
        r'^filter-groups/add-filter/$',
        views.filter_group_addfilter,
        name='alertprofiles-filter_groups-addfilter',
    ),
    re_path(
        r'^filter-groups/remove-filter/$',
        views.filter_group_remove_or_move_filter,
        name='alertprofiles-filter_groups-removefilter',
    ),
    # Filter variables (aka. matchfields)
    re_path(r'^matchfields/$', views.matchfield_list, name='alertprofiles-matchfields'),
    re_path(
        r'^matchfields/(?P<matchfield_id>\d+)/$',
        views.matchfield_detail,
        name='alertprofiles-matchfields-detail',
    ),
    re_path(
        r'^matchfields/new/$',
        views.matchfield_detail,
        name='alertprofiles-matchfields-new',
    ),
    re_path(
        r'^matchfields/save/$',
        views.matchfield_save,
        name='alertprofiles-matchfields-save',
    ),
    re_path(
        r'^matchfields/remove/$',
        views.matchfield_remove,
        name='alertprofiles-matchfields-remove',
    ),
    # Admin settings:
    #################
    # Permissions
    re_path(r'^permissions/$', views.permission_list, name='alertprofiles-permissions'),
    re_path(
        r'^permissions/(?P<group_id>\d+)/$',
        views.permission_list,
        name='alertprofiles-permissions-detail',
    ),
    re_path(
        r'^permissions/save/$',
        views.permissions_save,
        name='alertprofiles-permissions-save',
    ),
]

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

from django.urls import path

from nav.web.alertprofiles import views


urlpatterns = [
    # Overview
    path('', views.overview, name='alertprofiles-overview'),
    # alert profiles groups and permissions modal
    path(
        'groupsandpermissions/',
        views.groups_and_permissions_modal,
        name='alertprofiles-groups-and-permissions',
    ),
    # User settings
    path('profile/', views.show_profile, name='alertprofiles-profile'),
    path('profile/new/', views.profile_new, name='alertprofiles-profile-new'),
    path(
        'profile/<int:profile_id>/',
        views.profile_detail,
        name='alertprofiles-profile-detail',
    ),
    path('profile/save/', views.profile_save, name='alertprofiles-profile-save'),
    path('profile/remove/', views.profile_remove, name='alertprofiles-profile-remove'),
    path(
        'profile/time-period/<int:time_period_id>/',
        views.profile_time_period,
        name='alertprofiles-profile-timeperiod',
    ),
    path(
        'profile/time-period/<int:time_period_id>/subscriptions/',
        views.profile_time_period_setup,
        name='alertprofiles-profile-timeperiod-setup',
    ),
    path(
        'profile/time-period/add/',
        views.profile_time_period_add,
        name='alertprofiles-profile-timeperiod-add',
    ),
    path(
        'profile/time-period/remove/',
        views.profile_time_period_remove,
        name='alertprofiles-profile-timeperiod-remove',
    ),
    path(
        'profile/time-period/subscription/<int:subscription_id>',
        views.profile_time_period_subscription_edit,
        name='alertprofiles-profile-timeperiod-subscription',
    ),
    path(
        'profile/time-period/subscription/add/',
        views.profile_time_period_subscription_add,
        name='alertprofiles-profile-timeperiod-subscription-add',
    ),
    path(
        'profile/time-period/subscription/remove/',
        views.profile_time_period_subscription_remove,
        name='alertprofiles-profile-timeperiod-subscription-remove',
    ),
    path('language/save/', views.language_save, name='alertprofiles-language-save'),
    path('sms/', views.sms_list, name='alertprofiles-sms'),
    # Alert address
    path('address/', views.address_list, name='alertprofiles-address'),
    path(
        'address/<int:address_id>/',
        views.address_detail,
        name='alertprofiles-address-detail',
    ),
    path('address/new/', views.address_detail, name='alertprofiles-address-new'),
    path('address/save/', views.address_save, name='alertprofiles-address-save'),
    path('address/remove/', views.address_remove, name='alertprofiles-address-remove'),
    # Filters
    path('filters/', views.filter_list, name='alertprofiles-filters'),
    path(
        'filters/<int:filter_id>/',
        views.filter_detail,
        name='alertprofiles-filters-detail',
    ),
    path('filters/new/', views.filter_detail, name='alertprofiles-filters-new'),
    path('filters/save/', views.filter_save, name='alertprofiles-filters-save'),
    path('filters/remove/', views.filter_remove, name='alertprofiles-filters-remove'),
    path(
        'filters/add-expression/',
        views.filter_addexpression,
        name='alertprofiles-filters-addexpression',
    ),
    path(
        'filters/add-expression/operatorhelp',
        views.filter_addexpression_operator_help_modal,
        name='alertprofiles-filters-addexpression-operator-help',
    ),
    path(
        'filters/save-expression/',
        views.filter_saveexpression,
        name='alertprofiles-filters-saveexpression',
    ),
    path(
        'filters/remove-expression/',
        views.filter_removeexpression,
        name='alertprofiles-filters-removeexpression',
    ),
    # Filter groups
    path('filter-groups/', views.filter_group_list, name='alertprofiles-filter_groups'),
    path(
        'filter-groups/<int:filter_group_id>/',
        views.filter_group_detail,
        name='alertprofiles-filter_groups-detail',
    ),
    path(
        'filter-groups/operatorhelp/',
        views.filter_group_operator_help_modal,
        name='alertprofiles-filter_groups-operator-help',
    ),
    path(
        'filter-groups/new/',
        views.filter_group_detail,
        name='alertprofiles-filter_groups-new',
    ),
    path(
        'filter-groups/save/',
        views.filter_group_save,
        name='alertprofiles-filter_groups-save',
    ),
    path(
        'filter-groups/remove/',
        views.filter_group_remove,
        name='alertprofiles-filter_groups-remove',
    ),
    path(
        'filter-groups/add-filter/',
        views.filter_group_addfilter,
        name='alertprofiles-filter_groups-addfilter',
    ),
    path(
        'filter-groups/remove-filter/',
        views.filter_group_remove_or_move_filter,
        name='alertprofiles-filter_groups-removefilter',
    ),
    # Filter variables (aka. matchfields)
    path('matchfields/', views.matchfield_list, name='alertprofiles-matchfields'),
    path(
        'matchfields/<int:matchfield_id>/',
        views.matchfield_detail,
        name='alertprofiles-matchfields-detail',
    ),
    path(
        'matchfields/new/',
        views.matchfield_detail,
        name='alertprofiles-matchfields-new',
    ),
    path(
        'matchfields/save/',
        views.matchfield_save,
        name='alertprofiles-matchfields-save',
    ),
    path(
        'matchfields/remove/',
        views.matchfield_remove,
        name='alertprofiles-matchfields-remove',
    ),
    # Admin settings:
    #################
    # Permissions
    path('permissions/', views.permission_list, name='alertprofiles-permissions'),
    path(
        'permissions/help',
        views.permissions_help_modal,
        name='alertprofiles-permissions-help',
    ),
    path(
        'permissions/<int:group_id>/',
        views.permission_list,
        name='alertprofiles-permissions-detail',
    ),
    path(
        'permissions/save/',
        views.permissions_save,
        name='alertprofiles-permissions-save',
    ),
]

# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008, 2011 Uninett AS
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

from django.conf.urls import url
from nav.web.alertprofiles import views


urlpatterns = [
    # Overview
    url(r'^$', views.overview, name='alertprofiles-overview'),
    # User settings
    url(r'^profile/$', views.show_profile, name='alertprofiles-profile'),
    url(r'^profile/new/$', views.profile_new, name='alertprofiles-profile-new'),
    url(
        r'^profile/(?P<profile_id>\d+)/$',
        views.profile_detail,
        name='alertprofiles-profile-detail',
    ),
    url(r'^profile/save/$', views.profile_save, name='alertprofiles-profile-save'),
    url(
        r'^profile/remove/$', views.profile_remove, name='alertprofiles-profile-remove'
    ),
    url(
        r'^profile/time-period/(?P<time_period_id>\d+)/$',
        views.profile_time_period,
        name='alertprofiles-profile-timeperiod',
    ),
    url(
        r'^profile/time-period/(?P<time_period_id>\d+)/subscriptions/$',
        views.profile_time_period_setup,
        name='alertprofiles-profile-timeperiod-setup',
    ),
    url(
        r'^profile/time-period/add/$',
        views.profile_time_period_add,
        name='alertprofiles-profile-timeperiod-add',
    ),
    url(
        r'^profile/time-period/remove/$',
        views.profile_time_period_remove,
        name='alertprofiles-profile-timeperiod-remove',
    ),
    url(
        r'^profile/time-period/subscription/(?P<subscription_id>\d+)$',
        views.profile_time_period_subscription_edit,
        name='alertprofiles-profile-timeperiod-subscription',
    ),
    url(
        r'^profile/time-period/subscription/add/$',
        views.profile_time_period_subscription_add,
        name='alertprofiles-profile-timeperiod-subscription-add',
    ),
    url(
        r'^profile/time-period/subscription/remove/$',
        views.profile_time_period_subscription_remove,
        name='alertprofiles-profile-timeperiod-subscription-remove',
    ),
    url(r'^language/save/$', views.language_save, name='alertprofiles-language-save'),
    url(r'^sms/$', views.sms_list, name='alertprofiles-sms'),
    # Alert address
    url(r'^address/$', views.address_list, name='alertprofiles-address'),
    url(
        r'^address/(?P<address_id>\d+)/$',
        views.address_detail,
        name='alertprofiles-address-detail',
    ),
    url(r'^address/new/$', views.address_detail, name='alertprofiles-address-new'),
    url(r'^address/save/$', views.address_save, name='alertprofiles-address-save'),
    url(
        r'^address/remove/$', views.address_remove, name='alertprofiles-address-remove'
    ),
    # Filters
    url(r'^filters/$', views.filter_list, name='alertprofiles-filters'),
    url(
        r'^filters/(?P<filter_id>\d+)/$',
        views.filter_detail,
        name='alertprofiles-filters-detail',
    ),
    url(r'^filters/new/$', views.filter_detail, name='alertprofiles-filters-new'),
    url(r'^filters/save/$', views.filter_save, name='alertprofiles-filters-save'),
    url(r'^filters/remove/$', views.filter_remove, name='alertprofiles-filters-remove'),
    url(
        r'^filters/add-expression/$',
        views.filter_addexpression,
        name='alertprofiles-filters-addexpression',
    ),
    url(
        r'^filters/save-expression/$',
        views.filter_saveexpression,
        name='alertprofiles-filters-saveexpression',
    ),
    url(
        r'^filters/remove-expression/$',
        views.filter_removeexpression,
        name='alertprofiles-filters-removeexpression',
    ),
    # Filter groups
    url(
        r'^filter-groups/$', views.filter_group_list, name='alertprofiles-filter_groups'
    ),
    url(
        r'^filter-groups/(?P<filter_group_id>\d+)/$',
        views.filter_group_detail,
        name='alertprofiles-filter_groups-detail',
    ),
    url(
        r'^filter-groups/new/$',
        views.filter_group_detail,
        name='alertprofiles-filter_groups-new',
    ),
    url(
        r'^filter-groups/save/$',
        views.filter_group_save,
        name='alertprofiles-filter_groups-save',
    ),
    url(
        r'^filter-groups/remove/$',
        views.filter_group_remove,
        name='alertprofiles-filter_groups-remove',
    ),
    url(
        r'^filter-groups/add-filter/$',
        views.filter_group_addfilter,
        name='alertprofiles-filter_groups-addfilter',
    ),
    url(
        r'^filter-groups/remove-filter/$',
        views.filter_group_remove_or_move_filter,
        name='alertprofiles-filter_groups-removefilter',
    ),
    # Filter variables (aka. matchfields)
    url(r'^matchfields/$', views.matchfield_list, name='alertprofiles-matchfields'),
    url(
        r'^matchfields/(?P<matchfield_id>\d+)/$',
        views.matchfield_detail,
        name='alertprofiles-matchfields-detail',
    ),
    url(
        r'^matchfields/new/$',
        views.matchfield_detail,
        name='alertprofiles-matchfields-new',
    ),
    url(
        r'^matchfields/save/$',
        views.matchfield_save,
        name='alertprofiles-matchfields-save',
    ),
    url(
        r'^matchfields/remove/$',
        views.matchfield_remove,
        name='alertprofiles-matchfields-remove',
    ),
    # Admin settings:
    #################
    # Permissions
    url(r'^permissions/$', views.permission_list, name='alertprofiles-permissions'),
    url(
        r'^permissions/(?P<group_id>\d+)/$',
        views.permission_list,
        name='alertprofiles-permissions-detail',
    ),
    url(
        r'^permissions/save/$',
        views.permissions_save,
        name='alertprofiles-permissions-save',
    ),
]

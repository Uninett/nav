# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

__copyright__ = "Copyright 2007-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

from django.conf.urls.defaults import *

from nav.web.alertprofiles.views import *

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    # Overview
    url(r'^$', overview,
        name='alertprofiles-overview'),

    # User settings
    url(r'^profile/$', profile,
        name='alertprofiles-profile'),
    url(r'^profile/new/$', profile_new,
        name='alertprofiles-profile-new'),
    url(r'^profile/(?P<profile_id>\d+)/$', profile_detail,
        name='alertprofiles-profile-detail'),
    url(r'^profile/save/$', profile_save,
        name='alertprofiles-profile-save'),
    url(r'^profile/remove/$', profile_remove,
        name='alertprofiles-profile-remove'),

    url(r'^profile/time-period/(?P<time_period_id>\d+)/$', profile_time_period,
        name='alertprofiles-profile-timeperiod'),
    url(r'^profile/time-period/(?P<time_period_id>\d+)/subscriptions/$', profile_time_period_setup,
        name='alertprofiles-profile-timeperiod-setup'),
    url(r'^profile/time-period/add/$', profile_time_period_add,
        name='alertprofiles-profile-timeperiod-add'),
    url(r'^profile/time-period/remove/$', profile_time_period_remove,
        name='alertprofiles-profile-timeperiod-remove'),

    url(r'^profile/time-period/subscription/(?P<subscription_id>\d+)$', profile_time_period_subscription_edit,
        name='alertprofiles-profile-timeperiod-subscription'),
    url(r'^profile/time-period/subscription/add/$', profile_time_period_subscription_add,
        name='alertprofiles-profile-timeperiod-subscription-add'),
    url(r'^profile/time-period/subscription/remove/$', profile_time_period_subscription_remove,
        name='alertprofiles-profile-timeperiod-subscription-remove'),

    url(r'^language/save/$', language_save,
        name='alertprofiles-language-save'),

    url(r'^sms/$', sms_list,
        name='alertprofiles-sms'),

    # Alert address
    url(r'^address/$', address_list,
        name='alertprofiles-address'),
    url(r'^address/(?P<address_id>\d+)/$', address_detail,
        name='alertprofiles-address-detail'),
    url(r'^address/new/$', address_detail,
        name='alertprofiles-address-new'),
    url(r'^address/save/$', address_save,
        name='alertprofiles-address-save'),
    url(r'^address/remove/$', address_remove,
        name='alertprofiles-address-remove'),

    # Filters
    url(r'^filters/$', filter_list,
        name='alertprofiles-filters'),
    url(r'^filters/(?P<filter_id>\d+)/$', filter_detail,
        name='alertprofiles-filters-detail'),
    url(r'^filters/new/$', filter_detail,
        name='alertprofiles-filters-new'),
    url(r'^filters/save/$', filter_save,
        name='alertprofiles-filters-save'),
    url(r'^filters/remove/$', filter_remove,
        name='alertprofiles-filters-remove'),
    url(r'^filters/add-expression/$', filter_addexpression,
        name='alertprofiles-filters-addexpression'),
    url(r'^filters/save-expression/$', filter_saveexpression,
        name='alertprofiles-filters-saveexpression'),
    url(r'^filters/remove-expression/$', filter_removeexpression,
        name='alertprofiles-filters-removeexpression'),

    # Filter groups
    url(r'^filter-groups/$', filtergroup_list,
        name='alertprofiles-filtergroups'),
    url(r'^filter-groups/(?P<filter_group_id>\d+)/$', filtergroup_detail,
        name='alertprofiles-filtergroups-detail'),
    url(r'^filter-groups/new/$', filtergroup_detail,
        name='alertprofiles-filtergroups-new'),
    url(r'^filter-groups/save/$', filtergroup_save,
        name='alertprofiles-filtergroups-save'),
    url(r'^filter-groups/remove/$', filtergroup_remove,
        name='alertprofiles-filtergroups-remove'),
    url(r'^filter-groups/add-filter/$', filtergroup_addfilter,
        name='alertprofiles-filtergroups-addfilter'),
    url(r'^filter-groups/remove-filter/$', filtergroup_remove_or_move_filter,
        name='alertprofiles-filtergroups-removefilter'),

    # Filter variables (aka. matchfields)
    url(r'^matchfields/$', matchfield_list,
        name='alertprofiles-matchfields'),
    url(r'^matchfields/(?P<matchfield_id>\d+)/$', matchfield_detail,
        name='alertprofiles-matchfields-detail'),
    url(r'^matchfields/new/$', matchfield_detail,
        name='alertprofiles-matchfields-new'),
    url(r'^matchfields/save/$', matchfield_save,
        name='alertprofiles-matchfields-save'),
    url(r'^matchfields/remove/$', matchfield_remove,
        name='alertprofiles-matchfields-remove'),

    # Admin settings:
    #################

    # Permissions
    url(r'^permissions/$', permission_list,
        name='alertprofiles-permissions'),
    url(r'^permissions/(?P<group_id>\d+)/$', permission_list,
        name='alertprofiles-permissions-detail'),
    url(r'^permissions/save/$', permissions_save,
        name='alertprofiles-permissions-save'),
)

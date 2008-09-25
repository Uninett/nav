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
#    url(r'^profile/settings/$', profile_settings),
#    url(r'^profile/(?P<profile_id>\d+)/$', profile_detail),
    url(r'^profile/(?P<profile_id>\d+)/setup/$', 'profile_setup',
        name='alertprofiles-profile-setup'),

    # Filters
    url(r'^filters/$', filter_list, name='alertprofiles-filters'),
    url(r'^filters/(?P<filter_id>\d+)/$', filter_detail,
        name='alertprofiles-filters-detail'),
    url(r'^filters/addexpresion/$', filter_addexpresion,
        name='alertprofiles-filters-addexpresion'),
    url(r'^filters/saveexpresion/$', filter_saveexpresion,
        name='alertprofiles-filters-saveexpresion'),

    # Filter groups
    url(r'^filter-groups/$', filtergroup_list,
        name='alertprofiles-filtergroups'),
    url(r'^filter-groups/(?P<filter_id>\d+)/$', 'filtergroup_detail',
        name='alertprofiles-filtergroups-detail'),

    # Filter variables (aka. matchfields)
    url(r'^matchfields/$', matchfield_list,
        name='alertprofiles-matchfields'),
    url(r'^matchfields/(?P<matchfield_id>\d+)/$', 'matchfield_detail',
        name='alertprofiles-matchfields-detail'),

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

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

from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.db.models import Q

from nav.models.profiles import *
from nav.django.shortcuts import render_to_response, object_list
from nav.django.utils import get_account, permission_required
from nav.web.templates.AlertProfilesTemplate import AlertProfilesTemplate

def overview(request):
    account = get_account(request)
    active = {'overview': True}
    return render_to_response(
            AlertProfilesTemplate,
            'alertprofiles/overview.html',
            {'active': active}
        )

def filter_list(request):
    account = get_account(request)

    # Get all public filters, and private filters belonging to this user only
    filters = Filter.objects.filter(
            Q(owner__exact=account.pk) | Q(owner__exact=None)
        ).order_by('owner', 'name')

    active = {'filters': True}

    return object_list(
            AlertProfilesTemplate,
            request,
            queryset=filters,
            template_name='alertprofiles/filter_list.html',
            extra_context={'active': active},
        )

def filtergroup_list(request):
    account = get_account(request)

    # Get all public filtergroups, and private filtergroups belonging to this
    # user only
    filtergroups = FilterGroup.objects.filter(
            Q(owner__exact=account.pk) | Q(owner__isnull=True)
        ).order_by('owner', 'name')

    active = {'filtergroups': True}

    return object_list(
            AlertProfilesTemplate,
            request,
            queryset=filtergroups,
            template_name='alertprofiles/filtergroup_list.html',
            extra_context={'active': active},
        )

@permission_required
def matchfield_list(request):
    account = get_account(request)

    # Get all matchfields aka. filter variables
    matchfields = MatchField.objects.all().order_by('name')

    active = {'matchfields': True}

    return object_list(
            AlertProfilesTemplate,
            request,
            queryset=matchfields,
            template_name='alertprofiles/matchfield_list.html',
            extra_context={'active': active},
        )

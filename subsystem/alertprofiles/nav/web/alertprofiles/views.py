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
from django.shortcuts import get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.db.models import Q

from nav.models.profiles import *
from nav.django.shortcuts import render_to_response, object_list
from nav.django.utils import get_account, permission_required
from nav.web.templates.AlertProfilesTemplate import AlertProfilesTemplate

from nav.web.alertprofiles.forms import *

def overview(request):
    account = get_account(request)
    active = {'overview': True}
    return render_to_response(
            AlertProfilesTemplate,
            'alertprofiles/overview.html',
            {'active': active}
        )

def profile(request):
    account = get_account(request)
    active = {'profile': True}

    # Get information about user
    groups = account.accountgroup_set.all()
    active_profile = account.alertpreference.active_profile
    adress = AlertAddress.objects.filter(account=account.pk)
    profiles = AlertProfile.objects.filter(account=account.pk).order_by('name')

    # Get information about users privileges
    sms_privilege = account.has_perm('alert_by', 'sms')

    filter_dict = {'group_permisions__in': [g.id for g in groups]}
    filter_groups = FilterGroup.objects.filter(**filter_dict).order_by('name')

    info_dict = {
            'active': active,
            'groups': groups,
            'adress': adress,
            'profiles': profiles,
            'active_profile': active_profile,
            'sms_privilege': sms_privilege,
            'filter_groups': filter_groups,
        }

    return render_to_response(
            AlertProfilesTemplate,
            'alertprofiles/profile.html',
            info_dict,
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

def filter_detail(request, filter_id=None):
    active = {'filters': True}

    filter_form = None
    matchfields = MatchField.objects.all()

    if filter_id:
        filter = get_object_or_404(Filter, pk=filter_id)
        filter_form = FilterForm(instance=filter)

        # Get all matchfields (many-to-many connection by table Expresion)
        expresions = Expresion.objects.filter(filter=filter_id)
    else:
        filter_form = FilterForm()

    return render_to_response(
            AlertProfilesTemplate,
            'alertprofiles/filter_form.html',
            {
                    'active': active,
                    'filter_id': filter_id,
                    'filter_form': filter_form,
                    'matchfields': matchfields,
                    'expresions': expresions,
                },
        )

def filter_addexpresion(request):
    if request.method == 'POST':
        filter = get_object_or_404(Filter, pk=request.POST.get('filter'))
        matchfield = get_object_or_404(MatchField, pk=request.POST.get('matchfield'))
        initial = {'filter': filter.id, 'match_field': matchfield.id}
        form = ExpresionForm(match_field=matchfield, initial=initial)

        active = {'filters': True}
        info_dict = {
                'form': form,
                'active': active,
                'filter': filter,
                'matchfield': matchfield,
            }
        return render_to_response(
                AlertProfilesTemplate,
                'alertprofiles/expresion_form.html',
                info_dict,
            )
    else:
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

def filter_saveexpresion(request):
    if request.method == 'POST':
        data = ExpresionForm(request.POST)
        if data.is_valid():
            expresion = data.save(commit=False)
            raise Exception(expresion.get_operator_mapping())
        else:
            raise Exception(data.errors)
    else:
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

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

@permission_required
def permission_list(request, group_id=None):
    groups = AccountGroup.objects.all().order_by('name')

    selected_group = None
    filtergroups = None
    permisions = None
    if group_id:
        selected_group = groups.get(pk=group_id)
        filtergroups = FilterGroup.objects.filter(owner__isnull=True).order_by('name')
        permisions = AccountGroup.objects.get(pk=group_id).filtergroup_set.all()

    active = {'permissions': True}
    info_dict = {
            'groups': groups,
            'selected_group': selected_group,
            'filtergroups': filtergroups,
            'permisions': permisions,
            'active': active,
        }

    return render_to_response(
            AlertProfilesTemplate,
            'alertprofiles/permissions.html',
            info_dict,
        )

@permission_required
def permissions_save(request):
    if request.method == 'POST':
        group = get_object_or_404(AccountGroup, pk=request.POST.get('group'))
        filtergroups = FilterGroup.objects.filter(pk__in=request.POST.getlist('filtergroup'))

        group.filtergroup_set = filtergroups

        return HttpResponseRedirect(reverse('alertprofiles-permissions-detail', args=(group.id,)))
    else:
        return HttpResponseRedirect(reverse('alertprofiles-permissions'))

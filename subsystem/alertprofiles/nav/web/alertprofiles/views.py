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

# TODO Check that functions that should require permission do require
# permission

# TODO Filter/filtergroups have owners, check that the account that performs
# the operation is the owner

__copyright__ = "Copyright 2007-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.db.models import Q

from nav.models.profiles import *
from nav.django.shortcuts import render_to_response, object_list
from nav.django.utils import get_account, permission_required
from nav.web.templates.AlertProfilesTemplate import AlertProfilesTemplate

from nav.web.alertprofiles.forms import *
from nav.web.alertprofiles.utils import *

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
    admin = is_admin(account)

    # Get all public filters, and private filters belonging to this user only
    filters = Filter.objects.filter(
            Q(owner__exact=account.pk) | Q(owner__exact=None)
        ).order_by('owner', 'name')

    active = {'filters': True}
    info_dict = {
            'active': active,
            'admin': admin,
            'form_action': reverse('alertprofiles-filters-remove'),
        }

    return object_list(
            AlertProfilesTemplate,
            request,
            queryset=filters,
            template_name='alertprofiles/filter_list.html',
            extra_context=info_dict,
        )

def filter_detail(request, filter_id=None):
    active = {'filters': True}
    account = get_account(request)
    admin = is_admin(account)

    filter_form = None
    expresions = None
    matchfields = None

    if filter_id:
        filter = get_object_or_404(Filter, pk=filter_id)
        filter_form = FilterForm(instance=filter, admin=admin)

        matchfields = MatchField.objects.all()
        # Get all matchfields (many-to-many connection by table Expresion)
        expresions = Expresion.objects.filter(filter=filter_id)
    else:
        filter_form = FilterForm(initial={'owner': account}, admin=admin)

    return render_to_response(
            AlertProfilesTemplate,
            'alertprofiles/filter_form.html',
            {
                    'active': active,
                    'admin': admin,
                    'detail_id': filter_id,
                    'form': filter_form,
                    'matchfields': matchfields,
                    'expresions': expresions,
                },
        )

def filter_save(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    (account, admin, owner) = resolve_account_admin_and_owner(request)
    filter = None

    # Build a form. Different values depending on if we are updating or
    # making a new filter
    if request.POST.get('id'):
        filter = get_object_or_404(Filter, pk=request.POST.get('id'))
        if not account_owns_filters(account, filter):
            return HttpResponseRedirect('No access')

        form = FilterForm(request.POST, instance=filter, admin=admin)
    else:
        form = FilterForm(request.POST, admin=admin)

    # If there are some invalid values, return to form and show the errors
    if not form.is_valid():
        info_dict = {
                'form': form,
                'active': {'filters': True},
            }
        return render_to_response(
                AlertProfilesTemplate,
                'alertprofiles/filter_form.html',
                info_dict,
            )

    # Set the fields in Filter to the submited values
    if request.POST.get('id'):
        filter.name = request.POST.get('name')
        filter.owner = owner
    else:
        filter = Filter(name=request.POST.get('name'), owner=owner)

    # Save the filter
    filter.save()

    return HttpResponseRedirect(reverse('alertprofiles-filters-detail', args=(filter.id,)))

def filter_remove(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    if request.POST.get('confirm'):
        filters = Filter.objects.filter(pk__in=request.POST.getlist('element'))

        if not account_owns_filters(get_account(request), filters):
            return HttpResponseForbidden('No access')

        filters.delete()

        return HttpResponseRedirect(reverse('alertprofiles-filters'))
    else:
        filters = Filter.objects.filter(pk__in=request.POST.getlist('filter'))

        if not account_owns_filters(get_account(request), filters):
            return HttpResponseForbidden('No access')

        info_dict = {
                'form_action': reverse('alertprofiles-filters-remove'),
                'active': {'filters': True},
                'elements': filters,
                'perform_on': None,
            }
        return render_to_response(
                AlertProfilesTemplate,
                'alertprofiles/confirmation_list.html',
                info_dict,
            )

def filter_addexpresion(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    filter = get_object_or_404(Filter, pk=request.POST.get('id'))
    matchfield = get_object_or_404(MatchField, pk=request.POST.get('matchfield'))
    initial = {'filter': filter.id, 'match_field': matchfield.id}
    form = ExpresionForm(match_field=matchfield, initial=initial)

    if not account_owns_filters(get_account(request), filter):
        return HttpResponseForbidden('No access')

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

def filter_saveexpresion(request):
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    # Get the MatchField, Filter and Operator objects associated with the
    # input POST-data
    filter = Filter.objects.get(pk=request.POST.get('id'))
    type = request.POST.get('operator')
    match_field = MatchField.objects.get(pk=request.POST.get('match_field'))
    operator = Operator.objects.get(type=type, match_field=match_field.pk)

    if not account_owns_filters(get_account(request), filter):
        return HttpResponseForbidden('No access')

    # Get the value
    value = ""
    if operator.type == Operator.IN:
        # If input was a multiple choice list we have to join each option
        # in one string, where each option is separated by a | (pipe).
        # If input was a IP adress we should replace space with | (pipe).
        # FIXME We might want some data checks here
        if match_field.data_type == MatchField.IP:
            # FIXME We might want to check that it is a valid IP adress.
            # If we do so, we need to remember both IPv4 and IPv6
            value = request.POST.get('value').replace(' ', '|')
        else:
            value = "|".join([value for value in request.POST.getlist('value')])
    else:
        value = request.POST.get('value')

    expresion = Expresion(
            filter=filter,
            match_field=match_field,
            operator=operator.type,
            value=value,
        )
    expresion.save()
    return HttpResponseRedirect(reverse('alertprofiles-filters-detail', args=(filter.id,)))

def filter_removeexpresion(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    if request.POST.get('confirm'):
        expresions = request.POST.getlist('element')
        filter = get_object_or_404(Filter, pk=request.POST.get('perform_on'))

        if not account_owns_filters(get_account(request), filter):
            return HttpResponseForbidden('No access')

        Expresion.objects.filter(pk__in=expresions).delete()

        return HttpResponseRedirect(reverse('alertprofiles-filters-detail', args=(filter.id,)))
    else:
        expresions = Expresion.objects.filter(pk__in=request.POST.getlist('expression'))
        filter = get_object_or_404(Filter, pk=request.POST.get('id'))

        if not account_owns_filters(get_account(request), filter):
            return HttpResponseForbidden('No access')

        info_dict = {
                'form_action': reverse('alertprofiles-filters-removeexpresion'),
                'active': {'filters': True},
                'elements': expresions,
                'perform_on': filter.id,
            }
        return render_to_response(
                AlertProfilesTemplate,
                'alertprofiles/confirmation_list.html',
                info_dict,
            )

def filtergroup_list(request):
    account = get_account(request)
    admin = is_admin(account)

    # Get all public filtergroups, and private filtergroups belonging to this
    # user only
    filtergroups = FilterGroup.objects.filter(
            Q(owner__exact=account.pk) | Q(owner__isnull=True)
        ).order_by('owner', 'name')

    active = {'filtergroups': True}
    info_dict = {
            'active': active,
            'admin': admin,
            'form_action': reverse('alertprofiles-filtergroups-remove'),
        }
    return object_list(
            AlertProfilesTemplate,
            request,
            queryset=filtergroups,
            template_name='alertprofiles/filtergroup_list.html',
            extra_context=info_dict
        )

def filtergroup_detail(request, filter_group_id=None):
    active = {'filtergroups': True}
    account = get_account(request)
    admin = is_admin(account)

    form = None
    filtergroupcontent = None
    filters = None

    if filter_group_id:
        filtergroup = get_object_or_404(FilterGroup, pk=filter_group_id)
        form = FilterGroupForm(instance=filtergroup, admin=admin)

        filtergroupcontent = FilterGroupContent.objects.filter(filter_group=filtergroup.id).order_by('priority')
        filters = Filter.objects.filter(
                Q(owner__exact=account.pk) | Q(owner__isnull=True)
            ).order_by('owner', 'name')
    else:
        form = FilterGroupForm(initial={'owner': account}, admin=admin)

    info_dict = {
            'active': active,
            'admin': admin,
            'detail_id': filter_group_id,
            'filter_group_content': filtergroupcontent,
            'filters': filters,
            'form': form,
        }
    return render_to_response(
            AlertProfilesTemplate,
            'alertprofiles/filtergroup_form.html',
            info_dict,
        )

def filtergroup_save(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filtergroups'))

    (account, admin, owner) = resolve_account_admin_and_owner(request)
    filter_group = None

    if request.POST.get('id'):
        filter_group = get_object_or_404(FilterGroup, pk=request.POST.get('id'))
        if not account_owns_filters(account, filter_group):
            return HttpResponseForbidden('No access')
        form = FilterGroupForm(request.POST, instance=filter_group, admin=admin)
    else:
        form = FilterGroupForm(request.POST, admin=admin)

    if not form.is_valid():
        info_dict = {
                'form': form,
                'active': {'filtergroups': True},
            }
        return render_to_response(
                AlertProfilesTemplate,
                'alertprofiles/filtergroup_form.html',
                info_dict,
            )

    if request.POST.get('id'):
        filter_group.name = request.POST.get('name')
        filter_group.description = request.POST.get('description')
        filter_group.owner = owner
    else:
        filter_group = FilterGroup(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                owner=owner
            )

    filter_group.save()
    return HttpResponseRedirect(reverse('alertprofiles-filtergroups-detail', args=(filter_group.id,)))

def filtergroup_remove(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filters'))

    if request.POST.get('confirm'):
        filter_groups = FilterGroup.objects.filter(pk__in=request.POST.getlist('element'))

        if not account_owns_filters(get_account(request), filter_groups):
            return HttpResponseForbidden('No access')

        filter_groups.delete()

        return HttpResponseRedirect(reverse('alertprofiles-filtergroups'))
    else:
        filter_groups = FilterGroup.objects.filter(pk__in=request.POST.getlist('filter_group'))

        if not account_owns_filters(get_account(request), filter_groups):
            return HttpResponseForbidden('No access')

        info_dict = {
                'form_action': reverse('alertprofiles-filtergroups-remove'),
                'active': {'filtergroups': True},
                'elements': filter_groups,
                'perform_on': None,
            }
        return render_to_response(
                AlertProfilesTemplate,
                'alertprofiles/confirmation_list.html',
                info_dict,
            )

def filtergroup_addfilter(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filtergroups'))

    account = get_account(request)
    filter_group = get_object_or_404(FilterGroup, pk=request.POST.get('id'))
    filter = get_object_or_404(Filter, pk=request.POST.get('filter'))
    operator = request.POST.get('operator')

    if not account_owns_filters(account, filter_group):
        return HttpResponseForbidden('No access')

    if not operator or len(operator) != 2:
        return HttpResponseRedirect(
                reverse('alertprofiles-filtergroups-detail', attrs=(filter.id,))
            )

    # Operator is sent by POST data as a "bitfield" (it's really a string
    # pretending to be a bitfield) where position 0 represents 'include' and
    # position 1 represents 'positive'.
    include = False
    positive = False
    if operator[0] == '1':
        include = True
    if operator[1] == '1':
        positive = True

    # 'priority' is the order filters are considered when there's an alert.
    # We want to add new filters to filtergroupcontent with priority
    # incremented by one. Also double check that previously added filters
    # are ordered correctly, ie priority increments by one for each filter.
    last_priority = order_filter_group_content(filter_group)

    options = {
            'include': include,
            'positive': positive,
            'priority': last_priority + 1,
            'filter': filter,
            'filter_group': filter_group,
        }
    new_filter = FilterGroupContent(**options)
    new_filter.save()

    return HttpResponseRedirect(
            reverse('alertprofiles-filtergroups-detail', args=(filter_group.id,))
        )

def filtergroup_removefilter(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filtergroups'))

    # Check if we are deleting or moving filters
    if request.POST.get('moveup') or request.POST.get('movedown'):
        return filtergroup_movefilter(request)

    # We are deleting files. Show confirmation page or remove?
    if request.POST.get('confirm'):
        filter_group = FilterGroup.objects.get(pk=request.POST.get('perform_on'))
        filters = FilterGroupContent.objects.filter(pk__in=request.POST.getlist('element'))

        if not account_owns_filters(get_account(request), filter_group):
            return HttpResponseForbidden('No access')

        filters.delete()

        # Rearrange filters
        last_priority = order_filter_group_content(filter_group)

        return HttpResponseRedirect(
                reverse('alertprofiles-filtergroups-detail', args=(filter_group.id,))
            )
    else:
        filter_group = get_object_or_404(FilterGroup, pk=request.POST.get('id'))
        filter_group_content = FilterGroupContent.objects.filter(
                pk__in=request.POST.getlist('filter'),
                filter_group=filter_group.id
            )

        if not account_owns_filters(get_account(request), filter_group):
            return HttpResponseForbidden('No access')

        info_dict = {
                'form_action': reverse('alertprofiles-filtergroups-removefilter'),
                'active': {'filters': True},
                'elements': filter_group_content,
                'perform_on': filter_group.id,
            }
        return render_to_response(
                AlertProfilesTemplate,
                'alertprofiles/confirmation_list.html',
                info_dict,
            )

def filtergroup_movefilter(request):
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-filtergroups'))

    filter_group_id = request.POST.get('id')
    filter_group = get_object_or_404(FilterGroup, pk=filter_group_id)
    movement = 0
    filter = None

    if request.POST.get('moveup'):
        movement = -1
        filter = get_object_or_404(FilterGroupContent, pk=request.POST.get('moveup'))
    elif request.POST.get('movedown'):
        movement = 1
        filter = get_object_or_404(FilterGroupContent, pk=request.POST.get('movedown'))
    else:
        # No sensible input, just return to where we came from
        return HttpResponseRedirect(
                reverse('alertprofiels-filtergroups-detail', args=(filter_group_id,))
            )

    # Make sure content is ordered correct
    last_priority = order_filter_group_content(filter_group)

    # Check if the filter we're going to swap places with exists
    try:
        other_filter = FilterGroupContent.objects.filter(
                    filter_group=filter_group.id,
                    priority=filter.priority + movement
                )[0:1].get()
    except FilterGroupContent.DoesNotExist:
        return HttpResponseRedirect(
                reverse('alertprofiles-filtergroups-detail', args=(filter_group.id,))
            )

    new_priority = other_filter.priority
    other_filter.priority = filter.priority
    filter.priority = new_priority

    other_filter.save()
    filter.save()

    return HttpResponseRedirect(
            reverse('alertprofiles-filtergroups-detail', args=(filter_group_id,))
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
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('alertprofiles-permissions'))

    group = get_object_or_404(AccountGroup, pk=request.POST.get('group'))
    filtergroups = FilterGroup.objects.filter(pk__in=request.POST.getlist('filtergroup'))

    group.filtergroup_set = filtergroups

    return HttpResponseRedirect(reverse('alertprofiles-permissions-detail', args=(group.id,)))

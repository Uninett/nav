# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
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
# Authors: Thomas Adamcik <thomas.adamcik@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"
__id__ = "$Id$"

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.template import RequestContext

from nav.models.profiles import Account, AccountGroup
from nav.django.shortcuts import render_to_response, object_list, object_detail

from nav.web.templates.UserAdmin import UserAdmin
from nav.web.useradmin.forms import *

def account_list(request):
    return object_list(UserAdmin, request, Account.objects.all(),
                        template_object_name='account',
                        template_name='useradmin/account_list.html',
                        extra_context={'active': {'account_list': 1}})

def account_detail(request, account_id=None):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        account = None

    account_form = AccountForm(instance=account)
    org_form = OrganizationAddForm()
    group_form = GroupAddForm()

    if request.method == 'POST':
        if 'submit_account' in request.POST:
            account_form = AccountForm(request.POST, instance=account)

            if account_form.is_valid():
                account = account_form.save(commit=False)

                if account_form.cleaned_data['password1'].strip():
                    account.set_password(account_form.cleaned_data['password1'])

                account.save()

                return HttpResponseRedirect(reverse('useradmin-account_detail', args=[account.id]))

        elif 'submit_org' in request.POST:
            org_form = OrganizationAddForm(request.POST)

            if org_form.is_valid():
                account.accountorganization_set.get_or_create(organization=org_form.cleaned_data['organization'].id)

                return HttpResponseRedirect(reverse('useradmin-account_detail', args=[account.id]))

        elif 'submit_group' in request.POST:
            group_form = GroupAddForm(request.POST)

            if group_form.is_valid():
                account.accountgroup_set.add(group_form.cleaned_data['group'])
                account.save()

                return HttpResponseRedirect(reverse('useradmin-account_detail', args=[account.id]))

    if account:
        active = {'account_detail': True}
    else:
        active = {'account_new': True}

    return render_to_response(UserAdmin, 'useradmin/account_detail.html',
                        {
                            'active': active,
                            'account': account,
                            'account_form': account_form,
                            'org_form': org_form,
                            'group_form': group_form,
                        }, RequestContext(request))

def account_delete(request, account_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        # FIXME add message
        return HttpResponseRedirect(reverse('useradmin-account_list'))

    if account.is_system_account():
        # FIXME add message
        return HttpResponseRedirect(reverse('useradmin-account_list'))

    if request.method == 'POST':
        account.delete()
        # FIXME add message
        return HttpResponseRedirect(reverse('useradmin-account_list'))

    return render_to_response(UserAdmin, 'useradmin/delete.html',
                        {
                            'name': '%s (%s)' % (account.name, account.login),
                            'type': 'account',
                        }, RequestContext(request))

def account_organization_remove(request, account_id, org_id):
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        # FIXME add message
        return HttpResponseRedirect(reverse('useradmin-account_list'))

    try:
        organization = account.accountorganization_set.get(id=org_id)
    except AccountOrganization.DoesNotExist:
        # FIXME add message
        return HttpResponseRedirect(reverse('useradmin-account_detail', args=[account.id]))

    if request.method == 'POST':
        organization.delete()
        # FIXME add message
        return HttpResponseRedirect(reverse('useradmin-account_detail', args=[account.id]))

    return render_to_response(UserAdmin, 'useradmin/delete.html',
                        {
                            'name': '%s from %s' % (organization, account),
                            'type': 'organization',
                        }, RequestContext(request))



def group_list(request):
    return object_list(UserAdmin, request, AccountGroup.objects.all(),
                        template_object_name='group',
                        template_name='useradmin/group_list.html',
                        extra_context={'active': {'group_list': 1}})

def group_detail(request, group_id=None):
    try:
        group = AccountGroup.objects.get(id=group_id)
    except AccountGroup.DoesNotExist:
        group = None

    group_form = AccountGroupForm(instance=group)
    account_form = AccountAddForm()
    privilege_form = PrivilegeForm()

    if group:
        active = {'group_detail': True}
    else:
        active = {'group_new': True}

    return render_to_response(UserAdmin, 'useradmin/group_detail.html',
                        {
                            'active': active,
                            'group': group,
                            'group_form': group_form,
                            'account_form': account_form,
                            'privilege_form': privilege_form,
                        }, RequestContext(request))

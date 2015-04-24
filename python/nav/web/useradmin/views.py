#
# Copyright (C) 2008, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Controller functions for the useradmin interface"""

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.debug import sensitive_post_parameters

from nav.models.profiles import Account, AccountGroup, Privilege
from nav.models.manage import Organization

from nav.django.auth import sudo
from nav.web.useradmin import forms


class UserAdminContext(RequestContext):
    """Context container for the useradmin requests"""
    def __init__(self, *args, **kwargs):
        # account_processor is in the settings file.
        if 'processors' not in kwargs:
            kwargs['processors'] = [custom_processor]
        super(UserAdminContext, self).__init__(*args, **kwargs)


def custom_processor(_request):
    """Return some always available variables"""
    return {'navpath': [('Home', '/'), ('User Administration', )]}


def account_list(request):
    """Controller for displaying the account list"""
    accounts = Account.objects.all()
    return render_to_response('useradmin/account_list.html',
                              {'active': {'account_list': 1},
                               'accounts': accounts},
                              UserAdminContext(request))


@sensitive_post_parameters('password1', 'password2')
def account_detail(request, account_id=None):
    """Displays details and processes POST-requests for an account"""
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        account = None

    if request.method == 'POST':
        if 'submit_account' in request.POST:
            account_form = forms.AccountForm(request.POST, instance=account)
            if account_form.is_valid():
                return save_account(request, account_form)

        elif 'submit_org' in request.POST:
            org_form = forms.OrganizationAddForm(account, request.POST)
            if org_form.is_valid():
                return save_account_org(request, account, org_form)

        elif 'submit_group' in request.POST:
            group_form = forms.GroupAddForm(account, request.POST)
            if group_form.is_valid():
                return save_account_group(request, account, group_form)

        elif 'submit_sudo' in request.POST:
            return sudo_to_user(request)
    else:
        account_form = forms.AccountForm(instance=account)
        org_form = forms.OrganizationAddForm(account)
        group_form = forms.GroupAddForm(account)

    active = {'account_detail': True} if account else {'account_new': True}

    return render_to_response('useradmin/account_detail.html',
                  {
                      'active': active,
                      'account': account,
                      'account_form': account_form,
                      'org_form': org_form,
                      'group_form': group_form,
                  }, UserAdminContext(request))


def save_account(request, account_form):
    """Save an account based on post data"""
    account = account_form.save(commit=False)

    should_set_password = (
        'password1' in account_form.cleaned_data
        and account_form.cleaned_data['password1']
        and not account.ext_sync)

    if should_set_password:
        account.set_password(account_form.cleaned_data['password1'])

    account.save()

    messages.success(request, '"%s" has been saved.' % (account))
    return HttpResponseRedirect(reverse('useradmin-account_detail',
                                        args=[account.id]))


def save_account_org(request, account, org_form):
    """Add an organization to an account"""
    organization = org_form.cleaned_data['organization']

    try:
        account.organizations.get(id=organization.id)
        messages.warning(request,
            'Organization was not added as it has already been added.')
    except Organization.DoesNotExist:
        account.organizations.add(organization)
        messages.success(request, 'Added organization "%s" to account "%s"' %
                         (organization, account))

    return HttpResponseRedirect(reverse('useradmin-account_detail',
                                        args=[account.id]))


def save_account_group(request, account, group_form):
    """Add a group to an account"""
    group = group_form.cleaned_data['group']

    special_case = (
        (group.is_admin_group() or group.is_protected_group())
        and account.is_default_account())

    if special_case:
        messages.error(
            request, 'Default user may not be added to "%s" group.' % group)
    else:
        try:
            account.accountgroup_set.get(id=group.id)
            messages.warning(request,
                'Group was not added as it has already been added.')
        except AccountGroup.DoesNotExist:
            account.accountgroup_set.add(group)
            messages.success(
                request, 'Added "%s" to group "%s"' % (account, group))

    return HttpResponseRedirect(reverse('useradmin-account_detail',
                                        args=[account.id]))


def sudo_to_user(request):
    """Sudo to a user based on POST data"""
    sudo_account_id = request.POST.get('account')
    try:
        sudo_account = Account.objects.get(pk=sudo_account_id)
    except Account.DoesNotExist:
        messages.error(request, 'Account not found.')
    else:
        sudo(request, sudo_account)
    return HttpResponseRedirect(reverse('webfront-index'))


def account_delete(request, account_id):
    """Controller for displaying the delete account page"""
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        messages.error(request, 'Account %s does not exist.' % (account_id))
        return HttpResponseRedirect(reverse('useradmin-account_list'))

    if account.is_system_account():
        messages.error(request,
                       'Account %s can not be deleted as it is a system '
                       'account.' % (account.name))
        return HttpResponseRedirect(reverse('useradmin-account_detail',
                                            args=[account.id]))

    if request.method == 'POST':
        account.delete()
        messages.success(request,
                         'Account %s has been deleted.' % (account.name))
        return HttpResponseRedirect(reverse('useradmin-account_list'))

    return render_to_response('useradmin/delete.html',
                        {
                            'name': '%s (%s)' % (account.name, account.login),
                            'type': 'account',
                            'back': reverse('useradmin-account_detail',
                                            args=[account.id]),
                        }, UserAdminContext(request))


def account_organization_remove(request, account_id, org_id):
    """Controller for removing an organization from an account"""
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        messages.error(request, 'Account %s does not exist.' % (account_id))
        return HttpResponseRedirect(reverse('useradmin-account_list'))

    try:
        organization = account.organizations.get(id=org_id)
    except Organization.DoesNotExist:
        messages.error(request,
                    'Organization %s does not exist or it is not associated '
                    'with %s.' % (org_id, account))
        return HttpResponseRedirect(reverse('useradmin-account_detail',
                                            args=[account.id]))

    if request.method == 'POST':
        account.organizations.remove(organization)
        messages.success(request,
                    'Organization %s has been removed from account %s.' %
                    (organization, account))
        return HttpResponseRedirect(reverse('useradmin-account_detail',
                                            args=[account.id]))

    return render_to_response('useradmin/delete.html',
                        {
                            'name': '%s from %s' % (organization, account),
                            'type': 'organization',
                            'back': reverse('useradmin-account_detail',
                                            args=[account.id]),
                        }, UserAdminContext(request))

def account_group_remove(request, account_id, group_id, caller='account'):
    """Controller for removing a group from an account

    :param caller: indicate if account or group is caller. Used to define
                   redirect url
    """
    if caller == 'account':
        list_redirect = HttpResponseRedirect(reverse('useradmin-account_list'))
        detail_redirect = HttpResponseRedirect(
            reverse('useradmin-account_detail', args=[account_id]))
    else:
        list_redirect = HttpResponseRedirect(reverse('useradmin-group_list'))
        detail_redirect = HttpResponseRedirect(
            reverse('useradmin-group_detail', args=[group_id]))

    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        messages.error(request, 'Account %s does not exist.' % (account_id))
        return list_redirect

    try:
        group = account.accountgroup_set.get(id=group_id)
    except AccountGroup.DoesNotExist:
        messages.warning(request,
            'Group %s does not exist or it is not '
            'associated with %s.' % (group_id, account))
        return detail_redirect

    if group.is_protected_group():
        messages.error(request,
            '%s can not be removed from %s as it is a '
            'protected group.' % (account, group))
        return detail_redirect

    if group.is_admin_group() and account.is_admin_account():
        messages.error(
            request, '%s can not be removed from %s.' % (account, group))
        return detail_redirect

    if request.method == 'POST':
        account.accountgroup_set.remove(group)
        messages.success(
            request, '%s has been removed from %s.' % (account, group))
        return detail_redirect

    return render_to_response('useradmin/delete.html',
        {
            'name': '%s from the group %s' % (account, group),
            'type': 'account',
            'back': reverse('useradmin-account_detail', args=[account.id]),
        }, UserAdminContext(request))


def group_list(request):
    """Controller for listing all user groups in NAV"""
    groups = AccountGroup.objects.all()
    return render_to_response('useradmin/group_list.html',
                              {'active': {'group_list': True},
                               'groups': groups},
                              UserAdminContext(request))


def group_detail(request, group_id=None):
    """Controller for showing details for a user group"""
    try:
        group = AccountGroup.objects.get(id=group_id)
    except AccountGroup.DoesNotExist:
        group = None

    group_form = forms.AccountGroupForm(instance=group)
    account_form = forms.AccountAddForm(group)
    privilege_form = forms.PrivilegeForm()

    if request.method == 'POST':

        if 'submit_group' in request.POST:
            group_form = forms.AccountGroupForm(request.POST, instance=group)

            if group_form.is_valid():
                group = group_form.save()

                messages.success(request, '"%s" has been saved.' % (group))
                return HttpResponseRedirect(reverse('useradmin-group_detail',
                                                    args=[group.id]))

        elif 'submit_privilege' in request.POST:
            privilege_form = forms.PrivilegeForm(request.POST)

            if privilege_form.is_valid():
                message_type = privilege_form.cleaned_data['type']
                target = privilege_form.cleaned_data['target']

                try:
                    group.privilege_set.get(type=message_type, target=target)
                    messages.warning(request,
                        'Privilege was not added as it already exists.')
                except Privilege.DoesNotExist:
                    group.privilege_set.create(type=message_type, target=target)
                    messages.success(request, 'Privilege has been added.')

                return HttpResponseRedirect(reverse('useradmin-group_detail',
                                                    args=[group.id]))
        elif 'submit_account' in request.POST:
            account_form = forms.AccountAddForm(group, request.POST)

            if account_form.is_valid():
                try:
                    account = account_form.cleaned_data['account']
                    group.accounts.get(login=account.login)
                    messages.warning(request,
                        'Account %s was not added as it is already '
                        'a member of the group.' % account)
                except Account.DoesNotExist:
                    group.accounts.add(account)
                    messages.success(request,
                                     'Account %s has been added.' % account)

                return HttpResponseRedirect(reverse('useradmin-group_detail',
                                                    args=[group.id]))

    active = {'group_detail': True} if group else {'group_new': True}

    return render_to_response('useradmin/group_detail.html',
        {
            'active': active,
            'group': group,
            'group_form': group_form,
            'account_form': account_form,
            'privilege_form': privilege_form,
        }, UserAdminContext(request))


def group_delete(request, group_id):
    """Controller for deleting a user group"""
    try:
        group = AccountGroup.objects.get(id=group_id)
    except AccountGroup.DoesNotExist:
        messages.error(request, 'Group %s does not exist.' % (group_id))
        return HttpResponseRedirect(reverse('useradmin-group_list'))

    if group.is_system_group():
        messages.error(request,
                       'Group %s is a system group and can not be '
                       'deleted.' % (group))
        return HttpResponseRedirect(reverse('useradmin-group_detail',
                                            args=[group.id]))

    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group %s has been deleted.' % (group))
        return HttpResponseRedirect(reverse('useradmin-group_list'))

    return render_to_response('useradmin/delete.html',
        {
            'name': group,
            'type': 'group',
            'back': reverse('useradmin-group_detail', args=[group.id]),
        }, UserAdminContext(request))


def group_account_remove(request, group_id, account_id):
    """Controller for removing an account from a group"""
    return account_group_remove(request, account_id, group_id, caller='group')


def group_privilege_remove(request, group_id, privilege_id):
    """Controller for revoking a privilege from a group"""
    try:
        group = AccountGroup.objects.get(id=group_id)
    except AccountGroup.DoesNotExist:
        messages.error(request, 'Group %s does not exist.' % (group_id))
        return HttpResponseRedirect(reverse('useradmin-group_list'))

    try:
        privilege = group.privilege_set.get(id=privilege_id)
    except Privilege.DoesNotExist:
        messages.warning(request,
                         'Privilege %s does not exist or it is not associated '
                         'with %s.' % (privilege_id, group))
        return HttpResponseRedirect(reverse('useradmin-account_detail',
                                            args=[request.account.id]))

    if request.method == 'POST':
        privilege.delete()
        messages.success(request,
                         'Privilege %s has been removed from group %s.' %
                         (privilege, group))
        return HttpResponseRedirect(reverse('useradmin-group_detail',
                                            args=[group.id]))

    return render_to_response('useradmin/delete.html',
        {
            'name': '%s from %s' % (privilege, group),
            'type': 'privilege',
            'back': reverse('useradmin-group_detail', args=[group.id]),
        }, UserAdminContext(request))

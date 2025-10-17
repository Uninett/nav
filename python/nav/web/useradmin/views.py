#
# Copyright (C) 2008, 2011, 2020 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Controller functions for the useradmin interface"""

import copy
from datetime import datetime, timezone

from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_post_parameters

from nav.auditlog.models import LogEntry
from nav.models.profiles import Account, AccountGroup, Privilege
from nav.models.manage import Organization
from nav.models.api import APIToken, JWTRefreshToken

from nav.web.auth.sudo import sudo
from nav.web.auth.utils import get_account
from nav.web.useradmin import forms
from nav.web.jwtgen import generate_refresh_token, hash_token, decode_token
from nav.config import ConfigurationError
from nav.django.settings import LOCAL_JWT_IS_CONFIGURED


DEFAULT_NAVPATH = {'navpath': [('Home', '/'), ('User Administration',)]}


def account_list(request):
    """Controller for displaying the account list"""
    accounts = Account.objects.all()
    context = {
        'active': {'account_list': 1},
        'accounts': accounts,
        'auditlog_api_parameters': {'object_model': 'account'},
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/account_list.html', context)


@sensitive_post_parameters('password1', 'password2')
def account_detail(request, account_id=None):
    """Displays details and processes POST-requests for an account"""
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        account = None

    old_account = copy.deepcopy(account)
    external_authentication = getattr(account, "ext_sync", False)
    if external_authentication:
        account_form_class = forms.ExternalAccountForm
    else:
        account_form_class = forms.AccountForm
    account_form = account_form_class(instance=account)
    org_form = forms.OrganizationAddForm(account)
    group_form = forms.GroupAddForm(account)

    if request.method == 'POST':
        if 'submit_account' in request.POST:
            account_form = account_form_class(request.POST, instance=account)
            if account_form.is_valid():
                return save_account(request, account_form, old_account)

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

    if account:
        active = {"account_detail": True}
        auditlog_api_parameters = {"object_model": "account", "object_pk": account.pk}
        add_warnings_for_account(account, request)
    else:
        active = {"account_new": True}
        auditlog_api_parameters = {}

    context = {
        'auditlog_api_parameters': auditlog_api_parameters,
        'active': active,
        'account': account,
        'account_form': account_form,
        'org_form': org_form,
        'group_form': group_form,
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/account_detail.html', context)


def add_warnings_for_account(account, request):
    """Adds session warning messages about issues with an Account's configuration

    :type account: Account
    :type request: HttpRequest
    """
    if account.id == Account.DEFAULT_ACCOUNT:
        if account.locked:
            messages.warning(
                request,
                "This account represents all non-logged in users. Be wary of making "
                "changes to it.",
            )
        else:
            messages.warning(
                request,
                "This account represents all non-logged in users, but has been UNLOCKED"
                " so it can be used to log in. Please LOCK this account immediately",
            )
    else:
        if account.locked:
            messages.warning(request, "This account is locked and cannot log in.")

    if not account.locked and account.has_plaintext_password():
        messages.warning(
            request,
            "This account's password is stored in plain text. Its password should be "
            "changed immediately, or the account disabled.",
        )
    if account.has_old_style_password_hash():
        messages.warning(
            request,
            "This account's password is stored using an outdated and INSECURE hashing "
            "method. The user has either not logged in or not changed its password in "
            "years. Its password should be changed or the account disabled.",
        )
    if account.has_deprecated_password_hash_method():
        messages.warning(
            request,
            "This account's password is stored using an older hash method. The user "
            "has either not logged in or not changed its password in a long time. Its "
            "password should be changed or the account disabled.",
        )


def save_account(request, account_form, old_account):
    """Save an account based on post data"""
    account = account_form.save(commit=False)

    should_set_password = (
        'password1' in account_form.cleaned_data
        and account_form.cleaned_data['password1']
        and not account.ext_sync
    )

    if should_set_password:
        account.set_password(account_form.cleaned_data['password1'])

    account.save()
    logged_in_account = get_account(request)
    log_account_change(logged_in_account, old_account, account)

    messages.success(request, '"%s" has been saved.' % (account))
    return HttpResponseRedirect(reverse('useradmin-account_detail', args=[account.id]))


def save_account_org(request, account, org_form):
    """Add an organization to an account"""
    organization = org_form.cleaned_data['organization']

    try:
        account.organizations.get(id=organization.id)
        messages.warning(
            request, 'Organization was not added as it has already been added.'
        )
    except Organization.DoesNotExist:
        account.organizations.add(organization)
        log_add_account_to_org(request, organization, account)
        messages.success(
            request, 'Added organization "%s" to account "%s"' % (organization, account)
        )

    return HttpResponseRedirect(reverse('useradmin-account_detail', args=[account.id]))


def save_account_group(request, account, group_form):
    """Add a group to an account"""
    group = group_form.cleaned_data['group']

    special_case = (
        group.is_admin_group() or group.is_protected_group()
    ) and account.is_anonymous

    if special_case:
        messages.error(request, 'Default user may not be added to "%s" group.' % group)
    else:
        try:
            account.groups.get(id=group.id)
            messages.warning(
                request, 'Group was not added as it has already been added.'
            )
        except AccountGroup.DoesNotExist:
            account.groups.add(group)
            messages.success(request, 'Added "%s" to group "%s"' % (account, group))
            log_add_account_to_group(request, group, account)

    return HttpResponseRedirect(reverse('useradmin-account_detail', args=[account.id]))


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
        messages.error(
            request,
            'Account %s can not be deleted as it is a system account.' % (account.name),
        )
        return HttpResponseRedirect(
            reverse('useradmin-account_detail', args=[account.id])
        )

    if request.method == 'POST':
        from nav.web.auth.utils import PASSWORD_ISSUES_CACHE_KEY

        account.delete()
        logged_in_account = get_account(request)
        LogEntry.add_delete_entry(logged_in_account, account)
        messages.success(request, 'Account %s has been deleted.' % (account.name))
        # Delete cache entry of how many accounts have password issues
        cache.delete(PASSWORD_ISSUES_CACHE_KEY)
        return HttpResponseRedirect(reverse('useradmin-account_list'))

    context = {
        'name': '%s (%s)' % (account.name, account.login),
        'type': 'account',
        'action': 'delete account',
        'back': reverse('useradmin-account_detail', args=[account.id]),
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/delete.html', context)


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
        messages.error(
            request,
            'Organization %s does not exist or it is not associated '
            'with %s.' % (org_id, account),
        )
        return HttpResponseRedirect(
            reverse('useradmin-account_detail', args=[account.id])
        )

    if request.method == 'POST':
        account.organizations.remove(organization)
        messages.success(
            request,
            'Organization %s has been removed from account %s.'
            % (organization, account),
        )

        logged_in_account = get_account(request)
        LogEntry.add_log_entry(
            logged_in_account,
            'edit-account-remove-org',
            '{actor} removed user {object} from organization {target}',
            target=organization,
            object=account,
        )

        return HttpResponseRedirect(
            reverse('useradmin-account_detail', args=[account.id])
        )

    context = {
        'name': 'in %s from %s' % (organization, account),
        'type': 'organization',
        'action': 'remove organization membership',
        'back': reverse('useradmin-account_detail', args=[account.id]),
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/delete.html', context)


def account_group_remove(request, account_id, group_id, caller='account'):
    """Controller for removing a group from an account

    :param caller: indicate if account or group is caller. Used to define
                   redirect url
    """
    if caller == 'account':
        back_url = reverse('useradmin-account_detail', args=[account_id])
        list_redirect = HttpResponseRedirect(reverse('useradmin-account_list'))
        detail_redirect = HttpResponseRedirect(back_url)
    else:
        back_url = reverse('useradmin-group_detail', args=[group_id])
        list_redirect = HttpResponseRedirect(reverse('useradmin-group_list'))
        detail_redirect = HttpResponseRedirect(back_url)

    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        messages.error(request, 'Account %s does not exist.' % (account_id))
        return list_redirect

    try:
        group = account.groups.get(id=group_id)
    except AccountGroup.DoesNotExist:
        messages.warning(
            request,
            'Group %s does not exist or it is not '
            'associated with %s.' % (group_id, account),
        )
        return detail_redirect

    if group.is_protected_group():
        messages.error(
            request,
            '%s can not be removed from %s as it is a '
            'protected group.' % (account, group),
        )
        return detail_redirect

    if group.is_admin_group() and account.is_admin_account():
        messages.error(request, '%s can not be removed from %s.' % (account, group))
        return detail_redirect

    if request.method == 'POST':
        account.groups.remove(group)
        messages.success(request, '%s has been removed from %s.' % (account, group))

        logged_in_account = get_account(request)
        LogEntry.add_log_entry(
            logged_in_account,
            'edit-account-remove-group',
            '{actor} removed user {object} from group {target}',
            target=group,
            object=account,
        )

        return detail_redirect

    context = {
        'name': '%s from the group %s' % (account, group),
        'type': 'account',
        'action': 'remove group member',
        'back': back_url,
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/delete.html', context)


def group_list(request):
    """Controller for listing all user groups in NAV"""
    groups = AccountGroup.objects.all()
    context = {
        'active': {'group_list': True},
        'groups': groups,
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/group_list.html', context)


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
                return HttpResponseRedirect(
                    reverse('useradmin-group_detail', args=[group.id])
                )

        elif 'submit_privilege' in request.POST:
            privilege_form = forms.PrivilegeForm(request.POST)

            if privilege_form.is_valid():
                message_type = privilege_form.cleaned_data['type']
                target = privilege_form.cleaned_data['target']

                try:
                    group.privileges.get(type=message_type, target=target)
                    messages.warning(
                        request, 'Privilege was not added as it already exists.'
                    )
                except Privilege.DoesNotExist:
                    group.privileges.create(type=message_type, target=target)
                    messages.success(request, 'Privilege has been added.')

                return HttpResponseRedirect(
                    reverse('useradmin-group_detail', args=[group.id])
                )
        elif 'submit_account' in request.POST:
            account_form = forms.AccountAddForm(group, request.POST)

            if account_form.is_valid():
                try:
                    account = account_form.cleaned_data['account']
                    group.accounts.get(login=account.login)
                    messages.warning(
                        request,
                        'Account %s was not added as it is '
                        'already a member of the group.' % account,
                    )
                except Account.DoesNotExist:
                    group.accounts.add(account)
                    log_add_account_to_group(request, group, account)
                    messages.success(request, 'Account %s has been added.' % account)

                return HttpResponseRedirect(
                    reverse('useradmin-group_detail', args=[group.id])
                )

    active = {'group_detail': True} if group else {'group_new': True}

    context = {
        'active': active,
        'group': group,
        'group_form': group_form,
        'account_form': account_form,
        'privilege_form': privilege_form,
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/group_detail.html', context)


def group_delete(request, group_id):
    """Controller for deleting a user group"""
    try:
        group = AccountGroup.objects.get(id=group_id)
    except AccountGroup.DoesNotExist:
        messages.error(request, 'Group %s does not exist.' % (group_id))
        return HttpResponseRedirect(reverse('useradmin-group_list'))

    if group.is_system_group():
        messages.error(
            request, 'Group %s is a system group and can not be deleted.' % (group)
        )
        return HttpResponseRedirect(reverse('useradmin-group_detail', args=[group.id]))

    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group %s has been deleted.' % (group))
        return HttpResponseRedirect(reverse('useradmin-group_list'))

    context = {
        'name': group,
        'type': 'group',
        'action': 'delete group',
        'back': reverse('useradmin-group_detail', args=[group.id]),
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/delete.html', context)


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
        privilege = group.privileges.get(id=privilege_id)
    except Privilege.DoesNotExist:
        messages.warning(
            request,
            'Privilege %s does not exist or it is not associated '
            'with %s.' % (privilege_id, group),
        )
        account = get_account(request)
        return HttpResponseRedirect(
            reverse('useradmin-account_detail', args=[account.id])
        )

    if request.method == 'POST':
        privilege.delete()
        messages.success(
            request, 'Privilege %s has been removed from group %s.' % (privilege, group)
        )
        return HttpResponseRedirect(reverse('useradmin-group_detail', args=[group.id]))

    context = {
        'name': '%s from %s' % (privilege, group),
        'type': 'privilege',
        'action': 'revoke privilege',
        'back': reverse('useradmin-group_detail', args=[group.id]),
    }
    context.update(DEFAULT_NAVPATH)
    return render(request, 'useradmin/delete.html', context)


class NavPathMixin(object):
    def get_context_data(self, **kwargs):
        context = super(NavPathMixin, self).get_context_data(**kwargs)
        context.update(DEFAULT_NAVPATH)
        return context


class TokenList(NavPathMixin, generic.ListView):
    """Class based view for a token listing"""

    model = APIToken
    template_name = 'useradmin/token_list.html'

    def get_context_data(self, **kwargs):
        context = super(TokenList, self).get_context_data(**kwargs)
        context['active'] = {'token_list': True}
        return context


class TokenCreate(NavPathMixin, generic.CreateView):
    """Class based view for creating a new token"""

    model = APIToken
    form_class = forms.TokenForm
    template_name = 'useradmin/token_edit.html'

    def post(self, request, *args, **kwargs):
        response = super(TokenCreate, self).post(request, *args, **kwargs)
        messages.success(request, 'New token created')
        account = get_account(request)
        LogEntry.add_create_entry(account, self.object)
        return response


class TokenEdit(NavPathMixin, generic.UpdateView):
    """Class based view for editing a token"""

    model = APIToken
    form_class = forms.TokenForm
    template_name = 'useradmin/token_edit.html'

    def post(self, request, *args, **kwargs):
        old_object = copy.deepcopy(self.get_object())
        response = super(TokenEdit, self).post(request, *args, **kwargs)
        messages.success(request, 'Token saved')
        account = get_account(request)
        LogEntry.compare_objects(
            account,
            old_object,
            self.get_object(),
            ['expires', 'permission', 'endpoints', 'comment'],
        )
        return response


class TokenDelete(generic.DeleteView):
    """Delete a token"""

    model = APIToken

    def get_success_url(self):
        return reverse_lazy('useradmin-token_list')

    def delete(self, request, *args, **kwargs):
        old_object = copy.deepcopy(self.get_object())
        response = super(TokenDelete, self).delete(self, request, *args, **kwargs)
        messages.success(request, 'Token deleted')
        account = get_account(request)
        LogEntry.add_delete_entry(account, old_object)
        return response


class TokenDetail(NavPathMixin, generic.DetailView):
    """Display details for a token"""

    model = APIToken
    template_name = 'useradmin/token_detail.html'


@require_POST
def token_expire(request, pk):
    """Expire a token

    :param pk: Primary key
    :type request: django.http.request.HttpRequest
    """
    token = get_object_or_404(APIToken, pk=pk)
    token.expires = datetime.now()
    token.save()

    account = get_account(request)
    LogEntry.add_log_entry(
        account,
        'edit-apitoken-expiry',
        '{actor} expired {object}',
        object=token,
    )
    messages.success(request, 'Token has been manually expired')
    return redirect(token)


def log_account_change(actor, old, new):
    """Log change to account"""
    if not old:
        LogEntry.add_create_entry(actor, new)
        return

    attribute_list = ['login', 'name', 'password', 'ext_sync']
    LogEntry.compare_objects(
        actor, old, new, attribute_list, censored_attributes=['password']
    )


def log_add_account_to_group(request, group, account):
    logged_in_account = get_account(request)
    LogEntry.add_log_entry(
        logged_in_account,
        'edit-account-add-group',
        '{actor} added user {object} to group {target}',
        target=group,
        object=account,
    )


def log_add_account_to_org(request, organization, account):
    logged_in_account = get_account(request)
    LogEntry.add_log_entry(
        logged_in_account,
        'edit-account-add-org',
        '{actor} added user {object} to organization {target}',
        target=organization,
        object=account,
    )


class JWTList(NavPathMixin, generic.ListView):
    """Class based view for a token listing"""

    model = JWTRefreshToken
    template_name = 'useradmin/jwt_list.html'

    def get_context_data(self, **kwargs):
        context = super(JWTList, self).get_context_data(**kwargs)
        context['is_configured'] = LOCAL_JWT_IS_CONFIGURED
        context['active'] = {'jwt_list': True}
        return context


class JWTCreate(NavPathMixin, generic.View):
    """Class based view for creating a new token"""

    model = JWTRefreshToken
    form_class = forms.JWTRefreshTokenCreateForm
    template_name = 'useradmin/jwt_edit.html'

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            token = form.save(commit=False)
            try:
                encoded_token = generate_refresh_token_from_model(token)
            except ConfigurationError:
                return render(
                    request,
                    'useradmin/jwt_not_enabled.html',
                )
            claims = decode_token(encoded_token)
            token.expires = datetime.fromtimestamp(claims['exp'], tz=timezone.utc)
            token.activates = datetime.fromtimestamp(claims['nbf'], tz=timezone.utc)
            token.hash = hash_token(encoded_token)
            token.save()
            return render(
                request,
                'useradmin/jwt_created.html',
                {"object": token, "token": encoded_token},
            )
        return render(request, self.template_name, {"form": form})

    def get(self, request):
        form = self.form_class()
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)


class JWTEdit(NavPathMixin, generic.View):
    """Class based view for creating a new token"""

    model = JWTRefreshToken
    form_class = forms.JWTRefreshTokenEditForm
    template_name = 'useradmin/jwt_edit.html'

    def post(self, request, *args, **kwargs):
        token = get_object_or_404(JWTRefreshToken, pk=kwargs['pk'])
        form = self.form_class(request.POST, instance=token)
        if form.is_valid():
            form.save()
            return redirect('useradmin-jwt_detail', pk=token.pk)
        return render(request, self.template_name, {"form": form, "object": token})

    def get(self, request, *args, **kwargs):
        token = JWTRefreshToken.objects.get(pk=kwargs['pk'])
        form = self.form_class(instance=token)
        return render(request, self.template_name, {"form": form, "object": token})


class JWTDetail(NavPathMixin, generic.DetailView):
    """Display details for a token"""

    model = JWTRefreshToken
    template_name = 'useradmin/jwt_detail.html'


class JWTDelete(generic.DeleteView):
    """Delete a token"""

    model = JWTRefreshToken

    def get_success_url(self):
        return reverse_lazy('useradmin-jwt_list')

    def delete(self, request, *args, **kwargs):
        old_object = copy.deepcopy(self.get_object())
        response = super(JWTDelete, self).delete(self, request, *args, **kwargs)
        messages.success(request, 'Token deleted')
        account = get_account(request)
        LogEntry.add_delete_entry(account, old_object)
        return response


@require_POST
def jwt_revoke(request, pk):
    """Revoke a jwt token
    :param pk: Primary key
    :type request: django.http.request.HttpRequest
    """
    token = get_object_or_404(JWTRefreshToken, pk=pk)
    token.revoked = True
    token.save()

    account = get_account(request)
    LogEntry.add_log_entry(
        account,
        'edit-jwttoken-revoked',
        '{actor} revoked {object}',
        object=token,
    )
    messages.success(request, 'Token has been manually revoked')
    return redirect('useradmin-jwt_detail', pk=token.pk)


@require_POST
def jwt_recreate(request, pk):
    """Recreate a jwt token. This will invalidate the old token
    related to this object.
    :param pk: Primary key
    :type request: django.http.request.HttpRequest
    """
    token = get_object_or_404(JWTRefreshToken, pk=pk)
    try:
        encoded_token = generate_refresh_token_from_model(token)
    except ConfigurationError:
        return render(
            request,
            'useradmin/jwt_not_enabled.html',
        )
    claims = decode_token(encoded_token)
    token.expires = datetime.fromtimestamp(claims['exp'], tz=timezone.utc)
    token.activates = datetime.fromtimestamp(claims['nbf'], tz=timezone.utc)
    token.hash = hash_token(encoded_token)
    token.revoked = False
    token.save()

    account = get_account(request)
    LogEntry.add_log_entry(
        account,
        'edit-jwttoken-expiry',
        '{actor} recreated {object}',
        object=token,
    )
    messages.success(request, 'Token has been manually recreated')
    return render(
        request, 'useradmin/jwt_created.html', {"object": token, "token": encoded_token}
    )


def generate_refresh_token_from_model(token: JWTRefreshToken):
    endpoint_list = [endpoint for endpoint in token.endpoints.values()]
    encoded_token = generate_refresh_token(
        {
            "write": True if token.permission == 'write' else False,
            "endpoints": endpoint_list,
        }
    )
    return encoded_token

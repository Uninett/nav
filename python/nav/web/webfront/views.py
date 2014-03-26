#
# Copyright (C) 2009-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import os
from datetime import datetime
import simplejson
import logging

from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from django.views.decorators.debug import (sensitive_variables,
                                           sensitive_post_parameters)
from django.shortcuts import get_object_or_404

from nav.django.auth import ACCOUNT_ID_VAR, desudo
from nav.path import sysconfdir
from nav.django.utils import get_account
from nav.models.profiles import (Account, NavbarLink,
                                 AccountTool, AccountProperty)
from nav.web import ldapauth, auth
from nav.web.webfront.utils import quick_read, tool_list
from nav.web.webfront.forms import LoginForm, NavbarlinkForm, NavbarLinkFormSet, ChangePasswordForm
from nav.web.navlets import get_navlets
from nav.web.message import new_message, Messages

_logger = logging.getLogger('nav.web.tools')

WEBCONF_DIR_PATH = os.path.join(sysconfdir, "webfront")
WELCOME_ANONYMOUS_PATH = os.path.join(WEBCONF_DIR_PATH, "welcome-anonymous.txt")
WELCOME_REGISTERED_PATH = os.path.join(WEBCONF_DIR_PATH, "welcome-registered.txt")
NAV_LINKS_PATH = os.path.join(WEBCONF_DIR_PATH, "nav-links.conf")


def index(request):
    # Read files that will be displayed on front page
    if request.account.is_default_account():
        welcome = quick_read(WELCOME_ANONYMOUS_PATH)
    else:
        welcome = quick_read(WELCOME_REGISTERED_PATH)

    return direct_to_template(
        request,
        'webfront/index.html',
        {
            'navpath': [('Home', '/')],
            'date_now': datetime.today(),
            'welcome': welcome,
            'navlets': get_navlets(),
            'title': 'Welcome to NAV',
        }
    )

@sensitive_post_parameters('password')
def login(request):
    if request.method == 'POST':
        return do_login(request)

    origin = request.GET.get('origin', '').strip()
    if 'noaccess' in request.GET:
        if request.account.is_default_account():
            errors = ['You need to log in to access this resource']
        else:
            errors = ['You have insufficient privileges to access this '
                      'resource. Please log in as another user.']
    else:
        errors = []

    return direct_to_template(
        request,
        'webfront/login.html',
        {
            'form': LoginForm(initial={'origin': origin}),
            'origin': origin,
            'errors': errors,
        }
    )


@sensitive_variables('password')
def do_login(request):
    # FIXME Log stuff?
    errors = []
    form = LoginForm(request.POST)
    origin = request.POST.get('origin', '').strip()

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            account = auth.authenticate(username, password)
        except ldapauth.Error, e:
            errors.append('Error while talking to LDAP:\n%s' % e)
        else:
            if account:
                try:
                    request.session[ACCOUNT_ID_VAR] = account.id
                    request.account = account
                except ldapauth.Error, e:
                    errors.append('Error while talking to LDAP:\n%s' % e)
                else:
                    _logger.info("%s successfully logged in", account.login)
                    if not origin:
                        origin = reverse('webfront-index')
                    return HttpResponseRedirect(origin)
            else:
                _logger.info("failed login: %r", username)
                errors.append('Username or password is incorrect.')

    # Something went wrong. Display login page with errors.
    return direct_to_template(
        request,
        'webfront/login.html',
        {
            'form': form,
            'errors': errors,
            'origin': origin,
        }
    )


def logout(request):
    if request.method == 'POST' and 'submit_desudo' in request.POST:
        desudo(request)
        return HttpResponseRedirect(reverse('webfront-index'))
    else:
        del request.session[ACCOUNT_ID_VAR]
        del request.account
        request.session.set_expiry(datetime.now())
        request.session.save()
    return HttpResponseRedirect('/')


def about(request):
    return direct_to_template(
        request,
        'webfront/about.html',
        {
            'navpath': [('Home', '/'), ('About', None)],
            'title': 'About NAV',
        }
    )


def toolbox(request):
    """Render the toolbox"""
    account = get_account(request)
    try:
        layout_prop = AccountProperty.objects.get(account=account,
                                            property='toolbox-layout')
        layout = layout_prop.value
    except AccountProperty.DoesNotExist:
        layout = 'grid'

    tools = sorted(get_account_tools(account, tool_list(account)))

    return direct_to_template(
        request,
        'webfront/toolbox.html',
        {
            'navpath': [('Home', '/'), ('Toolbox', None)],
            'layout': layout,
            'tools': tools,
            'title': 'NAV toolbox',
        },
    )


def get_account_tools(account, all_tools):
    """Get tools for this account"""
    account_tools = account.accounttool_set.all()
    tools = []
    for tool in all_tools:
        try:
            account_tool = account_tools.get(toolname=tool.name)
        except AccountTool.DoesNotExist:
            tools.append(tool)
        else:
            tool.priority = account_tool.priority
            tool.display = account_tool.display
            tools.append(tool)
    return tools


def save_tools(request):
    """Save changes to tool setup for user"""
    account = get_account(request)
    if account.is_default_account():
        return HttpResponse(status=401)

    if 'data' in request.POST:
        account = get_account(request)
        tools = simplejson.loads(request.POST.get('data'))
        for toolname, options in tools.items():
            try:
                atool = AccountTool.objects.get(account=account,
                                                toolname=toolname)
            except AccountTool.DoesNotExist:
                atool = AccountTool(account=account, toolname=toolname)

            atool.priority = options['index']
            atool.display = options['display']
            atool.save()

    return HttpResponse()


def set_tool_layout(request):
    """Save tool layout for user"""
    account = get_account(request)
    if account.is_default_account():
        return HttpResponse(status=401)

    if 'layout' in request.POST:
        account = get_account(request)
        layout = request.POST['layout']
        if layout in ['grid', 'list']:
            try:
                layout_prop = AccountProperty.objects.get(
                    account=account, property='toolbox-layout')
            except AccountProperty.DoesNotExist:
                layout_prop = AccountProperty(account=account,
                                             property='toolbox-layout')

            layout_prop.value = layout
            layout_prop.save()

    return HttpResponse()


def _create_preference_context(request):
    """ Creates a context used by different views for the multiform preference page """
    account = get_account(request)

    if account.ext_sync:
        password_form = None
    else:
        password_form = ChangePasswordForm()

    context = {
        'navpath': [('Home', '/'), ('Preferences', None)],
        'title': 'Personal NAV preferences',
        'password_form': password_form,
        'account': account,
        'tool': {'name': 'My account',
                 'description': 'Edit my personal NAV account settings'},
        'navbar_formset': NavbarLinkFormSet(queryset=NavbarLink.objects.filter(account=account)),
    }

    return context


def preferences(request):
    """ My preferences """
    context = _create_preference_context(request)

    return direct_to_template(
        request,
        'webfront/preferences.html',
        context
    )


@sensitive_post_parameters('old_password', 'new_password1', 'new_password2')
def change_password(request):
    """ Handles POST requests to change a users password """
    context = _create_preference_context(request)
    account = get_account(request)

    if account.is_default_account():
        return direct_to_template(request, 'useradmin/not-logged-in.html', {})

    if request.method == 'POST':
        password_form = ChangePasswordForm(request.POST, my_account=account)

        if password_form.is_valid():
            account.set_password(password_form.cleaned_data['new_password1'])
            account.save()
            new_message(request, 'Your password has been changed.',
                        type=Messages.SUCCESS)
        else:
            context['password_form'] = password_form
            return direct_to_template(
                request,
                'webfront/preferences.html',
                context
            )
            
    return HttpResponseRedirect(reverse('webfront-preferences'))


def save_links(request):
    """ Saves navigation preference links on a user """
    account = get_account(request)
    formset_from_post = None
    context = _create_preference_context(request)

    if request.method == 'POST':
        formset = NavbarLinkFormSet(request.POST)
        if formset.is_valid():
            for form in formset.deleted_forms:
                instance = form.save(commit=False)
                instance.account = account
                instance.save()

            instances = formset.save(commit=False)
            for instance in instances:
                    instance.account = account
                    instance.save()
            new_message(request, 'Your links were saved.',
                        type=Messages.SUCCESS)
        else:
            context['navbar_formset'] = formset

            return direct_to_template(
                request,
                'webfront/preferences.html',
                context
            )

    return HttpResponseRedirect(reverse('webfront-preferences'))

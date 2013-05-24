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
from ConfigParser import ConfigParser
from datetime import datetime
from urllib import quote, unquote

from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.simple import direct_to_template
from nav.config import read_flat_config
from nav.django.auth import ACCOUNT_ID_VAR, desudo
from nav.path import sysconfdir
from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account
from nav.models.profiles import (Account, AccountNavbar, NavbarLink,
                                 AccountTool, AccountProperty)
from nav.models.manage import Netbox
from nav.web.templates.DjangoCheetah import DjangoCheetah
from nav.web import ldapauth, auth
from nav.web.webfront.utils import quick_read, current_messages, boxes_down, tool_list
from nav.web.webfront.forms import LoginForm, NavbarForm, PersonalNavbarForm
from nav.web.navlets import get_navlets

import simplejson
import logging

_logger = logging.getLogger('nav.web.tools')

WEBCONF_DIR_PATH = os.path.join(sysconfdir, "webfront")
WELCOME_ANONYMOUS_PATH = os.path.join(WEBCONF_DIR_PATH, "welcome-anonymous.txt")
WELCOME_REGISTERED_PATH = os.path.join(WEBCONF_DIR_PATH, "welcome-registered.txt")
CONTACT_INFORMATION_PATH = os.path.join(WEBCONF_DIR_PATH, "contact-information.txt")
EXTERNAL_LINKS_PATH = os.path.join(WEBCONF_DIR_PATH, "external-links.txt")
NAV_LINKS_PATH = os.path.join(WEBCONF_DIR_PATH, "nav-links.conf")

def index(request):
    # Read files that will be displayed on front page
    external_links = quick_read(EXTERNAL_LINKS_PATH)
    contact_information = quick_read(CONTACT_INFORMATION_PATH)
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
            'external_links': external_links,
            'contact_information': contact_information,
            'welcome': welcome,
            'current_messages': current_messages(),
            'navlets': get_navlets(),
            'title': 'Welcome to NAV',
        }
    )

def login(request):
    if request.method == 'POST':
        return do_login(request)

    origin = request.GET.get('origin', '').strip()
    return direct_to_template(
        request,
        'webfront/login.html',
        {
            'form': LoginForm(),
            'origin': origin,
        }
    )

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
                    if not origin:
                        origin = reverse('webfront-index')
                    return HttpResponseRedirect(origin)
            else:
                errors.append('Authentication failed for the specified username and password.')

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


def preferences(request):
    return direct_to_template(
        request,
        'webfront/preferences.html',
        {
            'navpath': [('Home', '/'), ('Preferences', None)],
            'title': 'Personal NAV preferences',
        }
    )

def preferences_navigation(request):
    def formset_wrapper(link_set, checked):
        """Massages data retrieved from the database to fit the forms used.
        """
        data = []
        for link in link_set:
            check = checked.get(link.id, {})
            data.append({
                'id': link.id,
                'name': link.name,
                'url': link.uri,
                'navbar': check.get('navbar', False),
                'qlink1': check.get('qlink1', False),
                'qlink2': check.get('qlink2', False),
            })
        return data

    def get_or_create_accountnavbar(account):
        """Tries to retrive this users navigation bar preferences from the
        database. If nothing is found, we copy the default users preferences.
        """
        account_navbar = AccountNavbar.objects.filter(account=account)
        if len(account_navbar) == 0:
            # No preferences. Set them according to default user
            default_navbar = AccountNavbar.objects.filter(
                account__id=Account.DEFAULT_ACCOUNT)
            for navbar in default_navbar:
                AccountNavbar.objects.create(
                    account=account,
                    navbarlink=navbar.navbarlink,
                    positions=navbar.positions,
                )
            account_navbar = AccountNavbar.objects.filter(account=account)

        # Convert old style positon preferences to new style.
        # Old style is a single string for all positions, new style is a
        # table row per position.
        did_convert = False
        for navbar in account_navbar:
            if navbar.positions not in ('navbar', 'qlink1', 'qlink2'):
                positions = []
                if navbar.positions.count('navbar'):
                    positions.append('navbar')
                if navbar.positions.count('qlink1'):
                    positions.append('qlink1')
                if navbar.positions.count('qlink2'):
                    positions.append('qlink2')
                navbar.delete()

                for position in positions:
                    AccountNavbar.objects.create(
                        account=account,
                        navbarlink=navbar.navbarlink,
                        positions=position,
                    )
                did_convert = True

        # If we did convert preferences, we need to fetch the new objects.
        if did_convert:
            account_navbar = AccountNavbar.objects.filter(account=account)
        return account_navbar

    def save_navbar(data, account):
        """Saves a given formsets cleaned data to the database.

            - data: should be the cleaned data from a formset, not the formset
                    itself
        """
        for link in data:
            # If link is a empty dictionary, we should skip it
            if link:
                # Try to fetch the navbar link from the database if id is
                # supplied.
                try:
                    navbarlink = NavbarLink.objects.get(id=link['id'])
                except (KeyError, NavbarLink.DoesNotExist):
                    navbarlink = NavbarLink()
                    navbarlink.account = account
                else:
                    # If the navbar link was found, and the DELETE flag was
                    # set, we should delete the navbar link.
                    if navbarlink.account == account:
                        if 'DELETE' in link and link['DELETE']:
                            navbarlink.delete()
                            continue

                # Only save navbar link if this user is it's owner.
                if navbarlink.account == account:
                    navbarlink.name = link['name']
                    navbarlink.uri = link['url']
                    navbarlink.save()

                # Remove existing accountnavbar position preferences
                AccountNavbar.objects.filter(
                    account=account, navbarlink=navbarlink
                ).delete()

                positions = []
                if 'navbar' in link and link['navbar']:
                    positions.append('navbar')
                if 'qlink1' in link and link['qlink1']:
                    positions.append('qlink1')
                if 'qlink2' in link and link['qlink2']:
                    positions.append('qlink2')

                # Save the new accountnavbar position preferences
                for position in positions:
                    AccountNavbar.objects.create(
                        account=account,
                        navbarlink=navbarlink,
                        positions=position,
                    )

    account = get_account(request)
    account_navbar = get_or_create_accountnavbar(account)
    NavbarFormset = formset_factory(NavbarForm, extra=0)
    PersonalNavbarFormset = formset_factory(PersonalNavbarForm, extra=1, can_delete=True)

    if request.method == 'POST':
        personal_navbar_formset = PersonalNavbarFormset(
            request.POST,
            prefix='user'
        )
        navbar_formset = NavbarFormset(
            request.POST,
            prefix='default'
        )
        if personal_navbar_formset.is_valid() and navbar_formset.is_valid():
            save_navbar(personal_navbar_formset.cleaned_data, account)
            save_navbar(navbar_formset.cleaned_data, account)
            return HttpResponseRedirect(reverse('webfront-preferences-navigation'))
    else:
        # Figure out which positions should be checked for which links.
        checked = {}
        for navbar in account_navbar:
            check = {}
            if navbar.navbarlink_id not in checked:
                checked[navbar.navbarlink_id] = {}
            checked[navbar.navbarlink_id][navbar.positions] = True

        # Get user links and default links if user is not default account.
        # Default account only has user links, and editing them will effect
        # everyone who uses those links.
        links = {
            'user': NavbarLink.objects.filter(account=account),
            'default': None,
        }
        if account.id != Account.DEFAULT_ACCOUNT:
            links['default'] = NavbarLink.objects.filter(
                account__id=Account.DEFAULT_ACCOUNT)

        personal_navbar_formset = PersonalNavbarFormset(
            initial=formset_wrapper(links['user'], checked),
            prefix='user'
        )
        navbar_formset = NavbarFormset(
            initial=formset_wrapper(links['default'], checked),
            prefix='default'
        )

    navpath = [
        ('Home', '/'),
        ('Preferences', reverse('webfront-preferences')),
        ('Navigation preferences', None)
    ]
    return direct_to_template(
        request,
        'webfront/preferences_navigation.html',
        {
            'navpath': navpath,
            'personal_navbar_formset': personal_navbar_formset,
            'navbar_formset': navbar_formset,
            'title': 'NAVbar preferences',
        }
    )

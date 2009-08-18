# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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
import cgi
from ConfigParser import ConfigParser
from datetime import datetime

from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.views.generic.simple import direct_to_template

from nav.config import readConfig
from nav.path import sysconfdir
from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account
from nav.models.profiles import Account, AccountNavbar, NavbarLink
from nav.models.manage import Netbox
from nav.web.templates.DjangoCheetah import DjangoCheetah

from nav.web import ldapAuth, auth
from nav.web.state import deleteSessionCookie
from nav.web.webfront.utils import quick_read, current_messages, boxes_down, tool_list
from nav.web.webfront.forms import LoginForm, NavbarForm, PersonalNavbarForm

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
    if request._req.session['user']['id'] == Account.DEFAULT_ACCOUNT:
        welcome = quick_read(WELCOME_ANONYMOUS_PATH)
    else:
        welcome = quick_read(WELCOME_REGISTERED_PATH)

    # Read nav-links
    nav_links = readConfig(NAV_LINKS_PATH)

    down = boxes_down()
    num_shadow = 0
    for box in down:
        if box.netbox.up == Netbox.UP_SHADOW:
            num_shadow += 1

    return direct_to_template(
        request,
        'webfront/index.html',
        {
            'navpath': [('Home', '/')],
            'date_now': datetime.today(),
            'external_links': external_links,
            'contact_information': contact_information,
            'welcome': welcome,
            'nav_links': nav_links,
            'current_messages': current_messages(),
            'boxes_down': down,
            'num_shadow': num_shadow,
        }
    )

def login(request):
    if request.method == 'POST':
        return do_login(request)

    return direct_to_template(
        request,
        'webfront/login.html',
        {
            'form': LoginForm(),
            'origin': cgi.escape(request.GET.get('origin', '').strip()),
        }
    )

def do_login(request):
    # FIXME Log stuff?
    errors = []
    form = LoginForm(request.POST)
    origin = cgi.escape(request.POST.get('origin', '').strip())

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            account = auth.authenticate(username, password)
        except ldapAuth.Error, e:
            errors.append('Error while talking to LDAP:\n%s' % e)
        else:
            if account:
                try:
                    auth.login(request, account)
                except ldapAuth.Error, e:
                    errors.append('Error while talking to LDAP:\n%s' % e)
                else:
                    if not origin:
                        origin = '/index/index'
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
    auth.logout(request)
    return HttpResponseRedirect('/')

def about(request):
    return direct_to_template(
        request,
        'webfront/about.html',
        {
            'navpath': [('Home', '/'), ('About', None)],
        }
    )

def toolbox(request):
    account = get_account(request)
    tools = tool_list(account)
    return direct_to_template(
        request,
        'webfront/toolbox.html',
        {
            'navpath': [('Home', '/'), ('Toolbox', None)],
            'tools': tools,
        },
    )

def preferences(request):
    return direct_to_template(
        request,
        'webfront/preferences.html',
        {
            'navpath': [('Home', '/'), ('Preferences', None)],
        }
    )

def preferences_navigation(request):
    def formset_wrapper(link_set, checked):
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
        account_navbar = AccountNavbar.objects.filter(account=account)
        if len(account_navbar) == 0:
            # No preferences. Set them according to default user
            default_navbar = AccountNavbar.objects.filter(
                account__id=Account.DEFAULT_ACCOUNT)
            for navbar in default_navbar:
                AccountNavbar.create(
                    account=account,
                    navbarlink=navbar.navbarlink,
                    positions=navbar.positions,
                )
            account_navbar = AccountNavbar.objects.filter(account=account)
        return account_navbar

    def save_navbar(data):
        for link in data:
            if link:
                try:
                    navbarlink = NavbarLink.objects.get(id=link['id'])
                except (KeyError, NavbarLink.DoesNotExist):
                    navbarlink = NavbarLink()
                    navbarlink.account = account
                else:
                    if navbarlink.account == account:
                        if 'DELETE' in link and link['DELETE']:
                            navbarlink.delete()
                            continue

                if navbarlink.account == account:
                    navbarlink.name = link['name']
                    navbarlink.uri = link['url']
                    navbarlink.save()

                try:
                    navbar = AccountNavbar.objects.get(
                        account=account, navbarlink=link['id']
                    )
                except (KeyError, AccountNavbar.DoesNotExist):
                    navbar = AccountNavbar()
                    navbar.account = account

                positions = []
                if 'navbar' in link and link['navbar']:
                    positions.append('navbar')
                if 'qlink1' in link and link['qlink1']:
                    positions.append('qlink1')
                if 'qlink2' in link and link['qlink2']:
                    positions.append('qlink2')

                if len(positions) > 0:
                    navbar.positions = ','.join(positions)
                    navbar.navbarlink = navbarlink
                    navbar.save()
                else:
                    if navbar.id:
                        navbar.delete()

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
            save_navbar(personal_navbar_formset.cleaned_data)
            save_navbar(navbar_formset.cleaned_data)
            return HttpResponseRedirect(reverse('webfront-preferences-navigation'))
    else:
        checked = {}
        for navbar in account_navbar:
            check = {}
            if navbar.positions.count('navbar'):
                check['navbar'] = True
            if navbar.positions.count('qlink1'):
                check['qlink1'] = True
            if navbar.positions.count('qlink2'):
                check['qlink2'] = True
            checked[navbar.navbarlink_id] = check

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
        }
    )

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
from ConfigParser import ConfigParser
from datetime import datetime

from django.template import RequestContext
from django.http import HttpResponseRedirect

from nav.path import sysconfdir
from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account
from nav.models.profiles import Account
from nav.models.manage import Netbox
from nav.web.templates.DjangoCheetah import DjangoCheetah

from nav.web import ldapAuth
from nav.web.state import deleteSessionCookie
from nav.web.webfront.utils import quick_read, current_messages, boxes_down, tool_list
from nav.web.webfront.forms import LoginForm

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
    config = ConfigParser()
    config.read(NAV_LINKS_PATH)
    nav_links = config.items('Links')

    down = boxes_down()
    num_shadow = 0
    for box in down:
        if box.netbox.up == Netbox.UP_SHADOW:
            num_shadow += 1

    return render_to_response(
        DjangoCheetah,
        'webfront/index.html',
        {
            'date_now': datetime.today(),
            'external_links': external_links,
            'contact_information': contact_information,
            'welcome': welcome,
            'nav_links': nav_links,
            'current_messages': current_messages(),
            'boxes_down': down,
            'num_shadow': num_shadow,
        },
        RequestContext(request)
    )

def login(request):
    if request.method == 'POST':
        return do_login(request)

    from django.shortcuts import render_to_response
    return render_to_response(
        'webfront/login.html',
        {'form': LoginForm()}
    )

def do_login(request):
    # FIXME Log stuff?
    errors = []
    form = LoginForm(request.POST)
    auth = False
    if form.is_valid():
        # Invalidate old sessions
        if request._req.session.has_key('user'):
            del request._req.session['user']
            request._req.session.save()

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        # Find account in database, or try ldap if account is not found
        account = None
        try:
            account = Account.objects.get(login=username)
        except Account.DoesNotExist:
            if ldapAuth.available:
                try:
                    auth = ldapAuth.authenticate(username, password)
                except ldapAuth.Error, e:
                    errors.append('Error while talking to LDAP server:\n%s' % e)
                else:
                    if not auth:
                        errors.append(Message.ERROR, 'LDAP authentication failed.')
                    name = ldapAuth.getUserName(username)
                    account = Account(
                        login=username,
                        name=name,
                        ext_sync='ldap'
                    )
                    account.set_password(password)
                    account.save()

        if account and not auth:
            if account.ext_sync == 'ldap' and ldapAuth.available:
                # Try to authenticate with LDAP if user has specified this.
                try:
                    auth = ldapAuth.authenticate(username, password)
                except ldapAuth.Error, e:
                    errors.append(Message.ERROR, 'Error while talking to LDAP server:\n%s' % e)
                else:
                    account.set_password(password)
                    account.save()
            else:
                # Authenticate against database
                auth = account.check_password(password)

        if auth:
            # We are authenticated, return user to where he wants to go.
            request._req.session['user'] = {
                'id': account.id,
                'login': account.login,
                'name': account.name,
            }
            request._req.session.save()
            return HttpResponseRedirect('/')
        else:
            errors.append('Login failed')

    # Something went wrong. Display login page with errors.
    form.password = None
    from django.shortcuts import render_to_response
    return render_to_response(
        'webfront/login.html',
        {
            'form': form,
            'errors': errors,
        }
    )

def logout(request):
    request._req.session.expire()
    del request._req.session
    deleteSessionCookie(request._req)
    return HttpResponseRedirect('/')

def about(request):
    return render_to_response(
        DjangoCheetah,
        'webfront/about.html',
        {},
        RequestContext(request),
        path=[
            ('Home', '/'),
            ('About', None),
        ]
    )

def toolbox(request):
    account = get_account(request)
    tools = tool_list(account)
    return render_to_response(
        DjangoCheetah,
        'webfront/toolbox.html',
        {
            'tools': tools,
        },
        RequestContext(request),
        path=[
            ('Home', '/'),
            ('Toolbox', None),
        ]
    )

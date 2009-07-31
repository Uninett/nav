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

from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.views.generic.simple import direct_to_template

from nav.config import readConfig
from nav.path import sysconfdir
from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account
from nav.models.profiles import Account
from nav.models.manage import Netbox
from nav.web.templates.DjangoCheetah import DjangoCheetah

from nav.web import ldapAuth, auth
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
        {}
    )

def toolbox(request):
    account = get_account(request)
    tools = tool_list(account)
    return direct_to_template(
        request,
        'webfront/toolbox.html',
        {
            'tools': tools,
        },
    )

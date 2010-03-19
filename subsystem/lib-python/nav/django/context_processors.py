# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 UNINETT AS
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

"""Context processors for NAV."""

from django.conf import settings

from nav.django.utils import get_account, is_admin
from nav.web.message import new_message, Messages
from nav.web.webfront.utils import tool_list
from nav.models.profiles import AccountNavbar
from nav.buildconf import VERSION

def debug(request):
    """Returns context variables helpful for debugging.

    Same as django.core.context_processors.debug, just without the check
    against INTERNAL_IPS."""
    context_extras = {}
    if settings.DEBUG:
        context_extras['debug'] = True
        from django.db import connection
        context_extras['sql_queries'] = connection.queries
    return context_extras

def account_processor(request):
    """Provides account information to RequestContext.

    Returns these variables:
     - account: This is the nav.models.profiles.Account object representing the
       current user.
     - is_admin: Does this user belong to the NAV administrator group
     - messages: A list of message dictionaries which is meant for the user to
       see.
    """
    account = get_account(request)
    admin = is_admin(account)
    messages = Messages(request)
    messages = messages.get_and_delete()

    navbar = []
    qlink1 = []
    qlink2 = []

    preferences = AccountNavbar.objects.select_related(
        'navbarlink'
    ).filter(account=account)
    if preferences.count() == 0:
        preferences = AccountNavbar.objects.select_related(
            'navbarlink'
        ).filter(account__id=0)

    for p in preferences:
        link = {
            'name': p.navbarlink.name,
            'uri': p.navbarlink.uri,
        }
        if p.positions.count('navbar'):
            navbar.append(link)
        if p.positions.count('qlink1'):
            qlink1.append(link)
        if p.positions.count('qlink2'):
            qlink2.append(link)

    return {
        'account': account,
        'is_admin': admin,
        'messages': messages,
        'navbar': navbar,
        'qlink1': qlink1,
        'qlink2': qlink2,
    }

def nav_version(request):
    return {
        'nav_version': VERSION,
    }

def toolbox(request):
    return {'available_tools': tool_list(get_account(request))}

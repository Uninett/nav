# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Context processors for NAV."""

import os
from operator import attrgetter

from django.conf import settings

from nav.config import find_configfile
from nav.django.auth import get_sudoer
from nav.django.utils import get_account, is_admin
from nav.web.message import Messages
from nav.web.webfront.utils import tool_list, quick_read, split_tools
from nav.models.profiles import NavbarLink
from nav.buildconf import VERSION
from nav.metrics import CONFIG

CONTACT_INFORMATION_PATH = find_configfile(
    os.path.join("webfront", "contact-information.txt"))


def debug(_request):
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

    if hasattr(request, 'session'):
        messages = Messages(request)
        messages = messages.get_and_delete()
        sudo = get_sudoer(request)
    else:
        messages = None
        sudo = None

    my_links = NavbarLink.objects.filter(account=account)

    tools = sorted(tool_list(account), key=attrgetter('name'))

    current_user_data = {
        'account': account,
        'is_admin': admin,
        'sudoer': sudo,
        'messages': messages,
        'my_links': my_links,
        'tools': tools,
        'split_tools': split_tools(tools)
    }
    return {
        'current_user_data': current_user_data,
    }


def nav_version(_request):
    return {
        'nav_version': VERSION,
    }


def footer_info(_request):
    return {
        'contact_information': quick_read(CONTACT_INFORMATION_PATH)
    }


def toolbox(request):
    return {'available_tools': tool_list(get_account(request))}


def graphite_base(_request):
    """Provide graphite dashboard url in context"""
    return {
        'graphite_base': CONFIG.get('graphiteweb', 'base')
    }

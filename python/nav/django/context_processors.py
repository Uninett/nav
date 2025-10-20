# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Uninett AS
# Copyright (C) 2022 Sikt
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
from django.urls import reverse

from nav.config import find_config_file
from nav.web.auth import get_login_url, get_logout_url
from nav.web.auth.sudo import get_sudoer
from nav.web.auth.utils import get_account
from nav.web.auth.utils import get_number_of_accounts_with_password_issues
from nav.web.message import Messages
from nav.web.webfront.utils import tool_list, quick_read, split_tools
from nav.models.profiles import NavbarLink
from nav.buildconf import VERSION
from nav.metrics import CONFIG

CONTACT_INFORMATION_PATH = find_config_file(
    os.path.join("webfront", "contact-information.txt")
)


def debug(_request):
    """Returns context variables helpful for debugging.

    Same as django.templates.context_processors.debug, just without the check
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
    admin = account.is_admin()

    if hasattr(request, 'session'):
        messages = Messages(request)
        messages = messages.get_and_delete()
        sudo = get_sudoer(request)
    else:
        messages = None
        sudo = None

    my_links = NavbarLink.objects.filter(account=account)

    tools = sorted(tool_list(account), key=attrgetter('name'))

    password_issues = dict()
    if account.has_password_issues():
        password_issues["message"] = (
            "Your account has an insecure or old password. It should be reset."
        )
        password_issues["link"] = reverse("webfront-preferences")
        password_issues["link_message"] = "Change your password here."
    else:
        if admin:
            number_accounts_with_password_issues = (
                get_number_of_accounts_with_password_issues()
            )
            if number_accounts_with_password_issues > 0:
                password_issues["message"] = (
                    f"There are {number_accounts_with_password_issues} accounts that "
                    "have insecure or old passwords."
                )
                password_issues["link"] = reverse("useradmin")
                password_issues["link_message"] = "See which users are affected here."

    current_user_data = {
        'account': account,
        'is_admin': admin,
        'sudoer': sudo,
        'messages': messages,
        'my_links': my_links,
        'tools': tools,
        'split_tools': split_tools(tools),
        'password_issues': password_issues,
    }
    return {
        'current_user_data': current_user_data,
    }


def nav_version(_request):
    return {
        'nav_version': VERSION,
    }


def footer_info(_request):
    return {'contact_information': quick_read(CONTACT_INFORMATION_PATH)}


def toolbox(request):
    return {'available_tools': tool_list(get_account(request))}


def graphite_base(_request):
    """Provide graphite dashboard url in context"""
    return {'graphite_base': CONFIG.get('graphiteweb', 'base')}


def auth(request):
    """Add the correct login url and logout url to context"""
    login_url = get_login_url(request)
    logout_url = get_logout_url(request)
    return {
        'login_url': login_url,
        'logout_url': logout_url,
    }

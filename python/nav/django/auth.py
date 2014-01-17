#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV authentication and authorization middleware for Django"""
import os
import urllib
from logging import getLogger

from nav.models.profiles import Account
from nav.django.utils import is_admin, get_account

from django.core.urlresolvers import reverse
from django.http import (HttpResponseForbidden, HttpResponseRedirect,
                         HttpResponse)

_logger = getLogger(__name__)

ACCOUNT_ID_VAR = 'account_id'
SUDOER_ID_VAR = 'sudoer'


class AuthenticationMiddleware(object):
    def process_request(self, request):
        session = request.session

        if ACCOUNT_ID_VAR not in session:
            session[ACCOUNT_ID_VAR] = Account.DEFAULT_ACCOUNT
        account = Account.objects.get(id=session[ACCOUNT_ID_VAR])
        request.account = account

        _logger.debug("Request for %s authenticated as user=%s",
                      request.get_full_path(), account.login)


class AuthorizationMiddleware(object):
    def process_request(self, request):
        account = request.account

        authorized = (authorization_not_required(request.get_full_path())
                      or
                      account.has_perm('web_access', request.get_full_path()))
        if not authorized:
            _logger.warn("User %s denied access to %s",
                         account.login, request.get_full_path())
            return self.redirect_to_login(request)
        else:
            if not account.is_default_account():
                os.environ['REMOTE_USER'] = account.login
            elif 'REMOTE_USER' in os.environ:
                del os.environ['REMOTE_USER']

    def redirect_to_login(self, request):
        """Redirects a request to the NAV login page, unless it was detected
        to be an AJAX request, in which case return a 401 Not Authorized
        response.

        """
        if request.is_ajax():
            return HttpResponse(status=401)

        new_url = '{0}?origin={1}&noaccess'.format(
            reverse('webfront-login'),
            urllib.quote(request.get_full_path()))
        return HttpResponseRedirect(new_url)


def authorization_not_required(fullpath):
    """Checks is authorization is required for the requested url

    Should the user be able to decide this? Currently not.

    """
    auth_not_required = ['/api/']
    for url in auth_not_required:
        if fullpath.startswith(url):
            return True

#
# sudo-related functionality
#


def sudo(request, other_user):
    """Switches the current session to become other_user"""
    if SUDOER_ID_VAR in request.session:
        # Already logged in as another user.
        raise SudoRecursionError()
    if not is_admin(get_account(request)):
        # Check if sudoer is acctually admin
        raise SudoNotAdminError()
    request.session[SUDOER_ID_VAR] = request.account.id
    request.session[ACCOUNT_ID_VAR] = other_user.id
    request.session.save()
    request.account = other_user


def desudo(request):
    """Switches the current session to become the original user from before a
    call to sudo().

    """
    if not SUDOER_ID_VAR in request.session:
        # We are not sudoing
        return

    original_user_id = request.session[SUDOER_ID_VAR]
    original_user = Account.objects.get(id=original_user_id)

    del request.session[ACCOUNT_ID_VAR]
    del request.session[SUDOER_ID_VAR]
    request.session[ACCOUNT_ID_VAR] = original_user_id
    request.session.save()
    request.account = original_user


def get_sudoer(request):
    """Returns a sudoer's Account, if current session is in sudo-mode"""
    if SUDOER_ID_VAR in request.session:
        return Account.objects.get(id=request.session[SUDOER_ID_VAR])


class SudoRecursionError(Exception):
    msg = u"Already posing as another user"

    def __unicode__(self):
        return self.msg


class SudoNotAdminError(Exception):
    msg = u"Not admin"

    def __unicode__(self):
        return self.msg



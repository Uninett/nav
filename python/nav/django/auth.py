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

from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect

_logger = getLogger(__name__)
ACCOUNT_ID_VAR = 'account_id'


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

        authorized = account.has_perm('web_access', request.get_full_path())
        if not authorized:
            _logger.warn("User %s denied access to %s",
                         account.login, request.get_full_path())
            if account.is_default_account():
                return self.redirect_to_login(request)
            else:
                return HttpResponseForbidden()
        else:
            if not account.is_default_account():
                os.environ['REMOTE_USER'] = account.login
            elif 'REMOTE_USER' in os.environ:
                del os.environ['REMOTE_USER']

    def redirect_to_login(self, request):
        # TODO: check for X-AJAX header
        new_url = '{0}?origin={1}'.format(
            reverse('webfront-login'),
            urllib.quote(request.get_full_path()))
        return HttpResponseRedirect(new_url)

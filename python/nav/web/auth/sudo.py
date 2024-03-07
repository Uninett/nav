# Copyright (C) 2010, 2011, 2013, 2019 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Sudo functionality for web authentication in NAV.
"""

import logging

from nav.auditlog.models import LogEntry
from nav.django.utils import is_admin, get_account
from nav.models.profiles import Account
from nav.web.auth.utils import set_account, clear_session


_logger = logging.getLogger(__name__)


SUDOER_ID_VAR = 'sudoer'


def sudo(request, other_user):
    """Switches the current session to become other_user"""
    if SUDOER_ID_VAR in request.session:
        # Already logged in as another user.
        raise SudoRecursionError()
    if not is_admin(get_account(request)):
        # Check if sudoer is acctually admin
        raise SudoNotAdminError()
    original_user = request.account
    request.session[SUDOER_ID_VAR] = original_user.id
    set_account(request, other_user)
    _logger.info('Sudo: "%s" acting as "%s"', original_user, other_user)
    _logger.debug(
        'Sudo: (session: %s, account: %s)', dict(request.session), request.account
    )
    LogEntry.add_log_entry(
        original_user,
        'sudo',
        '{actor} sudoed to {target}',
        subsystem='auth',
        target=other_user,
    )


def desudo(request):
    """Switches the current session to become the original user from before a
    call to sudo().

    """
    if SUDOER_ID_VAR not in request.session:
        # We are not sudoing
        return

    other_user = request.account
    original_user_id = request.session[SUDOER_ID_VAR]
    original_user = Account.objects.get(id=original_user_id)

    clear_session(request)
    set_account(request, original_user)
    _logger.info(
        'DeSudo: "%s" no longer acting as "%s"', original_user, request.account
    )
    _logger.debug(
        'DeSudo: (session: %s, account: %s)', dict(request.session), request.account
    )
    LogEntry.add_log_entry(
        original_user,
        'desudo',
        '{actor} no longer sudoed as {target}',
        subsystem='auth',
        target=other_user,
    )


def get_sudoer(request):
    """Returns a sudoer's Account, if current session is in sudo-mode"""
    if SUDOER_ID_VAR in request.session:
        return Account.objects.get(id=request.session[SUDOER_ID_VAR])


class SudoRecursionError(Exception):
    msg = u"Already posing as another user"

    def __str__(self):
        return self.msg


class SudoNotAdminError(Exception):
    msg = u"Not admin"

    def __str__(self):
        return self.msg

#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Authentication backends for NAV's web interface."""

import logging
from typing import Optional

from django.contrib.auth.backends import RemoteUserBackend
from django.http import HttpRequest

from nav.auditlog.models import LogEntry
from nav.models.profiles import Account
from nav.web.auth import remote_user


_logger = logging.getLogger(__name__)


class NAVRemoteUserBackend(RemoteUserBackend):
    "An adaptation of Django's RemoteUserBackend that is configurable the NAV way"

    def __init__(self):
        self.create_unknown_user = remote_user.CONFIG.will_autocreate_user()

    def authenticate(
        self, request: Optional[HttpRequest], user: str
    ) -> Optional[Account]:
        """Authenticates the username supplied by the web server.

        Returns the matching account, or None if REMOTE_USER authentication is
        disabled in NAV's configuration, or the username matches no account
        that is allowed to log in.
        """
        if not remote_user.CONFIG.is_remote_user_enabled():
            return None

        user = super().authenticate(request, user)
        return user

    def clean_username(self, username):
        return remote_user.CONFIG.clean_username(username)

    def configure_user(self, request, user, created=True):
        if created:
            user.ext_sync = 'REMOTE_USER'
            user.save()

            remote_user_varname = remote_user.CONFIG.get_remote_user_varname()
            _logger.info(
                "Created user %s from header %s",
                user.get_username(),
                remote_user_varname,
            )
            template = (
                'Account "{actor}" created due to {remote_user_varname} HTTP header'
            )
            LogEntry.add_log_entry(
                user, 'create-account', template=template, subsystem='auth'
            )
        return user

    def user_can_authenticate(self, user):
        active = super().user_can_authenticate(user)

        if not active:
            _logger.info("Locked user %s tried to log in", user.get_username())
            template = 'Account "{actor}" was prevented from logging in: blocked'
            LogEntry.add_log_entry(
                user, 'login-prevent', template=template, subsystem='auth'
            )

        return active

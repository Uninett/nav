#
# Copyright (C) 2025 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
import logging

from django.contrib.auth.backends import RemoteUserBackend

from nav.auditlog.models import LogEntry
from nav.web.auth import remote_user


_logger = logging.getLogger(__name__)


class NAVRemoteUserBackend(RemoteUserBackend):
    def __init__(self):
        self.create_unknown_user = remote_user.will_autocreate_user()

    def authenticate(self, request, remote_user):
        if not remote_user.is_remote_user_enabled():
            return None

        user = super().authenticate(request, remote_user)
        return user

    def clean_username(self, username):
        return remote_user.clean_username(username)

    def configure_user(self, request, user, created=True):
        if created:
            # for the sake of Account.locked
            user.set_password(remote_user.fake_password(32))
            user.ext_sync = 'REMOTE_USER'
            user.save()

            remote_user_varname = remote_user.get_remote_user_varname()
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

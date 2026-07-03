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
"""Authentication signal receivers that record logins in NAV's logs.

Login logging is hung off Django's auth signals rather than a specific view, so
it fires uniformly for every authentication path — the django-allauth login
flow, REMOTE_USER, LDAP, and any future backend.
"""

import logging

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from nav.auditlog.models import LogEntry

_logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Records a successful login in the audit log and the application log"""
    LogEntry.add_log_entry(user, 'log-in', '{actor} logged in', before=user)
    _logger.info("%s successfully logged in", user.get_username())


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request=None, **kwargs):
    """Records a failed login attempt in the application log"""
    # Auth backends name the identity credential differently: allauth uses
    # "username", and NAVRemoteUserBackend uses "user".
    username = (
        credentials.get('username')
        or credentials.get('login')
        or credentials.get('user')
    )
    _logger.info("failed login: %r", username)

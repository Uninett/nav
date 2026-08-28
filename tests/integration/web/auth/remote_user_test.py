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
"""Tests that REMOTE_USER logins work through the full middleware stack.

These drive a Django test client rather than calling
``NAVRemoteUserBackend.authenticate()`` directly, because the bug they guard
against lives in the dispatch *between* the two: Django matches credentials to
backends by binding them against each backend's signature, so a backend whose
parameters are named wrong is skipped without ever being called. A test that
invokes the backend directly cannot observe that.
"""

import logging
from unittest.mock import patch

from django.contrib.auth import SESSION_KEY

from nav.models.profiles import Account


class TestRemoteUserLogin:
    def test_when_remote_user_is_set_then_it_should_log_that_account_in(
        self, db, non_admin_account, anonymous_client, remote_user_auth
    ):
        with remote_user_auth():
            anonymous_client.get("/", REMOTE_USER=non_admin_account.login)

        assert anonymous_client.session.get(SESSION_KEY) == str(non_admin_account.pk)

    def test_when_remote_user_is_set_again_then_it_should_stay_logged_in_without_cycling_the_session(  # noqa: E501
        self, db, non_admin_account, anonymous_client, remote_user_auth
    ):
        with remote_user_auth():
            anonymous_client.get("/", REMOTE_USER=non_admin_account.login)
            session_key_after_login = anonymous_client.session.session_key
            anonymous_client.get("/", REMOTE_USER=non_admin_account.login)

        assert anonymous_client.session.get(SESSION_KEY) == str(non_admin_account.pk)
        assert anonymous_client.session.session_key == session_key_after_login

    def test_when_remote_user_is_unknown_and_autocreate_is_on_then_it_should_create_and_log_in_the_account(  # noqa: E501
        self, db, anonymous_client, remote_user_auth
    ):
        with remote_user_auth(autocreate=True):
            anonymous_client.get("/", REMOTE_USER="newcomer")

        account = Account.objects.get(login="newcomer")
        assert account.ext_sync == "REMOTE_USER"
        assert anonymous_client.session.get(SESSION_KEY) == str(account.pk)

    def test_when_remote_user_is_disabled_then_the_session_should_stay_anonymous(
        self, db, non_admin_account, anonymous_client, remote_user_auth
    ):
        with remote_user_auth(enabled=False):
            anonymous_client.get("/", REMOTE_USER=non_admin_account.login)

        assert anonymous_client.session.get(SESSION_KEY) == str(Account.DEFAULT_ACCOUNT)


class TestRemoteUserDebugLogging:
    def test_when_varname_is_customised_then_the_log_should_name_that_variable(
        self, db, non_admin_account, anonymous_client, remote_user_auth, caplog
    ):
        varname = "HTTP_X_REMOTE_USER"

        # The patch must be active before this client's first request: the
        # middleware reads `self.header` once, when the chain is built.

        with (
            remote_user_auth(),
            patch(
                "nav.web.auth.remote_user.CONFIG.get_remote_user_varname",
                return_value=varname,
            ),
            caplog.at_level(logging.DEBUG, logger="nav.web.auth.middleware"),
        ):
            anonymous_client.get(
                "/", headers={"x-remote-user": non_admin_account.login}
            )

        assert f'request.META["{varname}"]: "{non_admin_account.login}"' in caplog.text

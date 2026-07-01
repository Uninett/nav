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
"""Tests that logins are recorded in the audit log and the application log.

Logins go through django-allauth, so these exercise the real login flow (via the
``log_in`` helper).
"""

import logging

from django.test import Client

from nav.auditlog.models import LogEntry


class TestLoginLogging:
    def test_when_a_user_logs_in_then_it_should_record_an_audit_log_entry(
        self, db, non_admin_account, log_in
    ):
        entries = self._login_entries_for(non_admin_account)
        count_before = entries.count()

        log_in(Client(), non_admin_account.login, "password")

        assert entries.count() == count_before + 1
        assert non_admin_account.login in entries.order_by("-pk").first().summary

    def test_when_a_user_logs_in_then_it_should_log_to_the_application_log(
        self, db, non_admin_account, log_in, caplog
    ):
        with caplog.at_level(logging.INFO):
            log_in(Client(), non_admin_account.login, "password")

        assert f"{non_admin_account.login} successfully logged in" in caplog.text

    def test_when_a_login_attempt_fails_then_it_should_log_to_the_application_log(
        self, db, non_admin_account, log_in, caplog
    ):
        with caplog.at_level(logging.INFO):
            log_in(Client(), non_admin_account.login, "wrong-password")

        assert "failed login" in caplog.text

    def test_when_a_login_attempt_fails_then_it_should_not_record_an_audit_log_entry(
        self, db, non_admin_account, log_in
    ):
        entries = self._login_entries_for(non_admin_account)
        count_before = entries.count()

        log_in(Client(), non_admin_account.login, "wrong-password")

        assert entries.count() == count_before

    @staticmethod
    def _login_entries_for(account):
        """Returns the log-in audit-log entries whose actor is the given account"""
        return LogEntry.objects.filter(verb="log-in", actor_pk=str(account.pk))

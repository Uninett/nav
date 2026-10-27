"""Integration tests for the navuser CLI tool."""

import io
import sys
from unittest.mock import Mock

import pytest

from nav.auditlog.models import LogEntry
from nav.bin.navuser import main
from nav.models.profiles import Account, AccountGroup
from nav.web.auth.utils import default_account
from .utils import run_cli


class TestListCommand:
    """Tests for the navuser list command."""

    def test_when_listing_all_then_it_should_succeed(
        self, unlocked_account, locked_account, capsys
    ):
        code = run_cli(main, "list")
        assert code == 0
        output = capsys.readouterr().out
        assert unlocked_account.login in output
        assert locked_account.login in output

    def test_when_listing_with_verbose_flag_then_it_should_show_locked_indicator(
        self, locked_account, capsys
    ):
        code = run_cli(main, "list", "--verbose")
        assert code == 0
        output = capsys.readouterr().out
        assert f"{locked_account.login}  {locked_account.name}  [locked]" in output

    def test_when_listing_with_verbose_flag_then_it_should_show_external_sync_indicator(
        self, ext_synced_account, capsys
    ):
        code = run_cli(main, "list", "--verbose")
        assert code == 0
        output = capsys.readouterr().out
        assert (
            f"{ext_synced_account.login}  {ext_synced_account.name}  [ldap]" in output
        )


class TestAddCommand:
    """Tests for the navuser add command."""

    def test_when_adding_user_then_it_should_succeed(self, db, capsys):
        code = run_cli(main, "add", "test")
        assert code == 0
        output = capsys.readouterr().err
        assert "User test created" in output
        account = Account.objects.filter(login="test").first()
        assert account

    def test_when_adding_admin_user_then_it_should_succeed(self, db, capsys):
        code = run_cli(main, "add", "adminuser", "--admin")
        assert code == 0
        output = capsys.readouterr().err
        assert "Admin user adminuser created" in output
        account = Account.objects.filter(login="adminuser").first()
        assert account
        assert account.is_admin()

    def test_when_adding_user_with_name_then_it_should_succeed(self, db, capsys):
        code = run_cli(main, "add", "test", "--name", "Test User")
        assert code == 0
        output = capsys.readouterr().err
        assert "User test created" in output
        account = Account.objects.filter(login="test").first()
        assert account
        assert account.name == "Test User"

    def test_when_adding_user_then_it_should_add_log_entry(self, db):
        code = run_cli(main, "add", "test")
        assert code == 0
        account = Account.objects.get(login="test")
        log_entry = LogEntry.objects.filter(
            verb='create-account', object_pk=account.pk
        ).first()
        assert log_entry
        assert "via navuser" in log_entry.summary

    def test_when_user_with_login_already_exists_then_it_should_print_error(
        self, unlocked_account, capsys
    ):
        code = run_cli(main, "add", unlocked_account.login)
        assert code != 0
        output = capsys.readouterr().err
        assert f"User {unlocked_account.login} already exists" in output


class TestRemoveCommand:
    def test_when_removing_user_then_it_should_succeed(
        self, db, unlocked_account, capsys
    ):
        code = run_cli(main, "remove", unlocked_account.login)
        assert code == 0
        output = capsys.readouterr().err
        assert f"User {unlocked_account.login} has been removed" in output
        assert not Account.objects.filter(login=unlocked_account.login).exists()

    def test_when_removing_user_then_it_should_add_log_entry(
        self, unlocked_account, db
    ):
        code = run_cli(main, "remove", unlocked_account.login)
        assert code == 0
        log_entry = LogEntry.objects.filter(
            verb='delete-account', object_pk=unlocked_account.pk
        ).first()
        assert log_entry
        assert "via navuser" in log_entry.summary

    def test_when_removing_non_existing_user_then_it_should_print_error(self, capsys):
        code = run_cli(main, "remove", "doesnotexist")
        assert code != 0
        output = capsys.readouterr().err
        assert "No such user account: doesnotexist" in output


class TestAdminCommand:
    def test_when_making_user_admin_then_it_should_succeed(
        self, db, non_admin_account, capsys
    ):
        code = run_cli(main, "admin", "--add", non_admin_account.login)
        assert code == 0
        output = capsys.readouterr().err
        assert f"User {non_admin_account.login} was made an admin" in output
        assert non_admin_account.is_admin()

    def test_when_making_user_admin_then_it_should_add_log_entry(
        self, non_admin_account, db
    ):
        code = run_cli(main, "admin", "--add", non_admin_account.login)
        assert code == 0

        admin = AccountGroup.objects.get(id=AccountGroup.ADMIN_GROUP)
        log_entry = LogEntry.objects.filter(
            verb='edit-account-add-group', object_pk=non_admin_account.pk
        ).first()
        assert log_entry
        assert f"group {admin.name}" in log_entry.summary
        assert "via navuser" in log_entry.summary

    def test_when_removing_admin_rights_from_user_then_it_should_succeed(
        self, db, admin_account, capsys
    ):
        code = run_cli(main, "admin", "--remove", admin_account.login)
        assert code == 0
        output = capsys.readouterr().err
        assert f"User {admin_account.login} is no longer an admin" in output
        assert not admin_account.is_admin()

    def test_when_removing_admin_rights_from_user_then_it_should_add_log_entry(
        self, admin_account, db
    ):
        code = run_cli(main, "admin", "--remove", admin_account.login)
        assert code == 0

        admin = AccountGroup.objects.get(id=AccountGroup.ADMIN_GROUP)
        log_entry = LogEntry.objects.filter(
            verb='edit-account-remove-group', object_pk=admin_account.pk
        ).first()
        assert log_entry
        assert f"group {admin.name}" in log_entry.summary
        assert "via navuser" in log_entry.summary


class TestLockCommand:
    def test_when_locking_unlocked_account_then_account_should_not_be_active(
        self, db, unlocked_account, capsys
    ):
        code = run_cli(main, "lock", unlocked_account.login)
        assert code == 0
        output = capsys.readouterr().err
        assert f"User {unlocked_account.login} locked" in output
        unlocked_account.refresh_from_db()
        assert not unlocked_account.is_active

    def test_when_locking_account_then_it_should_add_log_entry(
        self, unlocked_account, db
    ):
        code = run_cli(main, "lock", unlocked_account.login)
        assert code == 0

        log_entry = LogEntry.objects.filter(
            verb='lock-account', object_pk=unlocked_account.pk
        ).first()
        assert log_entry
        assert "via navuser" in log_entry.summary

    def test_when_locking_already_locked_account_then_it_should_print_error(
        self, db, locked_account, capsys
    ):
        code = run_cli(main, "lock", locked_account.login)
        assert code != 0
        output = capsys.readouterr().err
        assert f"Cannot lock {locked_account.login}, already locked" in output
        locked_account.refresh_from_db()
        assert not locked_account.is_active


class TestUnlockCommand:
    def test_when_unlocking_locked_account_then_account_should_be_active(
        self, db, locked_account, capsys
    ):
        code = run_cli(main, "unlock", locked_account.login)
        assert code == 0
        output = capsys.readouterr().err
        assert f"User {locked_account.login} unlocked" in output
        locked_account.refresh_from_db()
        assert locked_account.is_active

    def test_when_unlocking_account_then_it_should_add_log_entry(
        self, locked_account, db
    ):
        code = run_cli(main, "unlock", locked_account.login)
        assert code == 0

        log_entry = LogEntry.objects.filter(
            verb='unlock-account', object_pk=locked_account.pk
        ).first()
        assert log_entry
        assert "via navuser" in log_entry.summary

    def test_when_unlocking_already_unlocked_account_then_it_should_print_error(
        self, db, unlocked_account, capsys
    ):
        code = run_cli(main, "unlock", unlocked_account.login)
        assert code != 0
        output = capsys.readouterr().err
        assert f"Cannot unlock {unlocked_account.login}, already unlocked" in output
        unlocked_account.refresh_from_db()
        assert unlocked_account.is_active

    def test_when_unlocking_default_account_then_it_should_print_error(
        self, db, capsys
    ):
        account = default_account()
        code = run_cli(main, "unlock", account.login)
        assert code != 0
        output = capsys.readouterr().err
        assert "It is not possible to unlock the default account." in output
        account.refresh_from_db()
        assert not account.is_active


class TestPasswdCommand:
    def test_when_setting_password_then_it_should_succeed(
        self, non_admin_account, monkeypatch, capsys
    ):
        monkeypatch.setattr(sys, "stdin", io.StringIO("newpassword\n"))
        code = run_cli(main, "passwd", non_admin_account.login)
        assert code == 0
        output = capsys.readouterr().err
        assert "New password saved" in output
        non_admin_account.refresh_from_db()
        assert non_admin_account.check_password("newpassword")

    def test_when_setting_password_then_it_should_add_log_entry(
        self, non_admin_account, monkeypatch
    ):
        monkeypatch.setattr(sys, "stdin", io.StringIO("newpassword\n"))
        code = run_cli(main, "passwd", non_admin_account.login)
        assert code == 0

        log_entry = LogEntry.objects.filter(
            verb='edit-account-password', object_pk=non_admin_account.pk
        ).first()
        assert log_entry
        assert "via navuser" in log_entry.summary

    def test_when_password_is_too_short_then_it_should_print_error(
        self, non_admin_account, monkeypatch, capsys
    ):
        monkeypatch.setattr(sys, "stdin", io.StringIO("short\n"))
        code = run_cli(main, "passwd", non_admin_account.login)
        assert code == 3
        output = capsys.readouterr().err
        assert "Password must be at least 8 characters" in output
        non_admin_account.refresh_from_db()
        assert non_admin_account.check_password("password")

    def test_when_setting_password_for_default_account_then_it_should_print_error(
        self, db, capsys
    ):
        account = default_account()
        code = run_cli(main, "passwd", account.login)
        assert code != 0
        output = capsys.readouterr().err
        assert "It is not possible to set a password for the default account." in output

    def test_when_current_password_is_wrong_then_it_should_print_error(
        self, non_admin_account, interactive_input, capsys
    ):
        interactive_input("wrongpassword")
        code = run_cli(main, "passwd", non_admin_account.login)
        assert code != 0
        output = capsys.readouterr().err
        assert "Authentication error" in output
        non_admin_account.refresh_from_db()
        assert non_admin_account.check_password("password")

    def test_when_new_passwords_do_not_match_then_it_should_print_error(
        self, non_admin_account, interactive_input, capsys
    ):
        interactive_input("password", "newpassword", "otherpassword")
        code = run_cli(main, "passwd", non_admin_account.login)
        assert code == 2
        output = capsys.readouterr().err
        assert "Sorry, passwords do not match" in output
        non_admin_account.refresh_from_db()
        assert non_admin_account.check_password("password")

    def test_when_noverify_flag_is_set_then_it_should_not_ask_for_current_password(
        self, non_admin_account, interactive_input
    ):
        interactive_input("newpassword", "newpassword")
        code = run_cli(main, "passwd", "--noverify", non_admin_account.login)
        assert code == 0
        non_admin_account.refresh_from_db()
        assert non_admin_account.check_password("newpassword")


class TestVerifyCommand:
    def test_when_password_is_correct_then_it_should_succeed(
        self, non_admin_account, monkeypatch
    ):
        monkeypatch.setattr(sys, "stdin", io.StringIO("password\n"))
        code = run_cli(main, "verify", non_admin_account.login)
        assert code == 0

    def test_when_password_is_wrong_then_it_should_fail(
        self, non_admin_account, monkeypatch
    ):
        monkeypatch.setattr(sys, "stdin", io.StringIO("wrongpassword\n"))
        code = run_cli(main, "verify", non_admin_account.login)
        assert code == "Password could not be verified"

    def test_when_password_is_correct_in_terminal_then_it_should_succeed(
        self, non_admin_account, interactive_input
    ):
        interactive_input("password")
        code = run_cli(main, "verify", non_admin_account.login)
        assert code == 0


# Fixtures


@pytest.fixture
def interactive_input(monkeypatch):
    """Simulates a terminal, answering password prompts in the given order"""

    def answer(*passwords):
        monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
        monkeypatch.setattr("nav.bin.navuser.getpass", Mock(side_effect=passwords))

    return answer


@pytest.fixture
def unlocked_account(db):
    account = Account(login="clitest", name="CLI Test User", is_active=True)
    account.save()
    yield account
    account.delete()


@pytest.fixture
def locked_account(db):
    account = Account(login="lockedtest", name="Locked CLI Test User", is_active=False)
    account.save()
    yield account
    account.delete()


@pytest.fixture
def ext_synced_account(db):
    account = Account(
        login="externaltest", name="Externally synced CLI Test User", ext_sync="ldap"
    )
    account.save()
    yield account
    account.delete()

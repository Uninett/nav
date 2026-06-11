"""Integration tests for the navuser CLI tool."""

import pytest

from nav.bin.navuser import main
from nav.models.profiles import Account
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

    def test_when_user_with_login_already_exists_then_it_should_print_error(
        self, db, unlocked_account, capsys
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

    def test_when_removing_non_existing_user_then_it_should_print_error(
        self, db, capsys
    ):
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

    def test_when_removing_admin_rights_from_user_then_it_should_succeed(
        self, db, admin_account, capsys
    ):
        code = run_cli(main, "admin", "--remove", admin_account.login)
        assert code == 0
        output = capsys.readouterr().err
        assert f"User {admin_account.login} is no longer an admin" in output
        assert not admin_account.is_admin()


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


# Fixtures


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

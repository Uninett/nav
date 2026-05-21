"""Integration tests for the navdashboard CLI tool."""

import json

import pytest

from nav.models.profiles import Account, AccountDashboard, AccountNavlet
from nav.bin.navdashboard import main


class TestListCommand:
    """Tests for the navdashboard list command."""

    def test_when_listing_all_then_it_should_succeed(
        self, dashboard_with_widget, capsys
    ):
        code = _run_cli("list")
        assert code == 0
        output = capsys.readouterr().out
        assert "CLI Dashboard" in output
        assert "clitest" in output

    def test_when_listing_with_user_filter_then_it_should_show_only_user_dashboards(
        self, dashboard_with_widget, capsys
    ):
        code = _run_cli("list", "--user", "clitest")
        assert code == 0
        output = capsys.readouterr().out
        assert "CLI Dashboard" in output

    def test_when_listing_as_json_then_it_should_output_valid_json(
        self, dashboard_with_widget, capsys
    ):
        code = _run_cli("list", "--format", "json")
        assert code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert isinstance(data, list)
        cli_dashboard = next(d for d in data if d["name"] == "CLI Dashboard")
        assert cli_dashboard["account"] == "clitest"
        assert cli_dashboard["widget_count"] == 1


class TestExportCommand:
    """Tests for the navdashboard export command."""

    def test_when_exporting_by_name_then_it_should_output_json(
        self, dashboard_with_widget, capsys
    ):
        code = _run_cli("export", "--user", "clitest", "--name", "CLI Dashboard")
        assert code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["name"] == "CLI Dashboard"
        assert len(data["widgets"]) == 1

    def test_when_exporting_by_id_then_it_should_output_json(
        self, dashboard_with_widget, capsys
    ):
        did = dashboard_with_widget.id
        code = _run_cli("export", "--id", str(did))
        assert code == 0
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["name"] == "CLI Dashboard"

    def test_when_exporting_to_file_then_it_should_write_file(
        self, dashboard_with_widget, tmp_path
    ):
        path = str(tmp_path / "export.json")
        code = _run_cli(
            "export", "--user", "clitest", "--name", "CLI Dashboard", "-o", path
        )
        assert code == 0
        with open(path) as f:
            data = json.loads(f.read())
        assert data["name"] == "CLI Dashboard"

    def test_when_user_missing_with_ok_flag_then_it_should_exit_zero(self, db, capsys):
        code = _run_cli(
            "export",
            "--user",
            "nonexistent",
            "--name",
            "foo",
            "--missing-user-ok",
        )
        assert code == 0
        err = capsys.readouterr().err
        assert "does not exist" in err

    def test_when_id_combined_with_user_then_it_should_exit_nonzero(self, db, capsys):
        code = _run_cli("export", "--id", "1", "--user", "admin")
        assert code == 2

    def test_when_neither_id_nor_user_name_then_it_should_exit_nonzero(
        self, db, capsys
    ):
        code = _run_cli("export", "--name", "foo")
        assert code == 2

    def test_when_user_without_name_then_it_should_exit_nonzero(self, db, capsys):
        code = _run_cli("export", "--user", "admin")
        assert code == 2


class TestImportCommand:
    """Tests for the navdashboard import command."""

    def test_when_importing_then_it_should_create_dashboard(
        self, account, tmp_path, capsys
    ):
        path = _write_dashboard_json(tmp_path, name="Imported")
        code = _run_cli("import", "--user", "clitest", "--file", path)
        assert code == 0
        assert AccountDashboard.objects.filter(
            account=account, name="Imported"
        ).exists()

    def test_when_round_tripping_then_data_should_be_preserved(
        self, dashboard_with_widget, tmp_path, capsys
    ):
        path = str(tmp_path / "roundtrip.json")
        _run_cli("export", "--user", "clitest", "--name", "CLI Dashboard", "-o", path)
        code = _run_cli(
            "import",
            "--user",
            "clitest",
            "--file",
            path,
            "--on-conflict",
            "rename",
        )
        assert code == 0
        imported = AccountDashboard.objects.filter(
            account=dashboard_with_widget.account, name="CLI Dashboard (2)"
        )
        assert imported.exists()
        assert imported.first().widgets.count() == 1

    def test_when_replacing_then_it_should_update_in_place(
        self, dashboard_with_widget, tmp_path, capsys
    ):
        original_id = dashboard_with_widget.id
        path = _write_dashboard_json(
            tmp_path, name="CLI Dashboard", num_columns=4, widgets=[]
        )
        code = _run_cli(
            "import",
            "--user",
            "clitest",
            "--file",
            path,
            "--on-conflict",
            "replace",
        )
        assert code == 0
        dashboard_with_widget.refresh_from_db()
        assert dashboard_with_widget.id == original_id
        assert dashboard_with_widget.num_columns == 4
        assert dashboard_with_widget.widgets.count() == 0
        err = capsys.readouterr().err
        assert "Replaced" in err

    def test_when_dry_run_then_it_should_not_modify_db(self, account, tmp_path, capsys):
        path = _write_dashboard_json(tmp_path, name="Dry Run Dashboard", widgets=[])
        code = _run_cli("import", "--user", "clitest", "--file", path, "--dry-run")
        assert code == 0
        assert not AccountDashboard.objects.filter(
            account=account, name="Dry Run Dashboard"
        ).exists()
        err = capsys.readouterr().err
        assert "Dry run" in err

    def test_when_shared_flag_then_it_should_make_dashboard_shared(
        self, account, tmp_path, capsys
    ):
        path = _write_dashboard_json(tmp_path, name="Shared Dashboard", widgets=[])
        code = _run_cli("import", "--user", "clitest", "--file", path, "--shared")
        assert code == 0
        dashboard = AccountDashboard.objects.get(
            account=account, name="Shared Dashboard"
        )
        assert dashboard.is_shared is True
        err = capsys.readouterr().err
        assert "(shared)" in err

    def test_when_user_missing_with_ok_flag_then_it_should_exit_zero(
        self, db, tmp_path, capsys
    ):
        path = _write_dashboard_json(tmp_path, widgets=[])
        code = _run_cli(
            "import",
            "--user",
            "nonexistent",
            "--file",
            path,
            "--missing-user-ok",
        )
        assert code == 0
        err = capsys.readouterr().err
        assert "does not exist" in err


# -- fixtures and helpers --


@pytest.fixture
def account(db):
    account = Account(login="clitest", name="CLI Test User")
    account.save()
    yield account
    account.delete()


@pytest.fixture
def dashboard_with_widget(account):
    dashboard = AccountDashboard.objects.create(
        account=account, name="CLI Dashboard", num_columns=3
    )
    AccountNavlet.objects.create(
        dashboard=dashboard,
        account=account,
        navlet="nav.web.navlets.welcome.WelcomeNavlet",
        column=1,
        order=0,
        preferences={},
    )
    return dashboard


def _run_cli(*args):
    """Run the navdashboard CLI with the given arguments.

    Returns the integer exit code.  Use capsys to capture stdout/stderr.
    """
    import sys

    sys.argv = ["navdashboard"] + list(args)
    try:
        main()
        return 0
    except SystemExit as exc:
        return exc.code if exc.code is not None else 0


def _write_dashboard_json(tmp_path, name="Test Dashboard", num_columns=2, widgets=None):
    """Write a dashboard JSON file and return its path."""
    if widgets is None:
        widgets = [
            {
                "navlet": "nav.web.navlets.welcome.WelcomeNavlet",
                "column": 1,
                "preferences": {},
                "order": 0,
            },
        ]
    data = {
        "name": name,
        "num_columns": num_columns,
        "version": 1,
        "widgets": widgets,
    }
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(data))
    return str(path)

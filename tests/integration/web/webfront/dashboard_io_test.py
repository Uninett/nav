"""Integration tests for nav.web.webfront.dashboard_io import logic."""

import pytest

from nav.models.profiles import Account, AccountDashboard, AccountNavlet
from nav.web.webfront.dashboard_io import (
    ConflictMode,
    DashboardConflictError,
    ImportAction,
    import_from_dict,
    list_dashboards,
)


class TestImportFromDict:
    """Tests for the import_from_dict function."""

    # -- error mode --

    def test_when_no_conflict_then_it_should_create_dashboard(self, account):
        result = import_from_dict(
            account, _make_dashboard_data(), on_conflict=ConflictMode.ERROR
        )

        assert result.dashboard.pk is not None
        assert result.dashboard.name == "Test Dashboard"
        assert result.dashboard.account == account
        assert result.dashboard.widgets.count() == 1
        assert result.action is ImportAction.CREATED

    def test_when_error_mode_and_name_exists_then_it_should_raise(self, account):
        AccountDashboard.objects.create(
            account=account, name="Test Dashboard", num_columns=3
        )

        with pytest.raises(DashboardConflictError, match="already exists"):
            import_from_dict(
                account, _make_dashboard_data(), on_conflict=ConflictMode.ERROR
            )

    # -- replace mode --

    def test_when_replacing_then_it_should_preserve_dashboard_id(self, account):
        existing = AccountDashboard.objects.create(
            account=account, name="Test Dashboard", num_columns=2
        )

        result = import_from_dict(
            account,
            _make_dashboard_data(num_columns=4),
            on_conflict=ConflictMode.REPLACE,
        )

        assert result.dashboard.id == existing.id
        assert result.dashboard.num_columns == 4
        assert result.action is ImportAction.REPLACED

    def test_when_replacing_then_it_should_replace_widgets(self, account):
        existing = AccountDashboard.objects.create(
            account=account, name="Test Dashboard", num_columns=3
        )
        AccountNavlet.objects.create(
            dashboard=existing,
            account=account,
            navlet="old.Widget",
            column=1,
            order=0,
        )

        result = import_from_dict(
            account, _make_dashboard_data(), on_conflict=ConflictMode.REPLACE
        )

        widgets = list(result.dashboard.widgets.values_list("navlet", flat=True))
        assert widgets == ["nav.web.navlets.welcome.WelcomeNavlet"]

    def test_when_replacing_without_match_then_it_should_create_new(self, account):
        result = import_from_dict(
            account, _make_dashboard_data(), on_conflict=ConflictMode.REPLACE
        )

        assert result.dashboard.pk is not None
        assert result.action is ImportAction.CREATED

    def test_when_replacing_ambiguous_match_then_it_should_raise(self, account):
        for _ in range(2):
            AccountDashboard.objects.create(
                account=account, name="Test Dashboard", num_columns=3
            )

        with pytest.raises(DashboardConflictError, match="Ambiguous"):
            import_from_dict(
                account,
                _make_dashboard_data(),
                on_conflict=ConflictMode.REPLACE,
            )

    # -- rename mode --

    def test_when_renaming_without_conflict_then_it_should_use_original_name(
        self, account
    ):
        result = import_from_dict(
            account, _make_dashboard_data(), on_conflict=ConflictMode.RENAME
        )

        assert result.dashboard.name == "Test Dashboard"
        assert result.action is ImportAction.CREATED

    def test_when_renaming_with_conflict_then_it_should_append_suffix(self, account):
        AccountDashboard.objects.create(
            account=account, name="Test Dashboard", num_columns=3
        )

        result = import_from_dict(
            account, _make_dashboard_data(), on_conflict=ConflictMode.RENAME
        )

        assert result.dashboard.name == "Test Dashboard (2)"
        assert result.action is ImportAction.RENAMED

    def test_when_renaming_with_multiple_conflicts_then_it_should_increment(
        self, account
    ):
        AccountDashboard.objects.create(
            account=account, name="Test Dashboard", num_columns=3
        )
        AccountDashboard.objects.create(
            account=account, name="Test Dashboard (2)", num_columns=3
        )

        result = import_from_dict(
            account, _make_dashboard_data(), on_conflict=ConflictMode.RENAME
        )

        assert result.dashboard.name == "Test Dashboard (3)"

    # -- create_new mode --

    def test_when_create_new_and_name_exists_then_it_should_create_duplicate(
        self, account
    ):
        AccountDashboard.objects.create(
            account=account, name="Test Dashboard", num_columns=3
        )

        result = import_from_dict(
            account, _make_dashboard_data(), on_conflict=ConflictMode.CREATE_NEW
        )

        assert result.dashboard.pk is not None
        assert result.action is ImportAction.CREATED
        assert (
            AccountDashboard.objects.filter(
                account=account, name="Test Dashboard"
            ).count()
            == 2
        )

    # -- name_override --

    def test_when_name_override_given_then_it_should_use_override(self, account):
        result = import_from_dict(
            account,
            _make_dashboard_data(name="Original"),
            on_conflict=ConflictMode.ERROR,
            name_override="Overridden",
        )

        assert result.dashboard.name == "Overridden"


class TestListDashboards:
    """Tests for the list_dashboards function."""

    def test_when_no_filter_then_it_should_return_all(self, account):
        AccountDashboard.objects.create(
            account=account, name="Dashboard 1", num_columns=3
        )
        result = list_dashboards()
        assert result.filter(account=account, name="Dashboard 1").exists()

    def test_when_filtered_by_account_then_it_should_only_return_matching(
        self, db, account
    ):
        AccountDashboard.objects.create(account=account, name="Mine", num_columns=3)
        result = list_dashboards(account=account)
        assert all(d.account == account for d in result)


# -- fixtures and helpers --


@pytest.fixture
def account(db):
    account = Account(login="dashtest", name="Dashboard Test User")
    account.save()
    yield account
    account.delete()


def _make_dashboard_data(name="Test Dashboard", num_columns=3, widgets=None):
    """Return a valid dashboard data dict."""
    if widgets is None:
        widgets = [
            {
                "navlet": "nav.web.navlets.welcome.WelcomeNavlet",
                "column": 1,
                "preferences": {},
                "order": 0,
            },
        ]
    return {
        "name": name,
        "num_columns": num_columns,
        "version": 1,
        "widgets": widgets,
    }

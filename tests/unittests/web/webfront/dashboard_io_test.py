"""Unit tests for nav.web.webfront.dashboard_io validation logic."""

import pytest

from nav.web.webfront.dashboard_io import validate_dashboard_data


class TestValidateDashboardData:
    """Tests for the validate_dashboard_data function."""

    def test_when_data_is_valid_then_it_should_return_sanitized_data(self):
        data = _make_dashboard_data()
        result = validate_dashboard_data(data)
        assert result["name"] == "Test Dashboard"
        assert result["num_columns"] == 3
        assert len(result["widgets"]) == 1

    def test_when_data_has_account_field_then_it_should_be_stripped(self):
        data = _make_dashboard_data()
        data["account"] = 42
        result = validate_dashboard_data(data)
        assert "account" not in result

    def test_when_data_is_not_a_dict_then_it_should_raise_value_error(self):
        with pytest.raises(ValueError, match="must be a dict"):
            validate_dashboard_data([1, 2, 3])

    def test_when_name_is_missing_then_it_should_raise_value_error(self):
        data = _make_dashboard_data()
        del data["name"]
        with pytest.raises(ValueError, match="Missing required field.*name"):
            validate_dashboard_data(data)

    def test_when_widgets_is_missing_then_it_should_raise_value_error(self):
        data = _make_dashboard_data()
        del data["widgets"]
        with pytest.raises(ValueError, match="Missing required field.*widgets"):
            validate_dashboard_data(data)

    def test_when_num_columns_has_wrong_type_then_it_should_raise_value_error(self):
        data = _make_dashboard_data(num_columns="three")
        with pytest.raises(ValueError, match="must be int"):
            validate_dashboard_data(data)

    def test_when_widget_is_not_a_dict_then_it_should_raise_value_error(self):
        data = _make_dashboard_data(widgets=["not a dict"])
        with pytest.raises(ValueError, match="Widget 0 must be a dict"):
            validate_dashboard_data(data)

    def test_when_widget_missing_field_then_it_should_raise_value_error(self):
        data = _make_dashboard_data(
            widgets=[{"navlet": "foo", "column": 1, "order": 0}]
        )
        with pytest.raises(ValueError, match="Widget 0 missing.*preferences"):
            validate_dashboard_data(data)

    def test_when_widget_column_exceeds_num_columns_then_it_should_raise(self):
        data = _make_dashboard_data(
            num_columns=2,
            widgets=[
                {
                    "navlet": "foo",
                    "column": 5,
                    "preferences": {},
                    "order": 0,
                }
            ],
        )
        with pytest.raises(ValueError, match="out of range"):
            validate_dashboard_data(data)

    def test_when_widget_column_is_zero_then_it_should_raise(self):
        data = _make_dashboard_data(
            widgets=[
                {
                    "navlet": "foo",
                    "column": 0,
                    "preferences": {},
                    "order": 0,
                }
            ],
        )
        with pytest.raises(ValueError, match="out of range"):
            validate_dashboard_data(data)

    def test_when_widget_has_extra_keys_then_they_should_be_stripped(self):
        data = _make_dashboard_data(
            widgets=[
                {
                    "navlet": "foo",
                    "column": 1,
                    "preferences": {},
                    "order": 0,
                    "extra_field": "should be removed",
                    "id": 999,
                }
            ],
        )
        result = validate_dashboard_data(data)
        assert "extra_field" not in result["widgets"][0]
        assert "id" not in result["widgets"][0]

    def test_when_widget_field_has_wrong_type_then_it_should_raise(self):
        data = _make_dashboard_data(
            widgets=[
                {
                    "navlet": "foo",
                    "column": "one",
                    "preferences": {},
                    "order": 0,
                }
            ],
        )
        with pytest.raises(ValueError, match="must be int"):
            validate_dashboard_data(data)

    def test_when_no_widgets_then_it_should_accept_empty_list(self):
        data = _make_dashboard_data(widgets=[])
        result = validate_dashboard_data(data)
        assert result["widgets"] == []


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

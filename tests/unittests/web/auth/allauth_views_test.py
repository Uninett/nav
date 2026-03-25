from unittest.mock import Mock, patch

from nav.web.auth.allauth.views import NAVConnectionsView


class TestNAVConnectionsView:
    def test_when_user_has_connections_then_it_should_include_connected_providers(self):
        mock_accounts = Mock()
        mock_accounts.values_list.return_value = ["google", "github"]

        mock_form = Mock()
        mock_form.accounts = mock_accounts

        parent_context = {"form": mock_form}

        view = NAVConnectionsView()
        with patch.object(
            NAVConnectionsView.__bases__[0],
            "get_context_data",
            return_value=parent_context,
        ):
            context = view.get_context_data()

        assert context["connected_providers"] == {"google", "github"}
        mock_accounts.values_list.assert_called_once_with("provider", flat=True)

    def test_when_user_has_no_connections_then_it_should_have_empty_set(self):
        mock_accounts = Mock()
        mock_accounts.values_list.return_value = []

        mock_form = Mock()
        mock_form.accounts = mock_accounts

        parent_context = {"form": mock_form}

        view = NAVConnectionsView()
        with patch.object(
            NAVConnectionsView.__bases__[0],
            "get_context_data",
            return_value=parent_context,
        ):
            context = view.get_context_data()

        assert context["connected_providers"] == set()

    def test_when_user_has_connections_then_it_should_preserve_parent_context(self):
        mock_accounts = Mock()
        mock_accounts.values_list.return_value = ["google"]

        mock_form = Mock()
        mock_form.accounts = mock_accounts

        parent_context = {"form": mock_form, "existing_key": "existing_value"}

        view = NAVConnectionsView()
        with patch.object(
            NAVConnectionsView.__bases__[0],
            "get_context_data",
            return_value=parent_context,
        ):
            context = view.get_context_data()

        assert context["existing_key"] == "existing_value"
        assert "connected_providers" in context

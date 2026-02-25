from unittest.mock import Mock, patch

from django.test import RequestFactory

from nav.portadmin.handlers import ManagementError
from nav.web.portadmin.views import commit_configuration


class TestCommitConfiguration:
    @patch("nav.web.portadmin.views.CONFIG")
    def test_when_commit_disabled_it_should_return_200(self, mock_config):
        mock_config.is_commit_enabled.return_value = False
        response = commit_configuration(_make_post_request())
        assert response.status_code == 200

    @patch("nav.web.portadmin.views.get_management_handler")
    @patch("nav.web.portadmin.views.get_object_or_404")
    @patch("nav.web.portadmin.views.CONFIG")
    def test_when_handler_succeeds_it_should_return_200(
        self, mock_config, mock_get_obj, mock_get_handler
    ):
        mock_config.is_commit_enabled.return_value = True
        mock_get_obj.return_value = Mock(netbox=Mock())
        mock_handler = Mock()
        mock_get_handler.return_value = mock_handler

        response = commit_configuration(_make_post_request())

        mock_handler.commit_configuration.assert_called_once()
        assert response.status_code == 200

    @patch("nav.web.portadmin.views.get_management_handler")
    @patch("nav.web.portadmin.views.get_object_or_404")
    @patch("nav.web.portadmin.views.CONFIG")
    def test_when_management_error_it_should_return_503(
        self, mock_config, mock_get_obj, mock_get_handler
    ):
        mock_config.is_commit_enabled.return_value = True
        mock_get_obj.return_value = Mock(netbox=Mock())
        mock_handler = Mock()
        mock_handler.commit_configuration.side_effect = ManagementError("timeout")
        mock_get_handler.return_value = mock_handler

        response = commit_configuration(_make_post_request())

        assert response.status_code == 503
        assert b"timeout" in response.content

    @patch("nav.web.portadmin.views.get_management_handler")
    @patch("nav.web.portadmin.views.get_object_or_404")
    @patch("nav.web.portadmin.views.CONFIG")
    def test_when_commit_not_supported_it_should_return_503(
        self, mock_config, mock_get_obj, mock_get_handler
    ):
        mock_config.is_commit_enabled.return_value = True
        mock_get_obj.return_value = Mock(netbox=Mock())
        mock_handler = Mock()
        mock_handler.commit_configuration.side_effect = NotImplementedError
        mock_get_handler.return_value = mock_handler

        response = commit_configuration(_make_post_request())

        assert response.status_code == 503
        assert b"not supported" in response.content.lower()

    @patch("nav.web.portadmin.views.get_management_handler")
    @patch("nav.web.portadmin.views.get_object_or_404")
    @patch("nav.web.portadmin.views.CONFIG")
    def test_when_no_handler_it_should_return_503(
        self, mock_config, mock_get_obj, mock_get_handler
    ):
        mock_config.is_commit_enabled.return_value = True
        mock_get_obj.return_value = Mock(netbox=Mock())
        mock_get_handler.return_value = None

        response = commit_configuration(_make_post_request())

        assert response.status_code == 503
        assert b"Could not obtain" in response.content


def _make_post_request(interfaceid=1):
    factory = RequestFactory()
    return factory.post("/portadmin/commit", {"interfaceid": str(interfaceid)})

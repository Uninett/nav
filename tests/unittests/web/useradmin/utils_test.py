from unittest.mock import MagicMock, patch

from nav.web.useradmin.utils import (
    annotate_accounts_with_2fa_status,
    is_2fa_globally_enabled,
)


class TestIs2faGloballyEnabled:
    def test_given_non_empty_mfa_supported_types_then_2fa_should_be_enabled(self):
        with patch('nav.web.useradmin.utils.settings') as mock_settings:
            mock_settings.MFA_SUPPORTED_TYPES = ['totp']
            assert is_2fa_globally_enabled() is True

    def test_given_no_supported_mfa_types_then_2fa_should_be_disabled(self):
        with patch('nav.web.useradmin.utils.settings') as mock_settings:
            mock_settings.MFA_SUPPORTED_TYPES = []
            assert is_2fa_globally_enabled() is False

    def test_given_empty_supported_mfa_types_then_2fa_should_be_disabled(self):
        with patch('nav.web.useradmin.utils.settings') as mock_settings:
            del mock_settings.MFA_SUPPORTED_TYPES
            assert is_2fa_globally_enabled() is False


class TestAnnotateAccountsWith2faStatus:
    def test_given_2fa_globally_disabled_then_queryset_should_not_be_annotated(self):
        with patch(
            'nav.web.useradmin.utils.is_2fa_globally_enabled', return_value=False
        ):
            queryset = MagicMock()
            result = annotate_accounts_with_2fa_status(queryset)
            assert result is queryset
            queryset.annotate.assert_not_called()

    def test_given_2fa_globally_enabled_then_queryset_should_be_annotated(self):
        with patch(
            'nav.web.useradmin.utils.is_2fa_globally_enabled', return_value=True
        ):
            queryset = MagicMock()
            result = annotate_accounts_with_2fa_status(queryset)
            queryset.annotate.assert_called_once()
            assert result is queryset.annotate.return_value

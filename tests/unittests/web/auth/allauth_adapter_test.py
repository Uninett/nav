"""Tests for the NAV allauth social account adapter."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.test import override_settings

from nav.web.auth.allauth.adapter import NAVAccountAdapter, NAVSocialAccountAdapter


class TestSocialIsOpenForSignup:
    def test_when_setting_unset_then_signup_should_be_closed(self):
        adapter = NAVSocialAccountAdapter()
        assert adapter.is_open_for_signup(Mock(), _sociallogin()) is False

    @override_settings(NAV_ALLOW_SIGNUPS=True)
    def test_when_setting_enabled_then_signup_should_be_open(self):
        adapter = NAVSocialAccountAdapter()
        assert adapter.is_open_for_signup(Mock(), _sociallogin()) is True

    @override_settings(NAV_ALLOW_SIGNUPS=False)
    def test_when_setting_disabled_then_signup_should_be_closed(self):
        adapter = NAVSocialAccountAdapter()
        assert adapter.is_open_for_signup(Mock(), _sociallogin()) is False


class TestPopulateUser:
    def test_when_user_has_no_login_then_it_should_set_login_from_uid(self):
        adapter = NAVSocialAccountAdapter()
        sociallogin = _sociallogin(uid="alice")
        with patch.object(
            DefaultSocialAccountAdapter,
            "populate_user",
            return_value=SimpleNamespace(),
        ):
            user = adapter.populate_user(Mock(), sociallogin, {})
        assert user.login == "alice"

    def test_when_user_already_has_login_then_it_should_keep_it(self):
        adapter = NAVSocialAccountAdapter()
        sociallogin = _sociallogin(uid="alice")
        with patch.object(
            DefaultSocialAccountAdapter,
            "populate_user",
            return_value=SimpleNamespace(login="bob"),
        ):
            user = adapter.populate_user(Mock(), sociallogin, {})
        assert user.login == "bob"


class TestPopulateUsername:
    def test_when_username_present_then_it_should_keep_it_without_generating(self):
        # NAV's login field has no max_length, so allauth's
        # generate_unique_username would crash if it were invoked; the override
        # must keep the already-populated username untouched instead.
        adapter = NAVAccountAdapter()
        user = SimpleNamespace(login="alice")
        adapter.populate_username(Mock(), user)
        assert user.login == "alice"


def _sociallogin(uid="alice"):
    sociallogin = Mock()
    sociallogin.account.uid = uid
    return sociallogin

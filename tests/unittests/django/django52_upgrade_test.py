"""Tests to verify Django 5.2 upgrade requirements are met."""

import django


class TestDjangoVersion:
    def test_when_checking_version_then_it_should_be_52_or_higher(self):
        assert django.VERSION >= (5, 2)


class TestLoginNotRequired:
    def test_when_importing_then_it_should_exist_natively(self):
        from django.contrib.auth.decorators import login_not_required

        assert callable(login_not_required)


class TestLocalization:
    def test_when_checking_settings_then_use_l10n_should_not_be_explicitly_set(self):
        import nav.django.settings as nav_settings

        assert not hasattr(nav_settings, 'USE_L10N')

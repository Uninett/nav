"""Tests for the PortAdmin configuration file options"""

import pytest

from nav.portadmin.config import PortAdminConfig


class TestRequirePrivilegesOption:
    def test_when_option_is_absent_it_should_default_to_off(self):
        """Upgrading without touching portadmin.conf must not restrict anyone"""
        config = PortAdminConfig()
        config.remove_option("authorization", "require_privileges")

        assert not config.is_privilege_authorization_enabled()

    @pytest.mark.parametrize(
        "value,expected",
        [("on", True), ("true", True), ("1", True), ("off", False), ("no", False)],
    )
    def test_when_option_is_set_it_should_be_honoured(self, value, expected):
        config = PortAdminConfig()
        config.set("authorization", "require_privileges", value)

        assert config.is_privilege_authorization_enabled() == expected

# -*- coding: utf-8 -*-
from nav.django.settings import NAV_VERSION, OS_VERSION


def test_valid_nav_version():
    """
    Test that NAV_VERSION is set to something containing a '.',
    which is assumed to be a valid version.
    """
    assert "." in NAV_VERSION


def test_valid_os_version():
    """Test that OS_VERSION contains a supported OS"""
    os_list = ["windows", "macos", "linux", "freebsd"]
    assert any(os in OS_VERSION.lower() for os in os_list)

# -*- coding: utf-8 -*-
from nav.django.utils import get_verbose_name, reverse_with_query, get_os_version
from unittest.mock import patch


def test_verbose_name():
    """Test that get_verbose_name() works on all supported Django versions"""
    from nav.models.manage import Netbox

    name = get_verbose_name(Netbox, 'type__name')
    assert name == 'type name'


def test_reverse_with_query_should_work_with_unicode():
    """Reveals issues with PY2/PY3 co-compatibility"""
    assert reverse_with_query("maintenance-new", roomid="bø-123")


def test_get_os_version_examples(subtests):
    with subtests.test("Linux"):
        with (
            patch("platform.system", return_value="Linux"),
            patch("distro.name", return_value="Ubuntu 22.04"),
        ):
            assert get_os_version() == "Linux Ubuntu 22.04"

    with subtests.test("macOS"):
        with (
            patch("platform.system", return_value="Darwin"),
            patch("platform.mac_ver", return_value=("13.2", ("", "", ""), "")),
        ):
            assert get_os_version() == "macOS 13.2"

    with subtests.test("Windows"):
        with (
            patch("platform.system", return_value="Windows"),
            patch("platform.release", return_value="10"),
            patch("platform.version", return_value="10.0.19042"),
        ):
            assert get_os_version() == "Windows 10 (10.0.19042)"

    with subtests.test("FreeBSD"):
        with (
            patch("platform.system", return_value="FreeBSD"),
            patch("platform.release", return_value="13.0"),
            patch("platform.version", return_value="GENERIC"),
        ):
            assert get_os_version() == "FreeBSD 13.0 (GENERIC)"

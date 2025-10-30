# -*- coding: utf-8 -*-
import logging
from unittest import TestCase

from django.test import RequestFactory

from nav.django.utils import (
    get_os_version,
    get_verbose_name,
    pformat_request,
    reverse_with_query,
)

from unittest.mock import patch

_logger = logging.getLogger(__name__)


def test_verbose_name():
    """Test that get_verbose_name() works on all supported Django versions"""
    from nav.models.manage import Netbox

    name = get_verbose_name(Netbox, 'type__name')
    assert name == 'type name'


def test_reverse_with_query_should_work_with_unicode():
    """Reveals issues with PY2/PY3 co-compatibility"""
    assert reverse_with_query("maintenance-new", roomid="bø-123")


class TestPFormatRequest(TestCase):
    def test_should_log_more_lines_than_there_are_attributes_in_request(
        self,
    ):
        r = RequestFactory()
        request = r.get('/')
        num_request_attributes = len(vars(request))
        with self.assertLogs(level=logging.DEBUG) as logs:
            pformat_request(request, _logger.debug)
            self.assertTrue(len(logs.records) > num_request_attributes)

    def test_should_log_nothing_for_nonexistent_attribute(self):
        r = RequestFactory()
        request = r.get('/')
        with self.assertRaises(AssertionError):
            with self.assertLogs():
                pformat_request(request, _logger.debug, 'doesnotexist-nanana')

    def test_should_log_one_line_for_content_type(self):
        r = RequestFactory()
        request = r.get('/')
        with self.assertLogs(level=logging.DEBUG) as logs:
            pformat_request(request, _logger.debug, 'content_type')
            self.assertEqual(len(logs.records), 1)


class TestGetValidOSVersion(TestCase):
    def test_given_linux_os_returns_pretty_print_version(self):
        with (
            patch("platform.system", return_value="Linux"),
            patch("distro.name", return_value="Ubuntu 22.04"),
        ):
            assert get_os_version() == "Linux Ubuntu 22.04"

    def test_given_mac_os_returns_pretty_print_version(self):
        with (
            patch("platform.system", return_value="Darwin"),
            patch("platform.mac_ver", return_value=("13.2", ("", "", ""), "")),
        ):
            assert get_os_version() == "macOS 13.2"

    def test_given_windows_os_returns_pretty_print_version(self):
        with (
            patch("platform.system", return_value="Windows"),
            patch("platform.release", return_value="10"),
            patch("platform.version", return_value="10.0.19042"),
        ):
            assert get_os_version() == "Windows 10 (10.0.19042)"

    def test_given_freebsd_os_returns_pretty_print_version(self):
        with (
            patch("platform.system", return_value="FreeBSD"),
            patch("platform.release", return_value="13.0"),
            patch("platform.version", return_value="GENERIC"),
        ):
            assert get_os_version() == "FreeBSD 13.0 (GENERIC)"

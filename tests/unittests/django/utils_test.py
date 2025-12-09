# -*- coding: utf-8 -*-
import logging
from unittest import TestCase

from django.test import RequestFactory

from nav.django.utils import get_verbose_name, pformat_request, reverse_with_query

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

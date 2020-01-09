"""Tests"""
from unittest import TestCase
from nav.web.report.views import find_page_range


class PageRangeTest(TestCase):
    """Tests for find_page_range"""

    def setUp(self):
        self.page_num = 1
        self.pages = range(1, 28)
        self.result = find_page_range(self.page_num, self.pages, 5)

    def test_returns_list(self):
        self.assertTrue(isinstance(self.result, list))

    def test_current_page_is_in_range(self):
        self.assertTrue(self.page_num in self.result)

    def test_returns_num_visible_pages(self):
        self.assertEqual(len(self.result), 5)

    def test_except_when_total_is_less(self):
        result = find_page_range(1, range(1, 3), 3)
        self.assertEqual(len(result), 2)

    def test_start_at_first_returns_correct_number(self):
        result = find_page_range(1, range(1, 11), 5)
        self.assertEqual(len(result), 5)

    def test_start_at_last_returns_correct_number(self):
        result = find_page_range(11, range(1, 11), 5)
        self.assertEqual(len(result), 5)

    def test_page_should_be_center(self):
        result = find_page_range(3, range(1, 11), 5)
        self.assertEqual(result[2], 3)

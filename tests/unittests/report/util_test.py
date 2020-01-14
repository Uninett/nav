"""Tests for report view utility functions"""
from nav.web.report.views import find_page_range


class TestPageRangeForPage1(object):
    """Tests for find_page_range"""

    @classmethod
    def setup_class(cls):
        cls.page_num = 1
        cls.pages = range(1, 28)
        cls.result = find_page_range(cls.page_num, cls.pages, 5)

    def test_current_page_is_in_range(self):
        assert self.page_num in self.result

    def test_returns_num_visible_pages(self):
        assert len(self.result) == 5


class TestGenericPageRangeCalls(object):
    def test_except_when_total_is_less(self):
        result = find_page_range(1, range(1, 3), 3)
        assert len(result) == 2

    def test_start_at_first_returns_correct_number(self):
        result = find_page_range(1, range(1, 11), 5)
        assert len(result) == 5

    def test_start_at_last_returns_correct_number(self):
        result = find_page_range(11, range(1, 11), 5)
        assert len(result) == 5

    def test_page_should_be_center(self):
        result = find_page_range(3, range(1, 11), 5)
        assert result[2] == 3

    def test_page_in_middle_of_long_range_should_not_crash(self):
        result = find_page_range(5, range(1, 11), 5)
        assert result[2] == 5

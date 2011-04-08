from unittest import TestCase

from nav.django.validators import *

class ValidPointStringTest(TestCase):
    def test_valid_point_string(self):
        point_string = "(2.3,4.5)"
        res = is_valid_point_string(point_string)
        self.assertTrue(res)

    def test_parens_and_sapce(self):
        point_string = "(9.888, 3.2222)"
        res = is_valid_point_string(point_string)
        self.assertTrue(res)

    def test_no_parens(self):
        point_string = "5.5,8.7"
        res = is_valid_point_string(point_string)
        self.assertTrue(res)

    def test_no_parens_and_space(self):
        point_string = "77.22134124, 543.3342"
        res = is_valid_point_string(point_string)
        self.assertTrue(res)

    def test_no_comma(self):
        point_string = "(2.4)"
        res = is_valid_point_string(point_string)
        self.assertFalse(res)

    def test_chars(self):
        point_string = "foo, bar"
        res = is_valid_point_string(point_string)
        self.assertFalse(res)

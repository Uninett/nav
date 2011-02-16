from unittest import TestCase

from nav.django.validators import *

class ValidPointStringTest(TestCase):
    def test_valid_point_string(self):
        point_string = "(2.3,4.5)"
        res = is_valid_point_string(point_string)
        self.assertTrue(res)

    def test_missing_parens(self):
        point_string = "5.5,8.7"
        res = is_valid_point_string(point_string)
        self.assertFalse(res)

    def test_no_comma(self):
        point_string = "(2.4)"
        res = is_valid_point_string(point_string)
        self.assertFalse(res)

import unittest

from datetime import timedelta, datetime
from nav.django.templatetags.info import time_since, is_max_timestamp

class TemplateTagsTest(unittest.TestCase):

    def test_time_since(self):
        def timestamp_calc(*args, **kwargs):
            return datetime.now() - timedelta(*args, **kwargs)

        minute = 60
        hour = minute * 60

        self.assertEqual(
            time_since(None),
            "Never")
        self.assertEqual(
            time_since(timestamp_calc(seconds=(10 * minute + 10))),
            "10 mins")
        self.assertEqual(
            time_since(timestamp_calc(seconds=(1 * minute + 5))),
            "1 min")
        self.assertEqual(
            time_since(timestamp_calc(0)),
            "Now")
        self.assertEqual(
            time_since(datetime.max),
            "Now")


    def test_is_max_timestamp(self):
        self.assertTrue(is_max_timestamp(datetime.max))
        self.assertFalse(is_max_timestamp(datetime(3, 2, 1)))

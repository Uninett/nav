import unittest

from datetime import timedelta
from nav.django.templatetags.info import time_since

class TemplateTagsTest(unittest.TestCase):

    def test_time_since(self):
        minute = 60
        hour = minute * 60

        self.assertEqual(time_since(None), "")

        self.assertEqual(time_since(timedelta(366)), "More than a year ago")
        self.assertEqual(time_since(timedelta(3)), "3 days ago")

        self.assertEqual(time_since(timedelta(seconds=(2 * hour) + (31 * minute))), "3 hours ago")
        self.assertEqual(time_since(timedelta(seconds=(2 * hour) + 10)), "2 hours ago")

        self.assertEqual(time_since(timedelta(seconds=(10 * minute + 10))), "10 minutes ago")
        self.assertEqual(time_since(timedelta(seconds=(10 * minute + 31))), "11 minutes ago")

        self.assertEqual(time_since(timedelta(seconds=10)), "10 seconds ago")
        self.assertEqual(time_since(timedelta(0)), "Active now")

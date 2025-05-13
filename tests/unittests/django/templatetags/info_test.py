import unittest

from datetime import timedelta, datetime

from nav.django.templatetags.info import (
    time_since,
    is_max_timestamp,
    get_attr,
    find_attr,
)


class DummyObject(object):
    def __init__(self):
        self.test = "A String"
        self.dummyobject = AnotherDummyObject()


class AnotherDummyObject(object):
    def __init__(self):
        self.test = "A String"


class TemplateTagsTest(unittest.TestCase):
    def setUp(self):
        self.dummy = DummyObject()

    def test_time_since(self):
        def timestamp_calc(*args, **kwargs):
            return datetime.now() - timedelta(*args, **kwargs)

        minute = 60

        self.assertEqual(time_since(None), "Never")
        self.assertEqual(
            time_since(timestamp_calc(seconds=(10 * minute + 10))), "10\xa0mins"
        )
        self.assertEqual(
            time_since(timestamp_calc(seconds=(1 * minute + 5))), "1\xa0min"
        )
        self.assertEqual(time_since(timestamp_calc(0)), "Now")
        self.assertEqual(time_since(datetime.max), "Now")

    def test_is_max_timestamp(self):
        self.assertTrue(is_max_timestamp(datetime.max))
        self.assertFalse(is_max_timestamp(datetime(3, 2, 1)))

    def test_get_attr_basic_lookup(self):
        """Test template filter for getting attributes from objects"""

        self.assertTrue(isinstance(get_attr(self.dummy, 'test'), str))
        self.assertTrue(
            isinstance(get_attr(self.dummy, 'dummyobject'), AnotherDummyObject)
        )
        self.assertEqual(get_attr(self.dummy, 'tes'), "")

    def test_get_attr_chained_lookup(self):
        """Test template filter for getting attributes from objects"""

        self.assertTrue(isinstance(get_attr(self.dummy, 'dummyobject.test'), str))

    def test_get_attr_chained_lookup_error(self):
        """Test template filter for getting attributes from objects"""

        self.assertEqual(get_attr(self.dummy, 'dummyobject.tes'), "")

    def test_find_attr_basic_lookup(self):
        """Test helper function for getting attributes from objects"""

        self.assertTrue(
            isinstance(find_attr(self.dummy, ['dummyobject']), AnotherDummyObject)
        )

    def test_find_attr_chained_lookup(self):
        """Test helper function for getting attributes from objects"""

        self.assertTrue(isinstance(find_attr(self.dummy, ['dummyobject', 'test']), str))

    def test_find_attr_error_lookup(self):
        """Test helper function for getting attributes from objects"""

        self.assertEqual(find_attr(self.dummy, ['dummyobjec']), "")

    def test_find_attr_chained_error_lookup(self):
        """Test helper function for getting attributes from objects"""

        self.assertEqual(find_attr(self.dummy, ['dummyobject', 'test', 'nothere']), "")

    def test_find_attr_middle_chained_error_lookup(self):
        """Test helper function for getting attributes from objects"""

        self.assertEqual(find_attr(self.dummy, ['dummyobjec', 'test', 'nothere']), "")

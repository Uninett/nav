"""Testcase for Arnold's memoisation class used for fetching info from files"""

import unittest
from mock import Mock, patch
from nav.arnold import Memo


@patch('os.path.getmtime')
class ArnoldMemoTest(unittest.TestCase):
    """Run the tests"""

    def setUp(self):
        self.fun = Mock()
        self.decorated_fun = Memo(self.fun)

    def test_basic_store(self, getmtime):
        """Test that function is actually run"""
        getmtime.return_value = 100
        self.decorated_fun(1)
        self.assertTrue(self.fun.called)

    def test_cache(self, getmtime):
        """Test that cache is used when calling function"""
        getmtime.return_value = 100
        self.decorated_fun(1)
        self.decorated_fun(1)
        self.assertEqual(self.fun.call_count, 1)

    def test_invalidate_cache(self, getmtime):
        """Test that getmtime affects storage"""
        getmtime.return_value = 100
        self.decorated_fun(1)
        getmtime.return_value = 200
        self.decorated_fun(1)
        self.assertEqual(self.fun.call_count, 2)

    def test_another_store(self, getmtime):
        """Test storage of two different values"""
        getmtime.return_value = 100
        self.decorated_fun(1)
        self.decorated_fun(2)
        self.assertEqual(self.fun.call_count, 2)

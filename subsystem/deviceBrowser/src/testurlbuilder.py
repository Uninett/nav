#!/usr/lib/apache/python/bin/python
import unittest

import urlbuilder

from nav import tables

class TestUrlBuilder(unittest.TestCase):
    def setUp(self):
        # set up stuff
		self.netbox = tables.getNetbox("ludvig.ntnu.no")
        

if __name__ == '__main__':
    unittest.main()
  

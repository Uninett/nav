#!/usr/lib/apache/python/bin/python
import unittest

import urlbuilder

from nav import tables

class TestUrlBuilder(unittest.TestCase):
    def setUp(self):
        # set up stuff
		self.device = tables.getNetbox("ludvig.ntnu.no")
        
    def testDeviceUrl(self):		
        url = urlbuilder.device(self.device)
		self.assertEqual(url, "http://isbre.itea.ntnu.no/stain/ludvig.ntnu.no/")	

if __name__ == '__main__':
    unittest.main()
  

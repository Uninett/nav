#!/usr/lib/apache/python/bin/python
import unittest

from test import Dummy

class DummyTest(unittest.TestCase):
    def testDummy(self):
        # Should allow ANYTHING
        dummy = Dummy()
        a = dummy.knott
        dummy.blapp()
        dummy.fjosk(15)
        dummy.knall(15,"skdjskdj!", None)
        dummy[24].blapp
        dummy[dummy.torsk] = 2398
	dummy.knall.blapp
	blapp = dummy.knott()
        blapp()

if __name__ == '__main__':
    unittest.main()
  

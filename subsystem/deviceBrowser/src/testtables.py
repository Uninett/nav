#!/usr/lib/apache/python/bin/python
import unittest
from nav.db import manage

class TestTables(unittest.TestCase):
    def setUp(self):
        # set up stuff
        pass
    def testValidSysname(self):
        hostname = "ludvig.ntnu.no"
        assert manage.getNetbox(hostname)
    def testInValidSysname(self):
        hostname = "du.er.jævlig.teit"
        assert not manage.getNetbox(hostname)
    def testValidIp(self):
        ip = "129.241.190.190"
        assert manage.getNetbox(ip)
    def testInValidIp(self):
        ip = "0.0.0.1"
        assert not manage.getNetbox(ip)

if __name__ == '__main__':
    unittest.main()
  

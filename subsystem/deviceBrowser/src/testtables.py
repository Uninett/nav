#!/usr/lib/apache/python/bin/python
import unittest
from nav import tables

class TestTables(unittest.TestCase):
    def setUp(self):
        # set up stuff
        pass
    def testValidSysname(self):
        hostname = "ludvig.ntnu.no"
        assert tables.getNetbox(hostname)
    def testInValidSysname(self):
        hostname = "du.er.jævlig.teit"
        assert not tables.getNetbox(hostname)
    def testValidIp(self):
        ip = "129.241.190.190"
        assert tables.getNetbox(ip)
    def testInValidIp(self):
        ip = "0.0.0.1"
        assert not tables.getNetbox(ip)

if __name__ == '__main__':
    unittest.main()
  

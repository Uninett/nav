#!/usr/lib/apache/python/bin/python
import unittest
from test import Dummy
import netbox
import mod_python

class TestNetbox(unittest.TestCase):
    def setUp(self):
        # set up stuff
        self.request = {}
        self.req = Dummy()
    def testValidNetbox(self):
        self.request['hostname']='ludvig.ntnu.no'
        response = netbox.process(self.request)
        assert response
    def testNetboxNotFound(self):
        self.request['hostname']='jalla.hostname'
        self.assertRaises(mod_python.apache.SERVER_RETURN, netbox.process, self.request)
    def testNoNetbox1(self):
        self.request['hostname']=''
        response = netbox.process(self.request)
        assert response
    def testNoNetbox2(self):
        response = netbox.process(self.request)
        assert response


if __name__ == '__main__':
    unittest.main()
  

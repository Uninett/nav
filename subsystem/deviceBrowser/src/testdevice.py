#!/usr/lib/apache/python/bin/python
import unittest
from test import Dummy
import device
import mod_python

class TestDevice(unittest.TestCase):
    def setUp(self):
        # set up stuff
        self.request = {}
        self.req = Dummy()
    def testValidDevice(self):
        self.request['hostname']='ludvig.ntnu.no'
        response = device.process(self.request)
        assert response
    def testDeviceNotFound(self):
        self.request['hostname']='jalla.hostname'
        self.assertRaises(mod_python.apache.SERVER_RETURN, device.process, self.request)
    def testNoDevice1(self):
        self.request['hostname']=''
        response = device.process(self.request)
        assert response
    def testNoDevice2(self):
        response = device.process(self.request)
        assert response


if __name__ == '__main__':
    unittest.main()
  

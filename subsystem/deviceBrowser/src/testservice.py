#!/usr/lib/apache/python/bin/python
import unittest
from test import Dummy
import service
import mod_python
from nav.db import manage 

class TestService(unittest.TestCase):
    def setUp(self):
        # set up stuff
        self.request = {}
        self.request['args'] = ['']
        self.request['query'] = ''
        self.req = Dummy()
    def testValidDeviceService(self):
        self.request['hostname']='ludvig.ntnu.no'
        self.request['service']='dns'
        response = service.process(self.request)
        assert response
    def testOnlyService1(self):
        self.request['hostname']=''
        self.request['service']='dns'
        response = service.process(self.request)
        assert response
    def testOnlyService2(self):
        self.request['service']='dns'
        response = service.process(self.request)
        assert response
    def testServiceIndex(self):
        response = service.process(self.request)
        assert response
    def testGetServices(self):
        netbox = manage.getNetbox('ludvig.ntnu.no')
        services = service.getServices(netbox)
        self.assert_(services)

if __name__ == '__main__':
    unittest.main()
  

#!/usr/lib/apache/python/bin/python
import unittest

from test import Dummy
from nav.errors import *

import mod_python
import dispatcher


class TestDispatcher(unittest.TestCase):
    def setUp(self):
        # we don't need anything in the request object now
        self.req = Dummy()
        self.req.uri = "/browse/ludvig.ntnu.no:dns/stats"
    def testHandlerDevice(self):
        response = dispatcher.handler(self.req)
        assert response
    def testHandlerNotFound(self):    
        self.req.uri = "/browse/notfound/error/"
        response = dispatcher.handler(self.req)
        self.assertEqual(response, mod_python.apache.HTTP_NOT_FOUND)
    def testUrlSplitDevice(self):
        request = dispatcher.classifyUri(self.req.uri)
        self.assertEqual(request['hostname'], 'ludvig.ntnu.no')
        self.assertEqual(request['service'], 'dns')
    def testUrlSplitIndexSlash(self):
        uri = "/browse/"
        request = dispatcher.classifyUri(uri)
        self.assertEqual(request, {})
    def testUrlSplitIndexFilename(self):
        uri = "/browse/dispatcher.py"
        request = dispatcher.classifyUri(uri)
        self.assertEqual(request, {})
    def testUrlSplitError(self):
        uri = "/error/not/found"
        self.assertRaises(BasepathError, dispatcher.classifyUri, uri)
    
if __name__ == '__main__':
    unittest.main()
  

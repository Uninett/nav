#!/usr/lib/apache/python/bin/python
import unittest
import os
import sys

from nav import config

class ConfigOpen(unittest.TestCase):
    def setUp(self):
        # set up stuff
        pass
    def testReadFile(self):
        configfile = config.readConfig('devbrowser.conf')

class ConfigPaths(ConfigOpen):
    def setUp(self):
        ConfigOpen.setUp(self)
        self.config = config.readConfig('devbrowser.conf')
    def testBasePath(self):
        basepath = self.config['basepath']
        assert len(basepath) > 0

if __name__ == '__main__':
    unittest.main()
  

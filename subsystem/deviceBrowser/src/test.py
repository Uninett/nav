#!/usr/lib/apache/python/bin/python
import unittest,glob,os,sys

import mod_python

class Dummy(object):
    def __getitem__(self, name):
        return self()
    def __getattr__(self, name):
        if name.count("__") == 2:
            return object.__getattr__(self, name)
        return self()
    def __setitem__(self, name, value):
        pass
    def __call__(self, *args, **kwargs):
        return Dummy()

def emulateApache():
    # mod_oython.apache won'd import outside mod_python-environment
    mod_python.apache = Dummy()
    mod_python.apache.OK = Dummy()
    mod_python.apache.HTTP_NOT_FOUND = Dummy()

    class SomeException(Exception): pass
    mod_python.apache.SERVER_RETURN = SomeException

if __name__ == '__main__':
    emulateApache()
    
    # Set current directory
    bindir = os.path.dirname(sys.argv[0])
    bindir = os.path.abspath(bindir)
    libdir = os.path.join(bindir, 'lib')
    os.chdir(bindir)
    sys.path.insert(0, libdir)
    sys.path.insert(0, bindir)

    # Fetch all test modules
    tests = glob.glob("test[a-z]*py")
    tests = [test.replace(".py", "") for test in tests]

    # Combine into a large testcase
    tests = unittest.defaultTestLoader.loadTestsFromNames(tests)

    # And run it! =)
    runner = unittest.TextTestRunner()
    runner.run(tests)


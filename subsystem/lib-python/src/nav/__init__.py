"""
$Id$

This file is part of the NAV project.

Provides a common root package for the NAV python library.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
import time

class CachedObject:
    """
    A simple class to wrap objects for 'caching'.  It contains the
    object reference and the time the object was cached.
    """
    def __init__(self, object=None, loadTime=None):
        if not loadTime:
            loadTime = time.time()

        self.loadTime = loadTime
        self.object = object

    def age(self):
        """
        Return the age of this object
        """
        return time.time() - self.loadTime

    def __repr__(self):
        return "<%s cached at %s>" % (repr(self.object),
                                      time.asctime(time.localtime(self.loadTime)))
    
    def __str__(self):
        return self.object.__str__()


# We import some sub-modules because of bugs in mod_python
import db
import auth
try:
    # This actually belongs in another subsystem
    import web
except:
    pass


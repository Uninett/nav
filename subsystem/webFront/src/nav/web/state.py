####################
#
# $Id: x1$
# This file is part of the NAV project.
# State handling for NAV web requests.
#
# Copyright (c) 2003 by NTNU, ITEA nettgruppen
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#          Stian Søiland <stian@soiland.no>
#
####################
"""
State handling for NAV web requests.

This module contains fixup- and cleanuphandlers for use with NAV.
They maintain state through use of cookies and a Session object that
is attached to the request object.
"""
import time
import random
import md5
import cPickle
import os
from os import path
from mod_python import apache
import sys

cookieName = 'nav_sessid'
tempDir = '/tmp'
serialPrefix = '%s_' % cookieName


def getUniqueString(entropy=''):
    """Generates a unique id string for use in session identification.
    You can provide additional strings to be used as entropy in the
    'entropy' parameter.  It's not really magic, it just picks the
    current system time and a pseudo random number and returns the md5
    digest of these put together."""
    hash = md5.new()
    hash.update(str(time.time()))
    hash.update(str(random.random()))
    hash.update(str(os.getpid()))
    if (entropy):
        hash.update(entropy)
    return hash.hexdigest()


def fixuphandler(req):
    """
    Set up a new or load an existing session object for this request.
    """
    c = None
    req.session = None

    if req.headers_in.has_key('Cookie'):
        import Cookie
        c = Cookie.SimpleCookie()
        c.load(str(req.headers_in['Cookie']))
        if c.has_key(cookieName):
            req.session = Session(c[cookieName].value)

    if req.session is None:
        req.session = Session()
    req.headers_out['Set-Cookie'] = '%s=%s;' % (cookieName, req.session.id)

    return apache.OK

class Session(dict):
    def __init__(self, id=None):
        if id:
            self.id = id
        else:
            self.id = getUniqueString()
            dict.__init__(self)
            self.created = time.time()
        self._changed = False

    def __new__(cls, sessionId=None):
        if not sessionId:
            return dict.__new__(cls)          
        
        filename = path.join(tempDir, '%s%s' % (serialPrefix, sessionId))
        try:
            file = open(filename, 'r')
        except IOError:
            return dict.__new__(cls) # Ok, instanciate a new
    
        unpickler = cPickle.Unpickler(file)
        session = unpickler.load()
        session._changed = False
        return session

    def save(self):
        """Make the Session object persistent"""
        filename = path.join(tempDir, '%s%s' % (serialPrefix, self.id))
        file = open(filename, 'w')

        pickler = cPickle.Pickler(file, False)
        pickler.dump(self)
        file.close()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._changed = True

    def __del__(self):
        # Persist to disk only if we changed during our existence
        if self._changed:
            self.save()
        

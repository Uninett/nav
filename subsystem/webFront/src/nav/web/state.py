"""
$Id$

This file is part of the NAV project.

This module performs state handling for NAV web requests.  It defines
a Session dictionary class with built-in persistence, and contains
functions to associate session objects with request objects.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
         Stian Søiland <stian@soiland.no>
"""
import time
import random
import md5
import cPickle
import os
from os import path
import sys

sessionCookieName = 'nav_sessid'
tempDir = '/tmp'
serialPrefix = '%s_' % sessionCookieName


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


def setupSession(req):
    """
    Sets up a session dictionary for this request.  If the request
    contains a session Cookie, we attempt to load a stored session, if
    not we create a new one and post a new session cookie to the
    client.
    """
    req.session = None

    cookieValue = getSessionCookie(req)
    if (cookieValue):
        req.session = Session(cookieValue)

    if req.session is None:
        req.session = Session()
    setSessionCookie(req, req.session.id)


def setSessionCookie(req, value):
    """
    Sets the session cookie = value in the given request object
    """
    req.headers_out['Set-Cookie'] = '%s=%s;' % (sessionCookieName, value)
    
def getSessionCookie(req):
    """
    Returns the value of the session cookie in the request object - if it exists.
    """
    if req.headers_in.has_key('Cookie'):
        import Cookie
        cookie = Cookie.SimpleCookie()
        cookie.load(str(req.headers_in['Cookie']))
        if cookie.has_key(sessionCookieName):
            return cookie[sessionCookieName].value
    # if all else fails:
    return None

def deleteSessionCookie(req):
    """
    Deletes the session cookie from the client by blanking it
    """
    setSessionCookie(req, '')


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
            # If the session does not exist, create a new one using the given id.
            return dict.__new__(cls, sessionId)
    
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
        self._changed = False

    def expire(self):
        """
        Expires this session and deletes persistent data
        """
        filename = path.join(tempDir, '%s%s' % (serialPrefix, self.id))
        try:
            os.unlink(filename)
        except OSError:
            pass

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._changed = True

    def __del__(self):
        # Persist to disk only if we changed during our existence
        if self._changed:
            self.save()
        

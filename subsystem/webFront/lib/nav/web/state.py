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
import fcntl
import nav.errors

sessionCookieName = 'nav_sessid'
tempDir = '/tmp'
serialPrefix = '%s_' % sessionCookieName
maxAge = 3600 # Sessions time out after this amount of seconds
_timestamp = 0


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
    message = None
    global _timestamp
    
    # First, we periodically delete expired sessions.  The expiry
    # isn't necessarily accurate, but what the heck...
    timenow = int(time.time())
    if timenow > (_timestamp + 5*60):
        expireCount = cleanup()
        if (expireCount > 0):
            print >> sys.stderr, "NAV-DEBUG: Expired %d sessions" % expireCount
        _timestamp = timenow

    cookieValue = getSessionCookie(req)
    if (cookieValue):
        try:
            req.session = Session(cookieValue)
        except cPickle.UnpicklingError:
            # Some weird unpickling error took place, we'll silently
            # create a new session after this
            req.session = None
        except NoSuchSessionError, e:
            # The session didn't exist, it probably expired.  We make
            # sure to set a warning about this inside the new session
            # that is generated, and re-authentication is necessary,
            # the login page will display this warning message.
            message = "Your login session expired"

    if req.session is None:
        req.session = Session()
        if message is not None:
            req.session['message'] = message
            req.session.save()
        setSessionCookie(req, req.session.id)


def setSessionCookie(req, value):
    """
    Sets the session cookie = value in the given request object
    """
    cookieString = '%s=%s; path=/' % (sessionCookieName, value)
    req.headers_out['Set-Cookie'] = cookieString
    
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

def _sessionFilter(file):
    """Just a filter for filter() to filter out session files"""
    prefixLength = len(serialPrefix)
    return file[:prefixLength] == serialPrefix

def _oldFilter(file):
    """Filters expired (too old) session files"""
    name = path.join(tempDir, file)
    try:
        mtime = os.stat(name)[8]
        nowtime = int(time.time())
        return (nowtime-mtime > maxAge)
    except:
        return False

def getExpired():
    """Returns a list of expired session files"""
    sessions = filter(_sessionFilter, os.listdir(tempDir))
    old = filter(_oldFilter, sessions)
    return map(lambda f: path.join(tempDir, f), old)

def cleanup():
    """Deletes expired session files"""
    old = getExpired()
    counter = 0
    for file in old:
        try:
            # Unlink the expired session file
            os.unlink(file)
            counter += 1
        except:
            # We failed; maybe another process removed the file before
            # us.  Oh well, we don't care.
            pass
    return counter

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
            # If the session does  not exist, it has probably expired,
            # and we raise an error
            raise NoSuchSessionError, sessionId

        fcntl.lockf(file, fcntl.LOCK_SH) # Shared read lock
        unpickler = cPickle.Unpickler(file)
        try:
            session = unpickler.load()
        except Exception, e:
            # Make sure we unlock before reraising the exception
            fcntl.lockf(file, fcntl.LOCK_UN)
            raise e
        else:
            fcntl.lockf(file, fcntl.LOCK_UN) # Release lock
        
        session._changed = False
        return session

    def save(self):
        """Make the Session object persistent"""
        filename = path.join(tempDir, '%s%s' % (serialPrefix, self.id))
        os.umask(0077) # Make sure only owner has rights
        file = open(filename, 'w')

        fcntl.lockf(file, fcntl.LOCK_EX) # Exclusive write lock
        pickler = cPickle.Pickler(file, True)
        pickler.dump(self)
        fcntl.lockf(file, fcntl.LOCK_UN) # Release lock
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

    def __delitem__(self, key):
        """Make sure we register as changed when an item is deleted"""
        dict.__delitem__(self, key)
        self._changed = True

    def __del__(self):
        # Persist to disk only if we changed during our existence
        if self._changed:
            self.save()
        
class StateError(nav.errors.GeneralException):
    "State error"

class NoSuchSessionError(StateError):
    "No such session error"

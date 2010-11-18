# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
This module performs state handling for NAV web requests.  It defines
a Session dictionary class with built-in persistence, and contains
functions to associate session objects with request objects.
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
import nav.web
import logging
import re
try:
    from mod_python import apache
except:
    pass

logger = logging.getLogger("nav.web.state")
sessionCookieName = 'nav_sessid'
tempDir = '/tmp'
serialPrefix = '%s_' % sessionCookieName
_timestamp = 0


def getUniqueString(entropy=''):
    """Generates a unique id string for use in session identification.
    You can provide additional strings to be used as entropy in the
    'entropy' parameter.  It's not really magic, it just picks the
    current system time and a pseudo random number and returns the md5
    digest of these put together."""
    # This function returns a 32 character md5 hash string.  The validate_sid
    # function will validate ids accordingly.  If you change this
    # implementation, you must also change the validate_sid implementation.
    hash = md5.new()
    hash.update(str(time.time()))
    hash.update(str(random.random()))
    hash.update(str(os.getpid()))
    if (entropy):
        hash.update(entropy)
    return hash.hexdigest()

session_valid_re = re.compile('[0-9a-f]{32}$')
def validate_sid(sid):
    """Verifies the validity of a session id.

    A valid session ID consists of exactly 32 characters, and must only
    contain the characters 0-9 and a-f.  Invalid session identifiers supplied
    by clients may result in directory traversal attacks (they might contain /
    and .. sequences).
    """    
    return session_valid_re.match(sid)

def setupSession(req):
    """
    Sets up a session dictionary for this request.  If the request
    contains a session Cookie, we attempt to load a stored session, if
    not we create a new one and post a new session cookie to the
    client.
    """
    from mod_python import apache
    req.session = None
    message = None
    global _timestamp
    
    # First, we periodically delete expired sessions.  The expiry
    # isn't necessarily accurate, but what the heck...
    timenow = int(time.time())
    if timenow > (_timestamp + 5*60):
        expireCount = cleanup()
        if (expireCount > 0):
            logger.info("Expired %d NAV sessions", expireCount)
        _timestamp = timenow

    cookieValue = getSessionCookie(req)
    if (cookieValue):
        try:
            req.session = Session(cookieValue)
        except cPickle.UnpicklingError:
            # Some weird unpickling error took place, we'll silently
            # create a new session after this
            logger.debug("Exception occurred while unpickling session id=%s",
                         cookieValue, exc_info=True)
            req.session = None
        except NoSuchSessionError, e:
            # The session didn't exist, it probably expired.  We make
            # sure to set a warning about this inside the new session
            # that is generated, and re-authentication is necessary,
            # the login page will display this warning message.
            logger.info("Unknown session ID %s", cookieValue)
            message = "Your previous login session expired"

    if req.session is None:
        req.session = Session()
        logger.debug("Created new session id=%s", req.session.id)
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
        return (nowtime-mtime > nav.web.webfrontConfig.getint('sessions', 'timeout'))
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

def sessionFilename(session):
    """ Return an appropriate filename for storing this session in
    a file.  Session can be either a session id or object."""
    if type(session) is str:
        sessid = session
    else:
        sessid = session.id

    if not validate_sid(sessid):
        logger.error("Invalid session ID: %s", sessid)
        raise apache.SERVER_RETURN, apache.HTTP_INTERNAL_SERVER_ERROR
        
    return path.join(tempDir, '%s%s' % (serialPrefix, sessid))

class Session(dict):
    def __init__(self, sessionid=None):
        if sessionid:
            self.id = sessionid
        else:
            entropy = str(id(self))
            self.id = getUniqueString(entropy)
        dict.__init__(self)
        self.created = time.time()
        self._changed = False

    def __new__(cls, sessionId=None):
        if not sessionId:
            return dict.__new__(cls)
        
        filename = sessionFilename(sessionId)
        # countdown variable, see other comments below
        attempts = 3
        while attempts > 0:
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
            except EOFError, e:
                # Another process has just created this session file,
                # but we managed to lock it before the other process
                # got a write lock, so the file is empty.  The
                # competing process may be in the queue waiting for a
                # write lock, and should receive it immediately after
                # we unlock.  Therefore, we unlock, and retry this
                # procedure three times before giving up completely
                # (in which case something is considerably wrong
                # anyway!)
                fcntl.lockf(file, fcntl.LOCK_UN)
                attempts -= 1
                if attempts <= 0:
                    raise e
            else:
                attempts = 0
                fcntl.lockf(file, fcntl.LOCK_UN) # Release lock

        session._changed = False
        return session

    def save(self):
        """Make the Session object persistent"""
        filename = sessionFilename(self)
        os.umask(0077) # Make sure only owner has rights
        if path.exists(filename):
            mode = 'r+'
        else:
            mode = 'w+'
        file = open(filename, mode)
        
        fcntl.lockf(file, fcntl.LOCK_EX) # Exclusive write lock
        file.truncate() # truncate file when lock is acquired
        pickler = cPickle.Pickler(file, True)
        pickler.dump(self)
        fcntl.lockf(file, fcntl.LOCK_UN) # Release lock
        self._changed = False
        file.close()

    def expire(self):
        """
        Expires this session and deletes persistent data
        """
        filename = path.join(tempDir, '%s%s' % (serialPrefix, self.id))
        try:
            os.unlink(filename)
        except OSError:
            pass

    def mtime(self):
        """ Return the mtime of the stored session file."""
        try:
            return path.getmtime(sessionFilename(self))
        except OSError, e:
            # If this was a new session, it hasn't been stored to disk
            # yet, so we just report the current time.
            return time.time()

    def touch(self):
        """ Update the mtime of the stored session file."""
        filename = sessionFilename(self)
        file = open(filename, 'r+')
        fcntl.lockf(file, fcntl.LOCK_EX)
        file.seek(0, 2) # Seek to end of file
        # Truncate the file here (nothing should exist
        # beyond this point anyway!)
        file.truncate()
        fcntl.lockf(file, fcntl.LOCK_UN)
        file.close()

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

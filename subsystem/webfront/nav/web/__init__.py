# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2006, 2007 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# $Id$
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#          Magnar Sveen <magnars@idi.ntnu.no>
#
"""
This module encompasses modules with web functionality for NAV.
"""
import sys
import traceback
import nav
import time
import ConfigParser
import os.path, nav.path
import base64
import cgi
import logging
import nav.logs

from nav.models.profiles import Account

logger = logging.getLogger("nav.web")
webfrontConfig = ConfigParser.ConfigParser()
webfrontConfig.read(os.path.join(nav.path.sysconfdir, 'webfront', 'webfront.conf'))

def headerparserhandler(req):
    """
    This is a header parser handler for Apache.  It will parse all
    requests to NAV and perform various tasks to exert a certain
    degree of control over the NAV web site.  It makes sure the
    session dictionary is associated with the request object, and
    performs authentication and authorization functions for each
    request.
    """
    import nav.web.auth
    import state
    from mod_python import apache

    # We automagically redirect users to the index page if they
    # request the root.
    if req.uri == '/':
        redirect(req, '/index/index')

    state.setupSession(req)
    nav.web.auth.authenticate(req)
    user = req.session['user']

    # Make sure the user's session file has its mtime updated every
    # once in a while, even though no new data is saved to the session
    # (this is so the session won't expire for no apparent reason)
    if (req.session.mtime()+30) < time.time():
        req.session.touch()

    # Make sure the main web template knows which user to produce
    # output for.
    from nav.web.templates.MainTemplate import MainTemplate
    MainTemplate.user = user

    # Fake a HTTP Authorization header, with username and an empty
    # password, for third-party and non-Python apps running om this
    # server.  This way NAV can authenticate for them
    authHeader = 'Authorization'
    if authHeader in req.headers_in:
        # Delete any existing Authorization headers
        logger.debug("Request already had an Authorization header, removing it")
        del req.headers_in[authHeader]
    if user['id'] > 0:
        # Only fake the header if we're not the public user
        basicCookie = base64.encodestring(user['login'] + ':').strip()
        req.headers_in.add(authHeader, 'Basic ' + basicCookie)

    return apache.OK

def cleanuphandler(req):
    from nav import db
    # Let's make sure we commit any open transactions at the end of each
    # request
    conns = [v.object for v in db._connectionCache.values()]
    for conn in conns:
        conn.commit()
    # Also make sure the session data is fully persisted
    try:
        req.session.save
    except:
        pass
    else:
        req.session.save()
    return 0

def redirect(req, url, temporary=False, seeOther=False):
    """
    Immediately redirects the request to the given url. If the
    seeOther parameter is set, 303 See Other response is sent, if the
    temporary parameter is set, the server issues a 307 Temporary
    Redirect. Otherwise a 301 Moved Permanently response is issued.
    """
    from mod_python import apache

    if seeOther:
        status = apache.HTTP_SEE_OTHER
    elif temporary:
        status = apache.HTTP_TEMPORARY_REDIRECT
    else:
        status = apache.HTTP_MOVED_PERMANENTLY
    
    logger.debug("Redirect to %s using status code %s", url, status)
    req.headers_out['Location'] = url
    req.status = status
    raise apache.SERVER_RETURN, status

def shouldShow(link, user):
    """
    Checks if a link should be shown on the webpage. If the link
    starts with 'http://' or 'https://' it is considered an external
    link and allowed. Internal links are checked using nav.auth.hasPrivilege.
    """
    startsWithHTTP = link.lower()[:7] == 'http://' or link.lower()[:8] == 'https://'
    #FIXME handle Account.DoesNotExist
    return startsWithHTTP or Account.objects.get(id=user['id']).has_perm('web_access', link)

def escape(s):
    """Replace special characters '&', '<' and '>' by SGML entities.
    Wraps cgi.escape, but allows False values of s to be converted to
    empty strings."""
    if s:
        return cgi.escape(str(s))
    else:
        return ''

def loginit():
    """Initialize a logging setup for the web interface"""
    global _loginited
    try:
        # Make sure we don't initialize logging setup several times (in case
        # of module reloads and such)
        if _loginited:
            return
    except:
        pass
    
    root = logging.getLogger('')

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s")
    logfile = os.path.join(nav.path.localstatedir, 'log', 'webfront.log')
    try:
        handler = logging.FileHandler(logfile)
    except IOError, e:
        # Most likely, we were denied access to the log file.
        # We silently ignore it and log nothing :-P
        pass
    else:
        handler.setFormatter(formatter)

        root.addHandler(handler)
        nav.logs.setLogLevels()
        _loginited = True

def exceptionhandler(handler):
    """Decorator for mod_python handler functions, to catch unhandled
    exceptions and display them in a "pretty" template ;-)
    """
    from mod_python import apache
    def handlerfunc(req, *args, **kwargs):
        try:
            result = handler(req, *args, **kwargs)
        except Exception, e:
            tracelines = traceback.format_exception(*sys.exc_info())
            # We don't want to see the exception handler itself in the
            # traceback data, remove it:
            del tracelines[1]

            if req.sent_bodyct > 0:
                # We've already sent body data to the client, so there is
                # no use in trying to output a full HTML template now.. 
                # Just print it as raw text enclosed in a <pre> element.
                req.write("<pre>\nUnhandled NAV Exception occurred:\n\n")
                req.write(escape("\n".join(tracelines)))
                req.write("\n</pre>\n")
            else:
                from nav.web.templates.ExceptionTemplate import ExceptionTemplate
                page = ExceptionTemplate()
                page.traceback = escape("\n".join(tracelines))
                page.path = [("Home", "/"), ("NAV Exception", False)]
                req.content_type = 'text/html'
                req.status = apache.HTTP_INTERNAL_SERVER_ERROR 
                req.write(page.respond())
            return apache.OK
        else:
            return result
    return handlerfunc

# Module initialization
try:
    from mod_python import apache
except:
    # Not running inside mod_python - do nothing
    pass
else:
    loginit()

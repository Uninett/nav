"""
$Id$

This file is part of the NAV project.
This module encompasses modules with web functionality for NAV.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
import state
import auth

def headerparserhandler(req):
    """
    This is a header parser handler for Apache.  It will parse all
    requests to NAV and perform various tasks to exert a certain
    degree of control over the NAV web site.  It makes sure the
    session dictionary is associated with the request object, and
    performs authentication and authorization functions for each
    request.
    """
    from mod_python import apache

    # We automagically redirect users to the index page if they
    # request the root.
    if req.uri == '/':
        redirect(req, '/index.py/index')

    state.setupSession(req)
    auth.authenticate(req)

    # Make sure the main web template knows which user to produce
    # output for.
    from nav.web.templates.MainTemplate import MainTemplate
    MainTemplate.user = req.session['user']

    return apache.OK


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
    
    req.headers_out['Location'] = url
    req.status = status
    raise apache.SERVER_RETURN, status

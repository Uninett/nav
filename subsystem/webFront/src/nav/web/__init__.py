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

    state.setupSession(req)
    auth.authenticate(req)

    return apache.OK

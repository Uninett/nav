"""
$Id$

This file is part of the NAV project.

This module represents the page index of the NAV web interface.  It
follows the mod_python.publisher paradigm.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>

"""
from mod_python import apache
import os
import nav


def index(req):
    if req.session.has_key('user'):
        name = req.session['user'].name
    else:
        name = req.session.id
    
    return """
    <a href="/index.py/toolbox">Toolbox is here, %s</a>
""" %  name

def toolbox(req):
    from nav.web.templates.ToolboxTemplate import ToolboxTemplate
    page = ToolboxTemplate()

    from nav.web import toolbox
    page.tools = toolbox.getToolList()

    return page

def login(req, login='', password='', origin=''):
    """
    Handles the login page
    """
    if login:
        # The user is attempting to log in, and we want to be sure
        # that any existing Account objects in this session are
        # deleted:
        if req.session.has_key('user'):
            del req.session['user']
            req.session.save()
        
        from nav import db
        conn = db.getConnection('navprofile', 'navprofile')
        from nav.db import navprofiles
        navprofiles.setCursorMethod(conn.cursor)
        from nav.db.navprofiles import Account

        try:
            account = Account.loadByLogin(login)
        except nav.db.navprofiles.NoSuchAccountError:
            return _getLoginPage(origin, "Login failed")

        if (account.authenticate(password)):
            #set session object and move to origin
            req.session['user'] = account
            req.session.save()
            if not origin.strip():
                origin = '/'
            req.headers_out['Location'] = origin
            req.status = apache.HTTP_TEMPORARY_REDIRECT
            req.send_http_header()
            raise apache.SERVER_RETURN, apache.HTTP_TEMPORARY_REDIRECT
        else:
            return _getLoginPage(origin, "Login failed")
    else:
        # The user requested only the login page
        return _getLoginPage(origin)

def _getLoginPage(origin, message=''):
    from nav.web.templates.LoginTemplate import LoginTemplate
    page = LoginTemplate()

    page.origin = origin
    page.message = message
    
    return page

#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
#
"""
This module represents the page index of the NAV web interface.  It
follows the mod_python.publisher paradigm.
"""
from mod_python import apache
import os, os.path, sys
import nav, nav.path
from nav import web
from nav.web import ldapAuth

webConfDir = os.path.join(nav.path.sysconfdir, "webfront")
welcomeFileAnonymous = os.path.join(webConfDir, "welcome-anonymous.txt")
welcomeFileRegistered = os.path.join(webConfDir, "welcome-registered.txt")
contactInformationFile = os.path.join(webConfDir, "contact-information.txt")
externalLinksFile = os.path.join(webConfDir, "external-links.txt")
navLinksFile = os.path.join(webConfDir, "nav-links.conf")

TIMES = [' seconds', ' minutes', ' hours', ' days', ' years']

def index(req):
    if req.session.has_key('user'):
        name = req.session['user'].name
    else:
        name = req.session.id

    from nav.web.templates.FrontpageTemplate import FrontpageTemplate

    page = FrontpageTemplate()
    page.path = [("Home", False)]

    if req.session['user'].id == 0:
        welcomeFile = welcomeFileAnonymous
    else:
        welcomeFile = welcomeFileRegistered
    page.welcome = lambda:file(welcomeFile).read()
    page.externallinks = lambda:file(externalLinksFile).read()
    page.contactinformation = lambda:file(contactInformationFile).read()

    navlinks = nav.config.readConfig(navLinksFile)
    navlinkshtml = ""
    for name, url in navlinks.items():
        if (nav.web.shouldShow(url, req.session['user'])):
            navlinkshtml = navlinkshtml + "<a href=\"%s\">%s</a><br>" % (url, name)
    page.navlinks = lambda:navlinkshtml

    from nav.web.messages.lib import messagelist

    page.messages = messagelist(req.session['user'])

    from nav import getstatus
    liste = nav.getstatus.boxesDownSortByNewest()
    numboxesdown = 0
    numboxesshadow = 0
    for box in liste:
        boxs = str(box[0])
        while boxs[:3] == "00:":
            boxs = boxs[3:]
        timeparts = boxs.split(':')
        time = timeparts[0] + TIMES[len(timeparts)-1]
        box.append(time)
        if box[4]:
            numboxesshadow = numboxesshadow + 1
        else:
            numboxesdown = numboxesdown + 1
    page.boxesdown = liste
    page.numboxesdown = numboxesdown
    page.numboxesshadow = numboxesshadow

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
            account = None
            apache.log_error('Account %s not found in NAVdb' % login,
                             apache.APLOG_NOTICE, req.server)
            
        authenticated = False
        if account is None:
            # If we did not find the account in the NAVdb, we try to
            # find the account through LDAP, if available.
            if ldapAuth.available:
                try:
                    authenticated = ldapAuth.authenticate(login, password)
                except ldapAuth.NoAnswerError, e:
                    return _getLoginPage(origin, "Login failed<br>(Unable to make contact with the LDAP server)")
                else:
                    if not authenticated:
                        return _getLoginPage(origin, "Login failed")
                    apache.log_error('Account %s authenticated through LDAP' % login,
                                     apache.APLOG_NOTICE, req.server)
                    # The login name was authenticated through our LDAP
                    # setup, so we create a new account in the NAVdb for
                    # this user.
                    fullName = ldapAuth.getUserName(login)
                    
                    account = Account()
                    account.login = login
                    account.name = fullName
                    account.setPassword(password)
                    account.ext_sync = 'ldap'
                    account.save()
    
                    # Later, we should allow configuration of default
                    # groups and such
            else:
                # If no alternative account retrieval methods were
                # available, we fail the login
                return _getLoginPage(origin, "Login failed")

        if not authenticated:
            if account.ext_sync == 'ldap' and ldapAuth.available:
                # Try to authenticate this ldap account through the ldap server
                try:
                    authenticated = ldapAuth.authenticate(login, password)
                    # If we were authenticated, we update the stored password hash
                    if authenticated:
                        apache.log_error('Account %s authenticated through LDAP' % login,
                                         apache.APLOG_NOTICE, req.server)
                        account.setPassword(password)
                        account.save()
                except ldapAuth.NoAnswerError, e:
                    req.session['message'] = 'No answer from LDAP server ' + str(e)
                    # Attempt to authenticate through stored password
                    # when no answer
                    authenticated = account.authenticate(password)
            else:
                # If this account is not to be externally
                # authenticated, we authenticated against NAVdb only.
                authenticated = account.authenticate(password)

        if authenticated:
            apache.log_error('Account %s successfully logged in' % login,
                             apache.APLOG_NOTICE, req.server)
            # Place the Account object in the session dictionary
            req.session['user'] = account
            req.session.save()

            # Redirect to the origin page, or to the root if one was
            # not given (using the refresh header, so as not to screw
            # up the client's POST operation)
            if not origin.strip():
                origin = '/'
            web.redirect(req, origin, seeOther=True)
        else:
            apache.log_error('Account %s failed login' % login,
                             apache.APLOG_WARNING, req.server)
            return _getLoginPage(origin, "Login failed")
    else:
        if req.session.has_key('message'):
            # Whatever sent us here has left a message for the user in
            # the session dictionary (probably an expired session)
            message = "%s<br>" % req.session['message']
            del req.session['message']
            req.session.save()
        else:
            message = ''
        # The user requested only the login page
        if origin:
            return _getLoginPage(origin,
                                 """%sYou are not authorized to access<br>%s""" % (message, origin))
        else:
            return _getLoginPage('', message)

def _getLoginPage(origin, message=''):
    from nav.web.templates.LoginTemplate import LoginTemplate
    page = LoginTemplate()

    page.origin = origin
    page.message = message
    
    return page

def logout(req):
    """
    Expires the current session, removes the session cookie and redirects to the index page.
    """
    # Expire and remove session
    req.session.expire()
    del req.session
    from nav.web import state
    state.deleteSessionCookie(req)

    # Redirect user to root page
    req.headers_out['Location'] = '/'
    req.status = apache.HTTP_TEMPORARY_REDIRECT
    req.send_http_header()
    raise apache.SERVER_RETURN, apache.HTTP_TEMPORARY_REDIRECT

def userinfo(req):
    """ Displays information about the authenticated user, and a form
    to let him/her change his/her password."""
    from nav.web.templates.UserInfo import UserInfo
    page = UserInfo()
    page.path = [("Home", "/"), ("User info", "/index/userinfo")]
    if req.session['user'].id > 0:
        page.account = req.session['user']
        page.changePassword = (page.account.ext_sync is None or len(page.account.ext_sync) == 0)

        page.groups = page.account.getGroups()
        page.orgs = page.account.getOrgIds()

    if req.session.has_key('message'):
        page.message = req.session['message']
        del req.session['message']
    if req.session.has_key('errorMessage'):
        page.errorMessage = req.session['errorMessage']
        del req.session['errorMessage']
        
    req.session.save()
    return page

def passwd(req, oldpasswd=None, newpasswd1=None, newpasswd2=None):
    """ Change the password of the authenticated user."""
    if oldpasswd is None or newpasswd1 is None or newpasswd2 is None:
        return "An internal error occurred, due to missing arguments."
    else:
        origin = '/index/userinfo'
        account = req.session['user']
        if account.id == 0:
            req.session['errorMessage'] = 'I told you, anonymous users cannot change passwords!'
        elif not account.authenticate(oldpasswd):
            req.session['errorMessage'] = 'Your old password was incorrect!'
        elif newpasswd1 != newpasswd2:
            req.session['errorMessage'] = 'Your password confirmation was incorrect!'
        else:
            account.setPassword(newpasswd1)
            account.save()
            req.session['message'] = 'Your password was successfully changed.'

        req.session.save()
        web.redirect(req, origin, seeOther=True)

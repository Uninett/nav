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
This module represents the page index of the NAV web interface.  It
follows the mod_python.publisher paradigm.
"""
from mod_python import apache
import os, os.path, sys

from nav.models.profiles import Account
import nav, nav.path
from nav import web
from nav.web import ldapAuth
import logging
import cgi
import urllib

logger = logging.getLogger("nav.web.index")

webConfDir = os.path.join(nav.path.sysconfdir, "webfront")
welcomeFileAnonymous = os.path.join(webConfDir, "welcome-anonymous.txt")
welcomeFileRegistered = os.path.join(webConfDir, "welcome-registered.txt")
contactInformationFile = os.path.join(webConfDir, "contact-information.txt")
externalLinksFile = os.path.join(webConfDir, "external-links.txt")
navLinksFile = os.path.join(webConfDir, "nav-links.conf")

TIMES = [' seconds', ' minutes', ' hours', ' days', ' years']

def _quickRead(filename):
    """
    Quickly read and return the contents of a file, or None if
    something went wrong.
    """
    try:
        return file(filename).read().strip()
    except IOError:
        return None

def index(req):
    if req.session.has_key('user'):
        name = req.session['user']['name']
    else:
        name = req.session.id

    import nav.config
    from nav.web.templates.FrontpageTemplate import FrontpageTemplate

    page = FrontpageTemplate()
    page.path = [("Home", False)]

    if req.session['user']['id'] == 0:
        welcomeFile = welcomeFileAnonymous
    else:
        welcomeFile = welcomeFileRegistered

    page.welcome = _quickRead(welcomeFile)
    page.externallinks = _quickRead(externalLinksFile)
    page.contactinformation = _quickRead(contactInformationFile)

    try:
        navlinks = nav.config.readConfig(navLinksFile)
        navlinkshtml = []
        for name, url in navlinks.items():
            if (nav.web.shouldShow(url, req.session['user'])):
                navlinkshtml.append(
                    "<a href=\"%s\">%s</a><br />" % (url, name))
        if len(navlinkshtml) > 0:
            page.navlinks = "".join(navlinkshtml)
    except IOError:
        pass

    import nav.messages
    page.msgs = nav.messages.getMsgs('publish_start < now() AND publish_end > now() AND replaced_by IS NULL')

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
    req.content_type = 'text/html'
    if login:
        # The user is attempting to log in, and we want to be sure
        # that any existing Account objects in this session are
        # deleted:
        if req.session.has_key('user'):
            del req.session['user']
            req.session.save()
        
        origin = urllib.unquote(origin)


        try:
            account = Account.objects.get(login=login)
        except Account.DoesNotExist:
            account = None
            logger.error("Account %s not found in NAVdb", login)

        authenticated = False
        if account is None:
            # If we did not find the account in the NAVdb, we try to
            # find the account through LDAP, if available.
            if ldapAuth.available:
                try:
                    authenticated = ldapAuth.authenticate(login, password)
                except ldapAuth.Error, e:
                    logger.exception("Error while talking to LDAP server")
                    return _getLoginPage(origin, "Login failed<br />(%s)" % e)
                else:
                    if not authenticated:
                        return _getLoginPage(origin, "Login failed")
                    logger.info("New account %s authenticated through LDAP", login)
                    # The login name was authenticated through our LDAP
                    # setup, so we create a new account in the NAVdb for
                    # this user.
                    fullName = ldapAuth.getUserName(login)

                    account = Account(
                        login=login,
                        name=fullName,
                        ext_sync='ldap'
                    )
                    account.set_password(password)
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
                        logger.info("Account %s authenticated through LDAP", login)
                        account.set_password(password)
                        account.save()
                except ldapAuth.Error, e:
                    req.session['message'] = 'Error while talking to ' \
                                             'LDAP: %s' % e
                    # Attempt to authenticate through stored password
                    # when no answer
                    logger.info("Attempting to authenticate %s locally",
                                login)
                    authenticated = account.check_password(password)
            else:
                # If this account is not to be externally
                # authenticated, we authenticated against NAVdb only.
                authenticated = account.check_password(password)

        if authenticated:
            logger.info("Account %s successfully logged in", login)

            # Create a dictionary with the neccessery values from the account
            # object.
            account_dict = {
                'id': account.id,
                'login': account.login,
                'name': account.name,
            }

            # Place the account information dictionary in the session
            # dictionary.
            req.session['user'] = account_dict
            req.session.save()

            # Redirect to the origin page, or to the root if one was
            # not given (using the refresh header, so as not to screw
            # up the client's POST operation)
            if not origin.strip():
                origin = '/'
            web.redirect(req, urllib.unquote(origin), seeOther=True)
        else:
            logger.warning("Account %s failed to log in", login)
            return _getLoginPage(origin, "Login failed")
    else:
        if req.session.has_key('message'):
            # Whatever sent us here has left a message for the user in
            # the session dictionary (probably an expired session)
            message = "%s<br />" % req.session['message']
            del req.session['message']
            req.session.save()
        else:
            message = ''
        # The user requested only the login page
        if origin:
            return _getLoginPage(
                origin,
                """%sYou are not authorized to access<br />%s""" %
                (message, cgi.escape(origin)))
        else:
            return _getLoginPage('', message)

def _getLoginPage(origin, message=''):
    from nav.web.templates.LoginTemplate import LoginTemplate
    page = LoginTemplate()

    page.origin = urllib.quote(origin)
    page.message = message

    return page

def logout(req):
    """
    Expires the current session, removes the session cookie and redirects to the index page.
    """
    # Expire and remove session
    login = req.session['user']['login']
    req.session.expire()
    del req.session
    from nav.web import state
    state.deleteSessionCookie(req)

    logger.info("User %s logged out", login) 
    # Redirect user to root page
    req.headers_out['Location'] = '/'
    req.status = apache.HTTP_TEMPORARY_REDIRECT
    req.send_http_header()
    raise apache.SERVER_RETURN, apache.HTTP_TEMPORARY_REDIRECT

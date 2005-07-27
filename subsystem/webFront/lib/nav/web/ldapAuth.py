# -*- coding: ISO8859-1 -*-
# Copyright 2004 Norwegian University of Science and Technology
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
#          Bjørn Ove Grøtan <bgrotan@itea.ntnu.no>
#
"""
Contains ldap authentication functionality for NAV web.
"""
import sys
from nav import web
from mod_python import apache
import nav.errors

try:
    import ldap
    available = 1
except ImportError,e:
    available = 0
    ldap = None
    apache.log_error("Python LDAP module is not available - " + str(e),
                     apache.APLOG_WARNING)

# Determine whether the config file enables ldap functionality or not
if not web.webfrontConfig.has_option('ldap', 'enabled'):
    available = 0
elif web.webfrontConfig.get('ldap', 'enabled').lower() not in ('yes', 'true', '1'):
    available = 0


#
# Function definitions
#


def openLDAP():
    """ Returns a fresh LDAP object associated with the configured LDAP server."""
    uri = web.webfrontConfig.get('ldap', 'server')
    l = ldap.initialize(uri)
    return l

def authenticate(login, password):
    """ Attempt to authenticate the login name with password against
    the configured LDAP server."""

    l = openLDAP()
    uri = web.webfrontConfig.get('ldap', 'server')
    base = web.webfrontConfig.get('ldap', 'binddn')
    dn = 'uid=%s,%s' % (login, base)
    try:
        l.simple_bind_s(dn,password)
        return True
    except ldap.SERVER_DOWN, e:
        raise NoAnswerError, uri
    except ldap.INVALID_CREDENTIALS, e:
        apache.log_error('LDAP did not authenticate account ' + login,
                         apache.APLOG_WARNING)
        return False
    except ldap.LDAPError,e:
        apache.log_error('An LDAP error occurred during authentication: ' + str(e),
                         apache.APLOG_ERR)
        return False

def getUserName(login):
    """ Attempt to retrieve the LDAP Common Name of the given login
    name."""
    l = openLDAP()
    search = 'uid=' + login
    uri = web.webfrontConfig.get('ldap', 'server')
    base = web.webfrontConfig.get('ldap', 'binddn')
    retvals = ['cn']
    try:
        res = l.search_ext_s(base,ldap.SCOPE_ONELEVEL,search,retvals,timeout=-1,sizelimit=0)
    except ldap.SERVER_DOWN, e:
        raise NoAnswerError, uri

    # Returnerer kun første posten siden man søker etter en spesifikk bruker.
    # Just look at the first result record, since we are searching for a specific login name.
    record = res[0][1]
    cn = record['cn'][0]
    return cn

#
# Exception classes
#
class Error(nav.errors.GeneralException):
    """General LDAP error"""

class NoAnswerError(Error):
    """No answer from the LDAP server"""

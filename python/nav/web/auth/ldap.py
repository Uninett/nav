#
# Copyright (C) 2007, 2010, 2011, 2014, 2015, 2017, 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Contains ldap authentication functionality for NAV web.
"""

import logging
from os.path import join
from typing import Union, Optional

import nav.errors
from nav.config import NAVConfigParser

_logger = logging.getLogger(__name__)


# Set default config params and read rest from file
class LdapWebfrontConfigParser(NAVConfigParser):
    DEFAULT_CONFIG_FILES = [join('webfront', 'webfront.conf')]
    DEFAULT_CONFIG = """
[ldap]
enabled=no
port=389
encryption=none
uid_attr=uid
name_attr=cn
require_group=
timeout=2
debug=no
lookupmethod=direct
suffix=
manager=
manager_password=
group_search=(member=%%s)
require_entitlement=
admin_entitlement=
entitlement_attribute=eduPersonEntitlement
encoding=utf-8
"""


_config = LdapWebfrontConfigParser()

try:
    import ldap
except ImportError as err:
    available = 0
    ldap = None
    _logger.warning("Python LDAP module is not available (%s) ", err)
else:
    # Determine whether the config file enables ldap functionality or not
    available = _config.getboolean('ldap', 'enabled')
    from ldap.filter import escape_filter_chars


#
# Function definitions
#


def open_ldap() -> "ldap.ldapobject.LDAPObject":
    """
    Returns a freshly made LDAP object, according to the settings
    configured in webfront.conf.
    """
    # Get config settings
    server = _config.get('ldap', 'server')
    port = _config.getint('ldap', 'port')
    encryption = _config.get('ldap', 'encryption').lower()
    timeout = _config.getfloat('ldap', 'timeout')
    # Revert to no encryption if none of the valid settings are found
    if encryption not in ('ssl', 'tls', 'none'):
        _logger.warning(
            'Unknown encryption setting %r in config file, using no encryption instead',
            _config.get('ldap', 'encryption'),
        )
        encryption = 'none'

    # Debug tracing from python-ldap/openldap to stderr
    if _config.getboolean('ldap', 'debug'):
        ldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)

    scheme = 'ldaps' if encryption == 'ssl' else 'ldap'
    uri = '%s://%s:%s' % (scheme, server, port)
    lconn = ldap.initialize(uri, bytes_mode=False)
    lconn.timeout = timeout
    lconn.set_option(ldap.OPT_REFERRALS, 0)

    # Use STARTTLS if enabled, then fail miserably if the server
    # does not support it
    if encryption == 'tls':
        _logger.debug("Using STARTTLS for ldap connection")
        try:
            lconn.start_tls_s()
        except ldap.PROTOCOL_ERROR:
            _logger.error(
                'LDAP server %s does not support the STARTTLS extension.  Aborting.',
                server,
            )
            raise NoStartTlsError(server)
        except (ldap.SERVER_DOWN, ldap.CONNECT_ERROR):
            _logger.exception("LDAP server is down")
            raise NoAnswerError(server)

    return lconn


def authenticate(login: str, password: str) -> Union["LDAPUser", bool]:
    """
    Attempt to authenticate the login name with password against the
    configured LDAP server.  If the user is authenticated, required
    group memberships are also verified.
    """
    lconn = open_ldap()
    server = _config.get('ldap', 'server')
    user = LDAPUser(login, lconn)
    # Bind to user using the supplied password
    try:
        user.bind(password)
    except (ldap.SERVER_DOWN, ldap.CONNECT_ERROR):
        _logger.exception("LDAP server is down")
        raise NoAnswerError(server)
    except ldap.INVALID_CREDENTIALS:
        _logger.warning(
            "Server %s reported invalid credentials for user %s", server, login
        )
        return False
    except ldap.TIMEOUT as error:
        _logger.error("Timed out waiting for LDAP bind operation")
        raise TimeoutError(error)
    except ldap.LDAPError:
        _logger.exception(
            "An LDAP error occurred when authenticating user %s against server %s",
            login,
            server,
        )
        return False
    except UserNotFound:
        _logger.exception(
            "Username %s was not found in the LDAP catalog %s", login, server
        )
        return False

    _logger.debug("LDAP authenticated user %s", login)

    # If successful so far, verify required group memberships before
    # the final verdict is made
    group_dn = _config.get('ldap', 'require_group')
    if group_dn:
        if user.is_group_member(group_dn):
            _logger.info("%s is verified to be a member of %s", login, group_dn)
            return user
        else:
            _logger.warning("Could NOT verify %s as a member of %s", login, group_dn)
            return False

    # If successful so far, verify required entitlements before the final verdict
    # is made
    require_entitlement = _config.get('ldap', 'require_entitlement')
    if require_entitlement:
        if user.has_entitlement(require_entitlement):
            _logger.info(
                "%s is verified to be entitled to %s", login, require_entitlement
            )
            return user
        else:
            _logger.warning(
                "Could NOT verify %s as entitled to %s", login, require_entitlement
            )
            return False

    # If no group matching was needed, we are already authenticated,
    # so return that.
    return user


class LDAPUser(object):
    """A user found or to find in an LDAP catalog.

    Given a username and an LDAP connection object, objects of this class can
    be used to search for a user in an LDAP directory, or to construct the
    user object's Distinguished Name from rules established in the
    webfront.conf config file.

    """

    def __init__(self, username: str, ldap_conn: "ldap.ldapobject.LDAPObject"):
        self.username = username
        self.ldap = ldap_conn
        self.user_dn = None

    def bind(self, password: str) -> None:
        """Performs an authenticated bind for this user using password"""
        suffix = _config.get('ldap', 'suffix')

        if not suffix:
            user_dn = self.get_user_dn()
            _logger.debug("Attempting authenticated bind to %s", user_dn)

            self.ldap.simple_bind_s(user_dn, password)
        if suffix:
            _logger.debug(
                "Attempting authenticated bind as user %s", self.username + suffix
            )

            self.ldap.simple_bind_s(self.username + suffix, password)

    def get_user_dn(self) -> str:
        """
        Given a user id (login name), return a fully qualified DN to
        identify this user, using the configured settings from
        webfront.conf.
        """
        if self.user_dn:
            return self.user_dn
        method = _config.get('ldap', 'lookupmethod')
        if method not in ('direct', 'search'):
            raise LDAPConfigError(
                'method must be "direct" or "search", not %s' % method
            )

        if method == 'direct':
            self.user_dn = self.construct_dn()
        if method == 'search':
            self.user_dn, self.username = self.search_dn()
        return self.user_dn

    def construct_dn(self) -> str:
        """Constructs and returns a Distinguished Name for this user.

        The DN is constructed using the pattern configured in webfront.conf.

        """
        uid_attr = _config.get('ldap', 'uid_attr')
        basedn = _config.get('ldap', 'basedn')
        user_dn = '%s=%s,%s' % (uid_attr, self.username, basedn)
        return user_dn

    def search_dn(self) -> tuple[str, str]:
        """Searches for the user's Distinguished Name in the LDAP directory.

        :returns: A tuple of (dn, canonical_username)
        """
        uid_attr = escape_filter_chars(_config.get('ldap', 'uid_attr'))
        encoding = _config.get('ldap', 'encoding')
        manager = _config.get('ldap', 'manager')
        manager_password = _config.get('ldap', 'manager_password', raw=True)
        if manager:
            _logger.debug("Attempting authenticated bind as manager to %s", manager)
            self.ldap.simple_bind_s(manager, manager_password)
        filter_ = "(%s=%s)" % (uid_attr, escape_filter_chars(self.username))
        result = self.ldap.search_s(
            _config.get('ldap', 'basedn'), ldap.SCOPE_SUBTREE, filter_
        )
        if not result or not result[0] or not result[0][0]:
            raise UserNotFound(filter_)

        user_dn, attrs = result[0]
        if uid_attr in attrs:
            uid = attrs[uid_attr][0].decode(encoding)
        else:
            uid = self.username
        return user_dn, uid

    def get_real_name(self) -> Optional[str]:
        """
        Attempt to retrieve the LDAP Common Name of the given login name.
        """
        encoding = _config.get('ldap', 'encoding')
        user_dn = self.get_user_dn()
        name_attr = _config.get('ldap', 'name_attr')
        try:
            res = self.ldap.search_s(
                user_dn, ldap.SCOPE_BASE, '(objectClass=*)', [name_attr]
            )
        except ldap.LDAPError:
            _logger.exception(
                "Caught exception while retrieving user name "
                "from LDAP, returning None as name"
            )
            return None

        # Just look at the first result record, since we are searching for
        # a specific user
        record = res[0][1]
        name = record[name_attr][0]
        return name.decode(encoding)

    def is_group_member(self, group_dn: str) -> bool:
        """
        Verify that uid is a member in the group object identified by
        group_dn, using the pre-initialized ldap object l.

        The full user DN will be attempted matched against the member
        attribute of the group object.  If no match is found, the user uid
        will be attempted matched against the memberUid attribute.  The
        former should work well for groupOfNames and groupOfUniqueNames
        objects, the latter should work for posixGroup objects.
        """
        group_search = _config.get('ldap', 'group_search')
        user_dn = self.get_user_dn()
        # Match groupOfNames/groupOfUniqueNames objects
        try:
            filterstr = group_search % escape_filter_chars(user_dn)
            result = self.ldap.search_s(group_dn, ldap.SCOPE_BASE, filterstr)
            _logger.debug("groupOfNames results: %s", result)
            if not result:
                # If no match, match posixGroup objects
                filterstr = '(memberUid=%s)' % escape_filter_chars(self.username)
                result = self.ldap.search_s(group_dn, ldap.SCOPE_BASE, filterstr)
                _logger.debug("posixGroup results: %s", result)
            return len(result) > 0
        except ldap.TIMEOUT as error:
            _logger.error("Timed out while verifying group memberships")
            raise TimeoutError(error)

    def get_entitlements(self) -> list[str]:
        """Returns a list of entitlements this user has"""
        encoding = _config.get('ldap', 'encoding')
        entitlement_attribute = _config.get('ldap', 'entitlement_attribute')
        user_dn = self.get_user_dn()
        filterstr = '({}=*)'.format(escape_filter_chars(entitlement_attribute))

        try:
            result = self.ldap.search_s(
                user_dn,
                ldap.SCOPE_BASE,
                filterstr=filterstr,
                attrlist=[entitlement_attribute],
            )
        except ldap.TIMEOUT as error:
            _logger.error("Timed out while fetching user entitlements")
            raise TimeoutError(error)

        _logger.debug("entitlement result: %s", result)
        if result:
            dn, attrs = result[0]
            if dn == user_dn and entitlement_attribute in attrs:
                return [ent.decode(encoding) for ent in attrs[entitlement_attribute]]

        return []

    def has_entitlement(self, entitlement: str) -> bool:
        """Verifies whether the user has a specific entitlement"""
        return entitlement in self.get_entitlements()

    def is_admin(self) -> Optional[bool]:
        """Verifies whether the user should have administrator privileges.

        :returns: True if the user should be an administrator, False if not. If no admin
        entitlement is configured, None is returned, as we cannot make such a decision.

        """
        admin_entitlement = _config.get('ldap', 'admin_entitlement')
        if admin_entitlement:
            return self.has_entitlement(admin_entitlement)


#
# Exception classes
#
class Error(nav.errors.GeneralException):
    """General LDAP error"""


class NoAnswerError(Error):
    """No answer from the LDAP server"""


class TimeoutError(NoAnswerError):
    """Timed out waiting for LDAP reply"""


class NoStartTlsError(Error):
    """The LDAP server does not support the STARTTLS extension"""


class LDAPConfigError(Error):
    """The LDAP configuration is invalid"""


class UserNotFound(Error):
    """User object was not found"""


def __test():
    """
    Test user login if module is run as script on command line.
    """
    from getpass import getpass

    logging.basicConfig()
    logging.getLogger('').setLevel(logging.DEBUG)

    uid = input("Username: ").strip()
    password = getpass('Password: ')

    user = authenticate(uid, password)

    if user:
        print("User was authenticated.")
        print("User's username is %s" % user.username)
        print("User's full name is %s" % user.get_real_name())
    else:
        print("User was not authenticated")


if __name__ == '__main__':
    __test()

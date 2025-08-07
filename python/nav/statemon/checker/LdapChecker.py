#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""LDAP service checker"""

from IPy import IP
import ldap
import ldapurl

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class LdapChecker(AbstractChecker):
    """LDAP"""

    IPV6_SUPPORT = True
    DESCRIPTION = "LDAP"
    OPTARGS = (
        (
            'url',
            "LDAP connection URL that will override the host's IP address"
            " and the default port number 389. Example: ldap://myserver"
            ".example.org:389/",
        ),
        ('base', "The LDAP server's base DN. Default is dc=example,dc=org"),
        ('scope', "One of BASE, ONELEVEL, SUBTREE"),
        ('filter', "An LDAP search filter. Example: cn=monitor"),
        ('version', "Which LDAP protocol version, 2 or 3. Default is 3."),
        ('username', "A specific username to bind as"),
        ('password', "The password to use when binding with a username"),
        ('port', "The TCP port of the LDAP server. 389 is the default."),
        ('timeout', "A response timeout in seconds."),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=389, **kwargs)

    def execute(self):
        args = self.args
        # we can connect in 2 ways. By hostname/ip (and portnumber)
        # or by ldap-uri
        if "url" in args and ldapurl.isLDAPUrl(args["url"]):
            conn = ldap.initialize(args["url"])
        else:
            ip, port = self.get_address()
            conn = ldap.initialize("ldap://%s:%s" % (ip, port))
        try:
            username = args.get("username", "")
            password = args.get("password", "")
            conn.simple_bind(username, password)

            try:
                self._set_version(args, conn)
            except ValueError:
                return Event.DOWN, "unsupported protocol version"

            base = args.get("base", "dc=example,dc=org")
            if base == "cn=monitor":
                my_res = conn.search_st(base, ldap.SCOPE_BASE, timeout=self.timeout)
                versionstr = str(my_res[0][-1]['description'][0])
                self.version = versionstr
                return Event.UP, versionstr
            scope = args.get("scope", "SUBTREE").upper()
            if scope == "BASE":
                scope = ldap.SCOPE_BASE
            elif scope == "ONELEVEL":
                scope = ldap.SCOPE_ONELEVEL
            else:
                scope = ldap.SCOPE_SUBTREE
            filtr = args.get("filter", "objectClass=*")
            try:
                conn.search_ext_s(base, scope, filterstr=filtr, timeout=self.timeout)
            except Exception as err:  # noqa: BLE001
                return (
                    Event.DOWN,
                    "Failed ldapSearch on %s for %s: %s"
                    % (self.get_address(), filtr, str(err)),
                )
        finally:
            try:
                conn.unbind()
            except Exception:  # noqa: BLE001
                pass

        return Event.UP, "Ok"

    @staticmethod
    def _set_version(args, conn):
        if "version" in args:
            version = int(args["version"])
            if version == 2:
                conn.protocol_version = ldap.VERSION2
            elif version == 3:
                conn.protocol_version = ldap.VERSION3
            else:
                raise ValueError("Unsupported protocol version %s" % version)
        else:
            # default is protocol-version 3
            conn.protocol_version = ldap.VERSION3

    def get_address(self):
        ip, port = AbstractChecker.get_address(self)
        addr = IP(ip)
        if addr.version() == 6:
            ip = '[%s]' % ip
        return ip, port

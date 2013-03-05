#
# Copyright (C) 2003,2004 Norwegian University of Science and Technology
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
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
import ldapurl

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
import ldap


class LdapChecker(AbstractChecker):
    """LDAP"""
    TYPENAME = "ldap"
    IPV6_SUPPORT = True
    DESCRIPTION = "LDAP"
    OPTARGS = (
        ('url', "LDAP connection URL that will override the host's IP address"
                " and the default port number 389. Example: ldap://myserver"
                ".example.org:389/"),
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
        args = self.getArgs()
        # we can connect in 2 ways. By hostname/ip (and portnumber)
        # or by ldap-uri
        if "url" in args and ldapurl.isLDAPUrl(args["url"]):
            conn = ldap.initialize(args["url"])
        else:
            ip, port = self.getAddress()
            conn = ldap.initialize("ldap://%s:%s" % (ip, port))
        username = args.get("username", "")
        password = args.get("password", "")
        conn.simple_bind(username, password)

        try:
            self._set_version(args, conn)
        except ValueError:
            return Event.DOWN, "unsupported protocol version"

        base = args.get("base", "dc=example,dc=org")
        if base == "cn=monitor":
            my_res = conn.search_st(base, ldap.SCOPE_BASE,
                                    timeout=self.getTimeout())
            versionstr = str(my_res[0][-1]['description'][0])
            self.setVersion(versionstr)
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
            conn.search_ext_s(base, scope, filterstr=filtr,
                              timeout=self.getTimeout())
            # pylint: disable=W0703
        except Exception as err:
            return (Event.DOWN,
                    "Failed ldapSearch on %s for %s: %s" % (
                        self.getAddress(), filtr, str(err)))

        conn.unbind()

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

    def getAddress(self):
        ip, port = AbstractChecker.getAddress(self)
        addr = IP(ip)
        if addr.version() == 6:
            ip = '[%s]' % ip
        return ip, port


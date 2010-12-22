# -*- coding: utf-8 -*-
#
# Copyright (C) 2003,2004 Norwegian University of Science and Technology
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

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
import ldap
import base64
import string

class LdapChecker(AbstractChecker):
    """
    Handle LDAP-servers. It can be quite simple (just try anonymous bind) or quite
    sophisticated with additional search and retrieve specific dn's with specific attributes.

    Arguments to this handler (with explenations):
    port:    remote tcp-port where ldap-server is living. Default is 389
    hostname: accessible from self.getAddress() as pure FQDN hostname
    url:    if this is defined as arguments this will override hostname/port
        example-url: ldap://myserver.mydomain.com:389
    version: implies protocol-version of LDAP. Default is 3 - though 2 is also supported
    username: leave this blank if you want to bind anonymously
    password: leave this blank if you want to bind anonymously
    authtype: meant to handle authentication-types. Not implemented yet. Only simple auth yet
        types will be: TLS, SASL, simple, Kerberos
    base:    the server's basedn (e.g. dc=mydomain,dc=com)
    scope:    what level of the search will be needed? BASE, ONELEVEL and SUBTREE can be used
    filter: dn to search for. May have regexp and more. Example: cn=monitor
    compare: uses the function compare_s(dn, attr, value)  - useful for testing whether an object has a particular value (instead of doing a search with SCOPE_BASE and checking the value)
    attrs:  specific attributes you want to retrieve from searching filter (not implemented in this version)
    attr_val: regexp for matching attrs. If matched - Event.UP is returned - else Event.DOWN (not implemented in this version)

    NB! If compare is set/given - attrs and attr_val will be ignored!
    """

    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "ldap", service,port=389, **kwargs)
    def execute(self):
        args = self.getArgs()
        versionstr = ""
        # we can connect in 2 ways. By hostname/ip (and portnumber)
        # or by ldap-uri
        if args.has_key("url"):
            if ldap.is_ldap_url(args["url"]):
                l = ldap.initialize(args["url"])
        else:
            ip, port = self.getAddress()
            l = ldap.open(ip, port=port)
        username = args.get("username","")
        password = args.get("password","")
        timeout = self.getTimeout()
        l.simple_bind(username, password)
        if args.has_key("version"):
            version = args["version"]
            if (version==2):
                l.protocol_version = ldap.VERSION2
            elif (version==3):
                l.protocol_version = ldap.VERSION3
            else:
                return Event.DOWN, "unsupported protocol version"
        else:
            # default is protocol-version 3
            try:
                l.protocol_version = ldap.VERSION3
            except Exception,e:
                return Event.DOWN, "unsupported protocol version"
        if args.has_key("compare"):
            try:
                result = l.compare_s(dn,attribute,value)
                if result:
                    return Event.UP, "Ok"
                else:
                    return Event.DOWN, "compare failed: %s:%s" % (attribute,value)
            except Exception,e:
                return Event.DOWN, "compare failed for some reason"

        else:
            base = args.get("base", "dc=ntnu,dc=no")
            if base == "cn=monitor":
                my_res = l.search_st(base, ldap.SCOPE_BASE, timeout=self.getTimeout())
                versionstr=str(my_res[0][-1]['description'][0])
                self.setVersion(versionstr)
                return Event.UP, versionstr
            scope = args.get("scope", "SUBTREE")
            scope = scope.upper()
            if scope == "BASE":
                scope = ldap.SCOPE_BASE
            elif scope == "ONELEVEL":
                scope = ldap.SCOPE_ONELEVEL
            else:
                scope =ldap.SCOPE_SUBTREE
            filter = args.get("filter","objectclass=dcObject")
            attrs = args.get("attrs", ["mail"])
            try:
                my_res = l.search_ext_s(base, scope,
                            filterstr=filter,
                            attrlist=attrs,
                            timeout=self.getTimeout())

                dn = my_res[0][0]
                mydict = my_res[0][1]
            except Exception,e:
                print "Exception: %s" % str(e)
                return Event.DOWN, "Failed ldapSearch on %s for %s: %s" % (self.getAddress(), filter, str(e))
                
            l.unbind()

        return Event.UP, "Ok"

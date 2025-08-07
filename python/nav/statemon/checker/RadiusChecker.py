#
# Copyright (C) 2018 Uninett AS
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
"""RADIUS service checker"""

from nav.util import resource_filename

# Python-radius specific modules. pyrad found at
# http://www.wiggy.net/code/pyrad/ by Wichert Akkermann
import pyrad.packet
from pyrad.client import Client
from pyrad.dictionary import Dictionary

# NAV ServiceMonitor-modules
from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


DEFAULT_DICTIONARY = resource_filename(
    'nav.statemon.checker', 'radius/dictionary.rfc2865'
)


class RadiusChecker(AbstractChecker):
    """
    Radius Monitor-client.

    Handles Radius-servers. It tries to authenticate like for example any
    VPN-concentrator from Cisco would.

    Future enhancements would be to check if we get a certain attribute
    back from the server, and what the value of that attribute would be.
    For now, we just connect and authenticate to radius.

    Arguments:
    ----------
    hostname  : Accessible from self.get_address() as pure FQDN hostname
    port      : Remote udp-port where radius authentication is living.
                Port 1812 is default for authentication.
    username  : A valid radius-username
    password  : Clear-text password associated with the username above.
    identifier: Each "client-source" connects to radius with a given
                identity and secret.
    rad_secret: Password associated with 'identifier'
    dictionary: Path to filename which holds the dictionary for this
                radius-daemon. The default-dictionary can be used, or
                a specific dictionary for a specific implementation
                of the radius-server.

    Return values:
    --------------
    Successful connection:
        return Event.UP, "Radius: " + version/implementation (if we find it)
    Failure to connect:
        return Event.DOWN, str(sys.exc_value)
    """

    # TODO: Check for IPv6 compatibility in pyrad
    DESCRIPTION = "RADIUS"
    ARGS = ()
    OPTARGS = (
        ('username', 'A valid RADIUS username'),
        ('password', 'Clear-text password for username'),
        ('identifier', "This client's RADIUS identifier"),
        ('secret', 'A RADIUS secret for this client'),
        (
            'dictionary',
            'Full path to a file containing an optional dictionary file for '
            'this radius server',
        ),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=1812, **kwargs)

    def execute(self):
        args = self.args
        try:
            username = args.get("username", "")
            password = args.get("password", "")
            rad_secret = args.get("secret", "").encode("utf-8")
            identifier = args.get("identifier", "")
            dictionary = args.get("dictionary", DEFAULT_DICTIONARY)
            ip, _port = self.get_address()
            srv = Client(server=ip, secret=rad_secret, dict=Dictionary(dictionary))
            req = srv.CreateAuthPacket(
                code=pyrad.packet.AccessRequest,
                User_Name=username,
                NAS_Identifier=identifier,
            )
            req["User-Password"] = req.PwCrypt(password)
            srv.SendPacket(req)
        except Exception as err:  # noqa: BLE001
            return (
                Event.DOWN,
                "Failed connecting to %s: %s)" % (self.get_address(), str(err)),
            )
        version = "FreeRadius 1.0"  # Fetch from radiusmonitor later.
        self.version = version
        return Event.UP, "Radius: " + version

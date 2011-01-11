# -*- coding: utf-8 -*-
#
# Copyright (C) 2004,2005 Norwegian University of Science and Technology
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

# Python Standard library
import sys,string,os,exceptions

# NAV ServiceMonitor-modules
from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event

# Python-radius specific modules. pyrad found at 
# http://www.wiggy.net/code/pyrad/ by Wichert Akkermann
import pyrad.packet
from pyrad.client import Client
from pyrad.dictionary import Dictionary

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
    hostname  : Accessible from self.getAddress() as pure FQDN hostname
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
    def __init__(self,service,**kwargs):
        AbstractChecker.__init__(self,"radius",service, port=1812, **kwargs)

    def execute(self):
        args = self.getArgs()
        try:
            username = args.get("username","")
            password = args.get("password","")
            rad_secret = args.get("secret","")
            identifier = args.get("identifier","")
            dictionary = args.get("dictionary","") # or "dictionary"
            ip,port = self.getAddress()
            srv = Client(server=ip,secret=rad_secret,dict=Dictionary(dictionary))
            req = srv.CreateAuthPacket(code=pyrad.packet.AccessRequest,
                    User_Name=username, NAS_Identifier=identifier)
            req["User-Password"] = req.PwCrypt(password)
            reply = srv.SendPacket(req)
        except Exception,e:
            return Event.DOWN, "Failed connecting to %s: %s)" % (self.getAddress(),str(e))
        version = "FreeRadius 1.0" # Fetch from radiusmonitor later.
        self.setVersion(version) 
        return Event.UP, "Radius: " + version

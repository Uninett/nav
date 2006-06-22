#! /usr/bin/env python
# -*- coding: ISO8859-1 -*-
#
# Copyright 2006 UNINETT AS
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

"""
The Boost Communication SMS gateway dispatcher.

This dispatcher sends SMS via Boost Communications WebService (SOAP). Requires
a username and password to send SMS using the SOAP interface.

Contact http://www.boostcom.no/ to setup a contract.
The remote service is called ExternalSender.
"""

__copyright__ = "Copyright 2006 Bjørn Ove Grøtan"
__license__ = "GPL"
__author__ = "Bjørn Ove Grøtan (bjorn.ove@grotan.com)"
__id__ = "$Id: boostsmsgwdispatcher.py 3464 2006-06-22 08:58:05Z bgrotan $"

import logging
import sys

try:
    from SOAPpy import SOAPProxy
except ImportError,ie:
    print 'SOAPpy not installed or misconfigured.'
    sys.exit(255)

class BoostSMSGWDispatcher(object):
    "The smsd dispatcher for BoostCom."
    def __init__(self):
        """Constructor."""

        # Create logger
        self.logger = logging.getLogger("nav.smsd.dispatcher")
        # Remote address for gateway
        self._url = "https://secure.boostcom.net/axis/services/ExternalSender"
        # FIXME: generalize and fetch from config-file
        # Username for WebService
        self._username = None # FIXME: fetch from config-file
        # Password for WebService
        self._password = None # FIXME; fetch from config-file
        # Our phonenumber
        self._sender = None # FIXME: fetch from config-file

        # Initiate connector to Boost
        try:
            self._service = SOAPProxy(self._url)
        except:
            # FIXME: what kinds of exceptions can we get?
            print 'An error occured.. ayee'
            sys.exit(255)

    def sendsms(self, receiver, message):
        """
        Send SMS using Boost's SMS gateway.

        Returns true/false if success or not.
        """

        result = self._service.sendMessage(
                    self._username,
                    self._password,
                    self._sender,
                    receiver,
                    message)
        if result:
            result = True
        else:
            result = False
        return (result,0)

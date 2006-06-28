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
Dispatcher for Boost Communications' External Sender product.

This dispatcher sends SMS via Boost Communications' WebService (SOAP). Requires
a username and password to send SMS using the SOAP interface.

Contact http://www.boostcom.no/ to setup a contract.
The remote service is called ExternalSender.

Depends on SOAPpy/python-soappy.
"""

__copyright__ = "Copyright 2006 Bjørn Ove Grøtan"
__license__ = "GPL"
__author__ = "Bjørn Ove Grøtan (bjorn.ove@grotan.com),", \
    "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id: boostdispatcher.py 3464 2006-06-22 08:58:05Z bgrotan $"

from nav.smsd.dispatcher import *

try:
    from SOAPpy import SOAPProxy
except ImportError, ie:
    raise DispatcherError, \
     'SOAPpy not installed or misconfigured.'

class BoostDispatcher(Dispatcher):
    """The smsd dispatcher for Boost Communications' External Sender."""

    def __init__(self, config):
        """Constructor."""

        # Call mother's init
        Dispatcher.__init__(self)

        # Get config
        try:
            # Remote address for gateway
            self.url = config['url']
            # Username for WebService
            self.username = config['username']
            # Password for WebService
            self.password = config['password']
            # Our phonenumber
            self.sender = config['sender']
        except KeyError, error:
            raise DispatcherError, "Config option not found: %s" % error

        # Initiate connector to Boost
        try:
            self.service = SOAPProxy(self.url)
        except Exception, error:
            raise DispatcherError, "Failed to initialize SOAPProxy: %s" % error

    def sendsms(self, receiver, message):
        """
        Send SMS using Boost's SMS gateway.

        Returns two values:
            A boolean which is true for success and false for failure.
            An integer which is the sending ID if available or 0 otherwise.
        """

        # FIXME: Check for exceptions here
        result = self.service.sendMessage(
                    self.username,
                    self.password,
                    self.sender,
                    receiver,
                    message)
        if result:
            result = True
        else:
            result = False

        return (result, 0)

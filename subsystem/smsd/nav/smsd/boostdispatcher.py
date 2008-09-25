#! /usr/bin/env python
# -*- coding: utf-8 -*-
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
    "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"

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

    def sendsms(self, phone, msgs):
        """
        Send SMS using Boost Communications' External Sender.

        Arguments:
            ``phone'' is the phone number the messages are to be dispatched to.
            ``msgs'' is a list of messages ordered with the most severe first.
            Each message is a tuple with ID, text and severity of the message.

        Returns five values:
            The formatted SMS.
            A list of IDs of sent messages.
            A list of IDs of ignored messages.
            A boolean which is true for success and false for failure.
            An integer which is the sending ID if available or 0 otherwise.
        """

        # Format SMS
        (sms, sent, ignored) = self.formatsms(msgs)

        # Send SMS
        try:
            result = self.service.sendMessage(
                        self.username,
                        self.password,
                        self.sender,
                        phone,
                        sms)
            self.logger.debug("BoostDispatcher result: %s", result)
        except Exception, error:
            self.logger.exception(error)

        if result:
            result = True
        else:
            result = False
        smsid = 0

        return (sms, sent, ignored, result, smsid)


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
A dispatcher for UNINETT's mail-to-SMS gateway.

This dispatcher sends SMS via UNINETT's mail-to-SMS gateway. The mail must be
sent from a uninett.no host, so this is of little use for others.
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"

import os
import pwd
import smtplib
import socket
from nav.smsd.dispatcher import *

class UninettMailDispatcher(Dispatcher):
    """The smsd dispatcher for UNINETT's mail-to-SMS gateway."""

    def __init__(self, config):
        """Constructor."""

        # Call mother's init
        Dispatcher.__init__(self)

        # Get config
        try:
            # Mail adress for gateway
            self.mailaddr = config['mailaddr']
        except KeyError, error:
            raise DispatcherError, "Config option not found: %s" % error

    def sendsms(self, phone, msgs):
        """
        Send SMS using UNINETT's mail-to-SMS gateway.

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

        # NOTE: This dispatcher should be made a general
        # SMS-via-mail-dispatcher if there is any wish for it.
        # This includes supporting various formats for the mail.

        # Format SMS
        (sms, sent, ignored) = self.formatsms(msgs)

        # Send SMS
        sender = "%s@%s" % (pwd.getpwuid(os.getuid())[0], socket.gethostname())
        headers = "From: %s\r\nTo: %s\r\nSubject: sms %s\r\n\r\n" % (
            sender, self.mailaddr, phone)
        message = headers + sms

        try:
            server = smtplib.SMTP('localhost')
            result = server.sendmail(sender, self.mailaddr, message)
            server.quit()
        except SMTPException, error:
            raise DispatcherError, "SMTP error: %s" % error

        if len(result) == 0:
            # No errors
            result = True
        else:
            # If anything failed the SMTPException above should handle it
            result = False
        smsid = 0

        return (sms, sent, ignored, result, smsid)


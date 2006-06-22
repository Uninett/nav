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
The UNINETT mail/SMS gateway dispatcher for Gammu.

This dispatcher sends SMS via UNINETT's existing mail/SMS gateway. The mail
must be sent from a uninett.no host, so this is of little use for others.
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id: gammudispatcher.py 3464 2006-06-22 08:58:05Z jodal $"

import os
import pwd
import smtplib
import socket
import nav.smsd.dispatcher

class UninettSMSGWDispatcher(nav.smsd.dispatcher.Dispatcher):
    "The smsd dispatcher for Gammu."
    def __init__(self):
        """Constructor."""

        # Call mother's init
        nav.smsd.dispatcher.Dispatcher.__init__(self)

        # FIXME: Read the rest from config

        # Mail adress for gateway
        self.mailaddr = 'sms@uninett.no'

    def sendsms(self, phone, sms):
        """
        Send SMS using UNINETT's mail/SMS gateway.

        Returns two values:
            A boolean which is true for success and false for failure.
            An integer which is the sending ID if available or 0 otherwise.
        """

        # FIXME: This dispatcher should be made a general
        # SMS-via-mail-dispatcher if there is any wish for it.
        # This includes supporting various formats for the mail.

        sender = "%s@%s" % (pwd.getpwuid(os.getuid())[0], socket.gethostname())
        headers = "From: %s\r\nTo: %s\r\nSubject: sms %s\r\n\r\n" % \
         (sender, self.mailaddr, phone)
        message = headers + sms
        server = smtplib.SMTP('localhost')
        # FIXME: Check for exceptions here?
        server.sendmail(sender, self.mailaddr, message)
        server.quit()

        # FIXME: Give these a bit more resonable values ;-)
        result = True
        smsid = 0

        return (result, smsid)


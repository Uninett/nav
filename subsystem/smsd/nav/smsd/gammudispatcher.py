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
The smsd dispatcher for Gammu.

This dispatcher takes care of all communication between smsd and Gammu. Gammu
is used to send SMS messages via a cell phone connected to the server with a
serial cable, USB cable, IR or Bluetooth. See http://www.gammu.org/ for more
information.

Depends on python-gammu.
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id$"

import gammu
import logging
import sys
import nav.smsd.dispatcher

class GammuDispatcher(nav.smsd.dispatcher.Dispatcher):
    "The smsd dispatcher for Gammu."
    def __init__(self):
        """Constructor."""

        # Call mother's init
        nav.smsd.dispatcher.Dispatcher.__init__(self)

    def sendsms(self, phone, sms):
        """
        Send SMS using Gammu.

        Returns two values:
            A boolean which is true for success and false for failure.
            An integer which is the sending ID if available or 0 otherwise.
        """

        # We got a python-gammu binding :-)
        sm = gammu.StateMachine()

        try:
            # Typically ~root/.gammurc or ~navcron/.gammurc
            sm.ReadConfig()
        except IOError, error:
            self.logger.exception("Error while reading Gammu config. Exiting. (%s)",
             error)

        try:
            # Fails if e.g. phone is not connected
            # See http://www.gammu.org/wiki/index.php?title=Gammu:Error_Codes
            # for complete list of errors fetched here
            sm.Init()
        except gammu.GSMError, error:
            self.logger.exception("GSM error %d: %s", error[0]['Code'], error[0]['Text'])

        # Tested with Nokia 6610, Tekram IRmate 410U and Gammu 1.07.00
        message = {'Text': sms, 'SMSC': {'Location': 1}, 'Number': phone}
        smsid = sm.SendSMS(message)

        if smsid:
            result = True
        else:
            result = False
        return (result, smsid)


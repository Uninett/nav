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
Class with common functions inherited/overrided by other dispatchers.
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id: gammudispatcher.py 3464 2006-06-22 08:58:05Z jodal $"

import logging
import sys

class Dispatcher(object):
    "The SMS formatter."
    def __init__(self):
        """Constructor."""

        # Create logger
        self.logger = logging.getLogger("nav.smsd.formatter")
        # Max length of SMS
        self.maxlen = 160
        # Max length of ignored message. 15 gives us up to four digits.
        self.ignlen = 15

    def formatsms(self, msgs):
        """
        Format a SMS from one or more messages.

        ``msgs'' is a list of messages ordered with the most severe first. Each
        message is a tuple with ID, text and severity of the message.

        Returns a tuple with the SMS, a list of IDs of sent messages and a list
        of IDs of ignored messages.

        Pseudo code:
        If one message
            SMS = message
        If multiple messages
            SMS = as many msgs as possible + how many was ignored
        """

        # Copies so we can modify them without wreaking the next SMS
        maxlen = self.maxlen
        ignlen = self.ignlen

        msgcount = len(msgs) # Number of messages
        msgno = 0 # Number of messages processed
        addmsg = True # Whether we shall continue to add msgs to the SMS
        tmpsms = "" # We format first and then checks the length

        # The empty result
        sms = ""
        sent = []
        ignored = []

        # Concatenate as many msgs as possible
        for msg in msgs:
            msgno += 1

            # If this is the last message we don't need to reserve space for
            # the ignored count. If we have enough space, we can add the
            # message itself instead. If we don't have enough space, the "+1
            # see web" is added as normal.
            if msgno == msgcount:
                ignlen = 0

            # We create a temporary SMS first and then afterwards checks if
            # it's short enough to be accepted. This makes it easy to also
            # count all extra space, numbering, etc.
            if msgno == 1:
                tmpsms = msg[1]
            elif msgno == 2:
                tmpsms = "1: %s; 2: %s" % (sms, msg[1])
            else:
                tmpsms = "%s; %d: %s" % (sms, msgno, msg[1])

            # If we have enough space...
            if len(tmpsms) < (maxlen - ignlen) and addmsg:
                # Accept updated SMS
                sms = tmpsms
                sent.append(msg[0])
            else:
                # Ignore message
                ignored.append(msg[0])

                # Stop adding messages when the first fail to fit
                addmsg = False

        # Tell how many was ignored
        if len(ignored) > 0:
            sms = "%s +%d see web." % (sms, len(ignored))

        return (sms, sent, ignored)

    def sendsms(self, phone, sms):
        """
        Empty shell for the sendsms method implemented by subclasses.
        
        Takes phonen number and the SMS message as input.

        Returns two values:
            A boolean which is true for success and false for failure.
            An integer which is the sending ID if available or 0 otherwise.
        """

        result = False
        smsid = 0

        return (result, smsid)

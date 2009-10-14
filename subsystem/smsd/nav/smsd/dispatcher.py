#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2009 UNINETT AS
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

__copyright__ = "Copyright 2006-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"

import logging
import sys
import time

class DispatcherError(Exception):
    """Base class for all exceptions raised by dispatchers."""

class PermanentDispatcherError(DispatcherError):
    """Thrown for permanent errors in dispatchers."""

class DispatcherHandler(object):
    """
    Handler for communication with the dispatchers.

    This layer makes it possible to use multiple dispatchers which works as
    failovers for each other.
    """

    def __init__(self, config):
        """Constructor."""

        # Create logger
        self.logger = logging.getLogger("nav.smsd.dispatcher")

        # Get config
        try:
            self.dispatcherretry = config['dispatcher']['dispatcherretry']
        except KeyError, error:
            self.dispatcherretry = 300 # 5 min
            self.logger.debug('Dispatcher retry time not set. Default %ds.' %
                self.dispatcherretry)

        # Get dispatchers
        self.dispatchers = []
        for pri in range(len(config['dispatcher']) + 1):
            key = 'dispatcher' + str(pri)
            if key in config['dispatcher']:
                dispatcher = config['dispatcher'][key]
                self.logger.debug("Init dispatcher %d: %s", pri, dispatcher)

                # Import dispatcher module
                modulename = 'nav.smsd.' + dispatcher.lower()
                try:
                    module = self.importbyname(modulename)
                    self.logger.debug("Imported module %s", modulename)
                except DispatcherError, error:
                    self.logger.warning("Failed to import %s: %s",
                     dispatcher, error)
                    continue
                except Exception, error:
                    self.logger.exception("Unknown exception: %s", error)

                # Initialize dispatcher
                try:
                    dispatcher_class = getattr(module, dispatcher)
                    instance = dispatcher_class(config[dispatcher])
                    self.dispatchers.append((dispatcher, instance))
                    self.logger.debug("Dispatcher loaded: %s", dispatcher)
                except DispatcherError, error:
                    self.logger.warning("Failed to init %s: %s",
                        dispatcher, error)
                    continue
                except Exception, error:
                    self.logger.exception("Unknown exception: %s", error)

        # Fail if no dispatchers are available
        if len(self.dispatchers) == 0:
            raise PermanentDispatcherError, \
                  "No dispatchers available. None configured " + \
                  "or all dispatchers failed permanently."

    def importbyname(self, name):
        """Import module given by name."""
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    def sendsms(self, phone, msgs):
        """
        Formats and sends with help of the wanted dispatcher.

        Arguments:
            ``phone'' is the phone number the messages are to be dispatched to.
            ``msgs'' is a list of messages ordered with the most severe first.
            Each message is a tuple with ID, text and severity of the message.

        Returns four values:
            The formatted SMS.
            A list of IDs of sent messages.
            A list of IDs of ignored messages.
            An integer which is the sending ID if available or 0 otherwise.

        Raises a DispatcherError if it doesn't find a working dispatcher and
        succeeds in sending the SMS.
        """

        for i, (dispatchername, dispatcher) in enumerate(self.dispatchers):

            if dispatcher.lastfailed:
                sincelastfail = int(time.time()) - dispatcher.lastfailed
                if sincelastfail < self.dispatcherretry:
                    self.logger.debug("%s last failed %ds ago. Skipping.",
                        dispatchername, sincelastfail)
                    continue # Skip this dispatcher for now

            try:
                self.logger.debug("Trying %s...", dispatchername)
                (sms, sent, ignored, result, smsid) = \
                    dispatcher.sendsms(phone, msgs)
            except PermanentDispatcherError, error:
                self.logger.error("%s failed permanently to send SMS: %s",
                    dispatchername, error)
                self.logger.info("Removing failed dispatcher %s.",
                    dispatchername)
                del self.dispatchers[i]
                continue # Skip to next dispatcher
            except DispatcherError, error:
                self.logger.warning("%s failed to send SMS: %s",
                    dispatchername, error)
                dispatcher.lastfailed = int(time.time())
                continue # Skip to next dispatcher
            except Exception, error:
                self.logger.exception(
                    "Unknown dispatcher exception during send: %s", error)
                continue

            else:
                if result is False:
                    self.logger.warning(
                        "%s failed to send SMS: Returned false.",
                        dispatchername)
                    dispatcher.lastfailed = int(time.time())
                    continue # Skip to next dispatcher

            # No exception and true result? Success!
            return (sms, sent, ignored, smsid)

        # Still running? All dispatchers failed permanently.
        if len(self.dispatchers) == 0:
            raise PermanentDispatcherError, \
                  "No dispatchers available. None configured " + \
                  "or all dispatchers failed permanently."

        # Still running? All dispatchers failed!
        raise DispatcherError, "All dispatchers failed to send SMS."

class Dispatcher(object):
    """The SMS dispatcher mother class."""

    def __init__(self):
        """Constructor."""

        # Create logger
        self.logger = logging.getLogger("nav.smsd.dispatcher")
        # Field for last failed timestamp
        self.lastfailed = None
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

    def sendsms(self, phone, msgs):
        """
        Empty shell for the sendsms method implemented by subclasses.

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
        result = False
        smsid = 0

        return (sms, sent, ignored, result, smsid)


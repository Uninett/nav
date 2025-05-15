# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Dispatch handling for smsd"""

import logging


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

        exit_on_permanent_error = config['main']['exit_on_permanent_error']
        self.cull_dead_dispatcher = exit_on_permanent_error.lower() in ('yes', 'true')

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
                except DispatcherError as error:
                    self.logger.warning("Failed to import %s: %s", dispatcher, error)
                    continue
                except Exception as error:  # noqa: BLE001
                    self.logger.exception("Unknown exception: %s", error)

                # Initialize dispatcher
                try:
                    dispatcher_class = getattr(module, dispatcher)
                    instance = dispatcher_class(config[dispatcher])
                    self.dispatchers.append((dispatcher, instance))
                    self.logger.debug("Dispatcher loaded: %s", dispatcher)
                except DispatcherError as error:
                    self.logger.warning("Failed to init %s: %s", dispatcher, error)
                    continue
                except Exception as error:  # noqa: BLE001
                    self.logger.exception("Unknown exception: %s", error)

        # Fail if no dispatchers are available
        if not self.dispatchers:
            raise PermanentDispatcherError(
                "No dispatchers available. None configured "
                "or all dispatchers failed permanently."
            )

    def importbyname(self, name):
        """Imports Python module given by name.

        :param name: a module name.
        :returns: a module object.

        """
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    def sendsms(self, phone, msgs):
        """
        Formats and sends with help of the wanted dispatcher.

        :param phone: the phone number the messages are to be dispatched to.
        :param msgs: a list of messages ordered with the most severe first.
                     Each message is a tuple with ID, text and severity of the
                     message.

        :returns: A tuple of four values:

                  * The formatted SMS.
                  * A list of IDs of sent messages.
                  * A list of IDs of ignored messages.
                  * An integer which is the sending ID if available or 0
                    otherwise.

        :raises: :exc:`DispatcherError` if it doesn't find a working
                 dispatcher and succeeds in sending the SMS.

        """

        for i, (dispatchername, dispatcher) in enumerate(self.dispatchers):
            try:
                self.logger.debug("Trying %s...", dispatchername)
                (sms, sent, ignored, result, smsid) = dispatcher.sendsms(phone, msgs)
            except PermanentDispatcherError as error:
                self.logger.error(
                    "%s reports a possibly permanent SMS dispatch failure: %s",
                    dispatchername,
                    error,
                )
                if self.cull_dead_dispatcher:
                    self.logger.error(
                        "Removing permanently failed dispatcher %s", dispatchername
                    )
                    del self.dispatchers[i]
                continue  # Skip to next dispatcher
            except DispatcherError as error:
                self.logger.warning("%s failed to send SMS: %s", dispatchername, error)
                continue  # Skip to next dispatcher
            except Exception as error:  # noqa: BLE001
                self.logger.exception(
                    "Unknown dispatcher exception during send: %s", error
                )
                continue

            else:
                if result is False:
                    self.logger.warning(
                        "%s failed to send SMS: Returned false.", dispatchername
                    )
                    continue  # Skip to next dispatcher

            # No exception and true result? Success!
            return (sms, sent, ignored, smsid)

        # Still running? All dispatchers failed permanently.
        if not self.dispatchers:
            raise PermanentDispatcherError(
                "No dispatchers available. None configured "
                "or all dispatchers failed permanently."
            )

        # Still running? All dispatchers failed!
        raise DispatcherError("All dispatchers failed to send SMS.")


class Dispatcher(object):
    """The SMS dispatcher mother class."""

    def __init__(self):
        """Constructor."""

        # Create logger
        self.logger = logging.getLogger("nav.smsd.dispatcher")
        # Max length of SMS
        self.maxlen = 160
        # Max length of ignored message. 15 gives us up to four digits.
        self.ignlen = 15

    def formatsms(self, msgs):
        """Formats a single SMS from one or more messages.

        Attempts to squeeze as many messages into the 160-characters that an
        SMS is limited to.

        :param msgs: a list of messages ordered with the most severe
                     first. Each message is a tuple with ID, text and severity
                     of the message.

        :returns: a 3-value tuple containing:

                  * the formatted text of the SMS
                  * a list of IDs of the messages that fit into the single SMS
                  * if list of IDs of the message that didn't fit in the SMS
                    and were subsequently ignored

        """

        # Copies so we can modify them without wreaking the next SMS
        maxlen = self.maxlen
        ignlen = self.ignlen

        msgcount = len(msgs)  # Number of messages
        msgno = 0  # Number of messages processed
        addmsg = True  # Whether we shall continue to add msgs to the SMS
        tmpsms = ""  # We format first and then checks the length

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
        if ignored:
            sms = "%s +%d see web." % (sms, len(ignored))

        return sms, sent, ignored

    def sendsms(self, phone, msgs):
        """Sends messages as an SMS to a phone number.

        This method must be overridden by implementers to have any effect.

        :param phone: the phone number the messages are to be dispatched to.
        :param msgs: a list of messages ordered with the most severe first.
                     Each list element is a tuple with ``(ID, text, severity)``

        :returns: a tuple containing 5 values:

                  * The formatted SMS.
                  * A list of IDs of sent messages.
                  * A list of IDs of ignored messages.
                  * A boolean which is true for success and false for failure.
                  * An integer which is the sending ID if available or 0
                    otherwise.

        """
        raise NotImplementedError()

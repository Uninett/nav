#
# Copyright (C) 2006, 2016 Uninett AS
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
"""The smsd dispatcher for Gammu.

This dispatcher takes care of all communication between smsd and Gammu. Gammu
is used to send SMS messages via a cell phone connected to the server with a
serial cable, USB cable, IR or Bluetooth. See http://www.gammu.org/ for more
information.

Depends on python-gammu.

"""

from nav.smsd.dispatcher import (Dispatcher, PermanentDispatcherError,
                                 DispatcherError)

from django.utils import six

try:
    import gammu
except ImportError as error:
    raise PermanentDispatcherError(
          'python-gammu not installed or misconfigured.')


class GammuDispatcher(Dispatcher):
    """The smsd dispatcher for Gammu."""

    def __init__(self, _config):
        """Constructor."""

        # Call mother's init
        Dispatcher.__init__(self)

    def sendsms(self, phone, msgs):
        """
        Send SMS using Gammu.

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
        sms = decode_sms_to_unicode(sms)

        # We got a python-gammu binding :-)
        sm = gammu.StateMachine()

        try:
            # Typically ~root/.gammurc or ~$NAV_USER/.gammurc
            sm.ReadConfig()
        except IOError as error:
            raise PermanentDispatcherError(error)

        try:
            # Fails if e.g. phone is not connected
            # See http://www.gammu.org/wiki/index.php?title=Gammu:Error_Codes
            # for complete list of errors fetched here
            sm.Init()
        except gammu.GSMError as error:
            raise PermanentDispatcherError(
                  "GSM %s error %d: %s" % (error.args[0]['Where'],
                                           error.args[0]['Code'],
                                           error.args[0]['Text'])
            )

        message = {
            'Text': sms,
            'SMSC': {'Location': 1},
            'Number': phone
        }

        try:
            # Tested with:
            # - Nokia 6610, Tekram IRmate 410U and Gammu 1.07.00
            # - Sony Ericsson K310, USB cable, Gammu 1.06.00, python-gammu 0.13
            smsid = sm.SendSMS(message)
        except gammu.GSMError as error:
            raise DispatcherError("GSM %s error %d: %s" % (error.args[0]['Where'],
                                                           error.args[0]['Code'],
                                                           error.args[0]['Text']))

        if isinstance(smsid, six.integer_types):
            result = True
        else:
            result = False

        return (sms, sent, ignored, result, smsid)


def decode_sms_to_unicode(sms):
    if isinstance(sms, six.text_type):
        return sms
    else:
        return sms.decode('utf-8')

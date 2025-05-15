#
# Copyright (C) 2006, 2018 Uninett AS
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
"""A dispatcher for Uninett's mail-to-SMS gateway.

This dispatcher sends SMS messages via Uninett's mail-to-SMS gateway. The
gateway accepts e-mails with the recipient's phone number in the subject and
the text message in the body. The mail must be sent from a uninett.no host,
so this is of little use for others, unless they have a similar interface.

"""

import smtplib

from django.core.mail import EmailMessage

from nav.smsd.dispatcher import Dispatcher, DispatcherError


class UninettMailDispatcher(Dispatcher):
    """The smsd dispatcher for Uninett's mail-to-SMS gateway."""

    def __init__(self, config):
        """Constructor"""
        super(UninettMailDispatcher, self).__init__()

        try:
            # Mail address for gateway
            self.mailaddr = config['mailaddr']
        except KeyError as error:
            raise DispatcherError("Config option not found: %s" % error)

    def sendsms(self, phone, msgs):
        """
        Sends SMS using Uninett's mail-to-SMS gateway.

        :param phone: The phone number the messages are to be dispatched to.
        :param msgs: A list of message strings, ordered by descending severity.
                     Each message is a tuple with ID, text and severity of the
                     message.

        :returns: A five-tuple containing these values:
                  - The formatted SMS.
                  - A list of IDs of sent messages.
                  - A list of IDs of ignored messages.
                  - A boolean which is true for success and false for failure.
                  - An integer which is the sending ID, if available or 0
                    otherwise.
        """
        (sms, sent, ignored) = self.formatsms(msgs)

        try:
            message = EmailMessage(
                subject="sms {}".format(phone), to=[self.mailaddr], body=sms
            )
            message.send(fail_silently=False)
        except smtplib.SMTPException as error:
            raise DispatcherError("SMTP error: %s" % error)

        result = True
        smsid = 0
        return sms, sent, ignored, result, smsid

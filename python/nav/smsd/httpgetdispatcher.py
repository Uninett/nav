# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2019 Uninett AS
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
"""Dispatcher for external HTTP service.

This dispatcher sends SMS via a webserver accepting information sent trough a
HTTP GET request.

It requires parameters for username, passord and group, in addition to
reciever and SMS message.

It has been made for working with the SMS gateway used by the University of
Oslo, but could be useful for other similar solutions.

"""

import urllib
from django.utils.six.moves.urllib.request import urlopen
from django.utils.six.moves.urllib.error import HTTPError
from nav.smsd.dispatcher import Dispatcher, DispatcherError


class HttpGetDispatcher(Dispatcher):
    """The smsd dispatcher for posting via a HTTP server."""

    def __init__(self, config):
        """Constructor."""

        # Call mother's init
        Dispatcher.__init__(self)

        # Get config
        try:
            # Remote address for gateway
            self.url = config['url']
        except KeyError as error:
            raise DispatcherError("Config option not found: %s" % error)

    def sendsms(self, phone, msgs):
        """
        Send SMS by calling the assigned URL with appropriate parametres

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
        sms = urllib.quote_plus(sms)

        # Format HTTP GET request
        get_data = {'phone': phone, 'sms': sms}
        url = self.url % get_data

        # Send SMS
        try:
            urlopen(url)
            result = True
        except HTTPError as e:
            self.logger.error('HTTP error: <%s>: %s (%s).' %
                              (e.url, e.msg, e.code))
            result = False

        smsid = 0
        self.logger.debug('HttpGetDispatcher response: %s, %s, %s, %s, %s',
                          sms, sent, ignored, result, smsid)
        return (sms, sent, ignored, result, smsid)

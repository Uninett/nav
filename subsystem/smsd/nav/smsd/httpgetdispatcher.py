#! /usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2007 USIT, UiO
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
Dispatcher for external HTTP service.

This dispatcher sends SMS via a webserver accepting information sent trough a
HTTP GET request.

It requires parameters for username, passord and group, in addition to
reciever and SMS message.

It has been made for working with the SMS gateway used by the University of
Oslo, but could be useful for other similar solutions.

"""

__copyright__ = "Copyright 2007 USIT, UiO"
__license__ = "GPL"
__author__ = "Arne Meyer Vedø-Hansen (amveha@ulrik.uio.no), Asbjørn Prøis (asbjorp@usit.uio.no), Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"

import urllib
import urllib2
from nav.smsd.dispatcher import *

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
        except KeyError, error:
            raise DispatcherError, "Config option not found: %s" % error

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
        get_data = { 'phone': phone, 'sms': sms }
        url = self.url % get_data

        # Send SMS
	urllib2.HTTPError = HttpGetError
	try:
	    urllib2.urlopen(url)
	    result = True
	except HttpGetError, e:
	    self.logger.error('%s', e)
	    result = False

	smsid = 0
	self.logger.debug('HttpGetDispatcher response: %s, %s, %s, %s, %s',
                          sms, sent, ignored, result, smsid)
        return (sms, sent, ignored, result, smsid)

class HttpGetError(urllib2.HTTPError):
    def __init__(self, url, code, msg, hdrs, fp):
        self.url = url
        self.code = code
        self.msg = msg
        self.hdrs = hdrs
        self.fp = fp

    def __str__(self):
        return 'HTTP error: <%s>: %s (%s).' % (self.url, self.msg, self.code)


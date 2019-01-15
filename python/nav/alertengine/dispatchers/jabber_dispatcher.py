#! /usr/bin/env python
#
# Copyright (C) 2008, 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Plugin module for sending jabber alerts"""

import logging
import time
from threading import Thread
from time import sleep

from nav.errors import ConfigurationError
from nav.alertengine.dispatchers import Dispatcher, DispatcherException, \
    is_valid_email

_logger = logging.getLogger('nav.alertengine.dispatchers.jabber')

try:
    import xmpp
except ImportError as err:
    xmpp = None
    _logger.warning("Python xmpp module is not available, "
                    "jabber dispatching disabled (%s) ", err)


class Jabber(Dispatcher):
    """Jabber/XMPP dispatcher"""
    def __init__(self, *args, **kwargs):
        super(Jabber, self).__init__(*args, **kwargs)

        self.config = kwargs['config']
        self.ready = False
        self.jid = None
        self.client = None

        self.thread = Thread(target=self.thread_loop, args=[self.connect])
        self.thread.setDaemon(True)
        self.thread.start()

        count = 0

        while count < 10 and not self.ready:
            time.sleep(1)
            count += 1

        if not self.ready:
            raise Exception('Not ready in time')

    @staticmethod
    def presence_handler(connection, presence):
        """XMPP Presence handler"""
        who = str(presence.getFrom())
        typ = presence.getType()

        _logger.debug('presence_handler invoked for %s', presence)

        if typ == 'subscribe':
            connection.send(xmpp.Presence(who, 'subscribed'))
            connection.send(xmpp.Presence(who, 'subscribe'))

            _logger.debug('Sent subscription confirmation to %s', who)

        elif typ == 'unsubscribe':
            connection.send(xmpp.Presence(who, 'unsubscribed'))
            connection.send(xmpp.Presence(who, 'unsubscribe'))

            _logger.debug('Sent unsubscription confirmation to %s', who)

    @staticmethod
    def thread_loop(connect):
        """Main thread loop for XMPP client connection"""
        _logger.debug('starting thread loop')

        client = connect()

        # Put thread to sleep waiting for flag to be set.
        while True:
            client.Process(1)
            _logger.debug('thread sleeping 120 seconds')
            sleep(120)
        _logger.debug('stopping thread loop')

    def connect(self):
        """Connects to the XMPP server"""
        try:
            self.jid = xmpp.protocol.JID(self.config['jid'])
        except KeyError:
            raise ConfigurationError('Jabber config is missing "jid" entry')

        self.client = xmpp.Client(self.jid.getDomain())

        con = self.client.connect()

        if not con:
            raise DispatcherException('Could not connect to jabber server')

        _logger.debug('Connected with %s', con)

        try:
            auth = self.client.auth(
                self.jid.getNode(), self.config['password'],
                resource=self.jid.getResource() or 'alertengine')
        except KeyError:
            raise ConfigurationError(
                'Jabber config is missing "password" entry')

        if not auth:
            raise DispatcherException(
                'Could not authenticate with jabber server')

        self.client.RegisterHandler('presence', self.presence_handler)
        self.client.sendInitPresence()

        self.ready = True

        return self.client

    def send(self, address, alert, language='en', retry=True,
             retry_reason=None):
        message = self.get_message(alert, language, 'jabber')

        if not self.client.isConnected():
            self.connect()

        try:
            ident = self.client.send(
                xmpp.protocol.Message(address.address, message, typ='chat'))
            _logger.debug('Sent message with jabber id %s', ident)
        except (xmpp.protocol.StreamError, IOError) as err:
            if retry:
                _logger.warning('Sending jabber message failed, retrying once')
                self.connect()
                self.send(address, alert, language,
                          retry=False, retry_reason=err)
            else:
                raise DispatcherException(
                    ("Couldn't send message due to: '%s', reason for retry: "
                     "'%s'") % (err, retry_reason))

    @staticmethod
    def is_valid_address(address):
        return is_valid_email(address)

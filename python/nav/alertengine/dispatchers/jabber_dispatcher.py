#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Plugin module for sending jabber alerts"""

import xmpp
import logging
import time
from threading import Thread
from time import sleep

from nav.errors import ConfigurationError
from nav.alertengine.dispatchers import dispatcher, DispatcherException

logger = logging.getLogger('nav.alertengine.dispatchers.jabber')

class jabber(dispatcher):
    def __init__(self, *args, **kwargs):
        self.config = kwargs['config'];
        self.ready = False

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
        who = str(presence.getFrom())
        type = presence.getType()

        logger.debug('presence_handler invoked for %s' % presence)

        if type == 'subscribe':
            connection.send(xmpp.Presence(to=who, type='subscribed'))
            connection.send(xmpp.Presence(to=who, type='subscribe'))

            logger.debug('Sent subscription confirmation to %s' % who)

        elif type == 'unsubscribe':
            connection.send(xmpp.Presence(to=who, type='unsubscribed'))
            connection.send(xmpp.Presence(to=who, type='unsubscribe'))

            logger.debug('Sent unsubscription confirmation to %s' % who)

    @staticmethod
    def thread_loop(connect):
        logger.debug('starting thread loop')

        client = connect()

        # Put thread to sleep waiting for flag to be set.
        while True:
            client.Process(1)
            logger.debug('thread sleeping 120 seconds')
            sleep(120)
        logger.debug('stopping thread loop')

    def connect(self):
        try:
            self.jid = xmpp.protocol.JID(self.config['jid'])
        except KeyError:
            raise ConfigurationError('Jabber config is missing "jid" entry')

        self.client = xmpp.Client(self.jid.getDomain())

        con = self.client.connect()

        if not con:
            raise DispatcherException('Could not connect to jabber server')

        logger.debug('Connected with %s' % con)

        try:
            auth = self.client.auth(self.jid.getNode(), self.config['password'], resource=self.jid.getResource() or 'alertengine')
        except KeyError:
            raise ConfigurationError('Jabber config is missing "password" entry')

        if not auth:
            raise DispatcherException('Could not authenticate with jabber server')

        self.client.RegisterHandler('presence', self.presence_handler)
        self.client.sendInitPresence()

        self.ready = True

        return self.client

    def send(self, address, alert, language='en', retry=True, retry_reason=None):
        message = self.get_message(alert, language, 'jabber')

        if not self.client.isConnected():
            self.connect()

        try:
            id = self.client.send(xmpp.protocol.Message(address.address, message, typ='chat'))
            logger.debug('Sent message with jabber id %s' % id)
        except (xmpp.protocol.StreamError, IOError), e:
            if retry:
                logger.warning('Sending jabber message failed, retrying once.')
                self.connect()
                self.send(address, alert, language, retry=False, retry_reason=e)
            else:
                raise DispatcherException("Couldn't send message due to: '%s', reason for retry: '%s'" % (e, retry_reason))

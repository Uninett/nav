#! /usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2008 UNINETT AS
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
# Author: Thomas Adamcik <thomas.adamcik@uninett.no>
#

"""Plugin module for sending jabber alerts"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"

import xmpp
import logging
import time
from threading import Thread
from time import sleep

from nav.alertengine.dispatchers import dispatcher, DispatcherException

logger = logging.getLogger('nav.alertengine.dispatchers.jabber')

class jabber(dispatcher):
    def __init__(self, *args, **kwargs):
        self.config = kwargs['config'];

        self.connect()

        self.thread = Thread(target=self.thread_loop, args=[self.get_client])
        self.thread.setDaemon(True)
        self.thread.start()

    def get_client(self):
        return self.client

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
    def thread_loop(get_client):
        logger.debug('starting thread loop')

        # Put thread to sleep waiting for flag to be set.
        while True:
            get_client().Process(1)
            logger.debug('thread sleeping 120 seconds')
            sleep(120)
        logger.debug('stopping thread loop')

    def connect(self):
        self.jid = xmpp.protocol.JID(self.config['jid'])
        self.client = xmpp.Client(self.jid.getDomain())

        con = self.client.connect()

        if not con:
            raise DispatcherException('Could not connect to jabber server')

        logger.debug('Connected with %s' % con)

        auth = self.client.auth(self.jid.getNode(), self.config['password'], resource=self.jid.getResource() or 'alertengine')

        if not auth:
            raise DispatcherException('Could not authenticate with jabber server')

        self.client.RegisterHandler('presence',self.presence_handler)
        self.client.sendInitPresence()

    def send(self, address, alert, language='en', type='unknown', retry=True, retry_reason=None):
        message = alert.messages.get(language=language, type='jabber')

        if not self.client.isConnected():
            self.connect()

        try:
            id = self.client.send(xmpp.protocol.Message(address.address, message.message, typ='chat'))
            logger.info('alert %d sent by jabber to %s due to %s subscription' % (alert.id, address.address, type))
            logger.debug('Sent message with jabber id %s' % id)
        except (xmpp.protocol.StreamError, IOError), e:
            if retry:
                logger.warn('Sending jabber message failed, retrying once.')
                self.connect()
                self.send(address, alert, language, type, False, e)
            else:
                raise DispatcherException("Couldn't send message due to: '%s', reason for retry: '%s'" % (e, retry_reason))

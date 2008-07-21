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

"""FIXME"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"

import xmpp
import logging
import time

from nav.alertengine.dispatchers import dispatcher, DispatcherException

logger = logging.getLogger('nav.alertengine.dispatchers.jabber')

class jabber(dispatcher):
    def __init__(self, *args, **kwargs):
        self.config = kwargs['config'];

        self.connect()

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

    def send(self, address, alert, language='en', type='unknown', retry=True, retry_reason=None):
        message = alert.messages.get(language=language, type='email')

        if not self.client.isConnected():
            self.connect()

        try:
            self.client.Process(1)
            id = self.client.send(xmpp.protocol.Message(address.address, message.message, typ='chat'))
            logger.debug('Send message with jabber id %s' % id)
        except (xmpp.protocol.StreamError, IOError), e:
            if retry:
                logger.warn('Retrying...')
                self.connect()
                self.send(address, alert, language, type, False, e)
            else:
                raise DispatcherException("Couldn't send message due to: '%s', reason for retry: '%s'" % (e, retry_reason))

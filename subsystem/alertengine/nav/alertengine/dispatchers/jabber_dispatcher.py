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

        self.jid = xmpp.protocol.JID(self.config['jid'])
        self.client = xmpp.Client(self.jid.getDomain())

        self.connect()

    def connect(self):
        self.con = self.client.connect()

        if not self.con:
            raise DispatcherException('Could not connect to jabber server')

        logger.debug('Connected with %s' % self.con)

        auth = self.client.auth(self.jid.getNode(), self.config['password'], resource=self.jid.getResource())

        if not auth:
            self.con = None
            raise DispatcherException('Could not authenticate with jabber server')

    def send(self, address, alert, language='en', type='unknown'):
        message = alert.messages.get(language=language, type='email')

        if not self.con:
            self.connect()

        try:
            id = self.client.send(xmpp.protocol.Message(address.address, message.message, typ='chat'))
            logger.debug('Send message with jabber id %s' % id)
        except xmpp.protocol.StreamError, e:
            raise DispatcherException('Jabber stream error occured: %s' % e)

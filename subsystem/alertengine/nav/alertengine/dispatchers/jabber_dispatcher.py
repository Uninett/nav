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

"""
"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"


import sys
import logging
from jabber import jabber as jabber_ext, xmlstream
from time import sleep
from threading import Thread, Lock

from nav.alertengine.dispatchers import dispatcher

logger = logging.getLogger('nav.alertengine.jabber')

class jabber(dispatcher):
    con = None

    def __init__(self, config={}):
        self.config = config
        self.lock = Lock()
        self.connect()

    def connect(self):
        server = self.config.get('server')
        password = self.config.get('password')
        username = self.config.get('username', 'nav')
        resource = self.config.get('resource', 'default')
        port = self.config.get('port', 5223)


        # FIXME ssl
        con = jabber_ext.Client(host=server, log=sys.stderr,
                            port=port, connection=xmlstream.TCP_SSL)

        con.registerHandler('presence', self.presence_handler)

        try:
            con.connect()
        except IOError, e:
            # FIXME handle reconnect?
            logger.critical("Couldn't connect: %s" % e)
        else:
            logger.info('Connected to %s' % server)

        if con.auth(username, password, resource):
            logger.info('Logged in as %s to server %s' % (username, server))
        else:
            # FIXME handle reconnect?
            logger.critical('Could not log in: %s %s' % (con.lastErr, con.lastErrCode))

        con.sendInitPresence()
        con.requestRoster()

        self.con = con

        # Start up process_loop thread, run as a deamon so that the thread dies when
        # the parent dies.
        # FIXME we should probably get rid of the thread upon reconnection...
        self.thread = Thread(target=self.process_loop)
        self.thread.setDaemon(1)
        self.thread.start()

    @staticmethod
    def presence_handler(con, presence):
        '''Handels presence changes, only cares about subscribe and unsubscribe'''
        who = str(presence.getFrom())
        type = presence.getType()

        if type == 'subscribe':
            con.send(jabber_ext.Presence(to=who, type='subscribed'))
        elif type == 'unsubscribe':
            con.send(jabber_ext.Presence(to=who, type='unsubscribed'))

    def process_loop(self):
        '''Checks for jabber events, uses lock tp prevent checking and sending at the same time'''
        logger.debug('Starting process_loop thread')
        while self.lock.acquire():
            try:
                self.con.process(5)
            except Exception, e:
                logger.debug('Something went wrong in our thread: %s' % e)
                break
            self.lock.release()
            sleep(5)
        self.lock.release()

    def send(self, address, alert, language='en', type='unknown'):
        message = alert.messages.get(language=language, type='email')
        # Get the lock and the send any messages
        if self.lock.acquire():
            self.con.send(jabber_ext.Message(address.address, message.message, type='chat'))
            self.lock.release()


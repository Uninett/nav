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
from jabber import jabber, xmlstream
from time import sleep
from threading import Thread, Lock

def presence_handler(con, presence):
    '''Handels presence changes, only cares about subscribe and unsubscribe'''
    who = str(presence.getFrom())
    type = presence.getType()

    if type == 'subscribe':
        con.send(jabber.Presence(to=who, type='subscribed'))
    elif type == 'unsubscribe':
        con.send(jabber.Presence(to=who, type='unsubscribed'))

def process_loop(con, lock):
    '''Checks for jabber events, uses lock tp prevent checking and sending at the same time'''
    logger.debug('Starting process_loop thread')
    while lock.acquire():
        con.process(1)
        lock.release()
        sleep(5)

logger = logging.getLogger('nav.alertengine.jabber')

# FIXME settings
server = 'jabber.org'
username = 'nav-test'
password = 'test'
resource = 'default'

con = jabber.Client(host=server, log=sys.stderr,
                    port=5223, connection=xmlstream.TCP_SSL)
con.registerHandler('presence',presence_handler)

try:
    con.connect()
except IOError, e:
    logger.critical("Couldn't connect: %s" % e)
    sys.exit(0)
else:
    print logger.info('Connected to %s' % server)

if con.auth(username,password,resource):
    print logger.info('Logged in as %s to server %s' % (username, server))
else:
    logger.critical('Could not log in: %s %s' % (con.lastErr, con.lastErrCode))
    sys.exit(1)

con.sendInitPresence()
con.requestRoster()

# Start up process_loop thread, run as a deamon so that the thread dies when
# the parent dies.
lock = Lock()
process_thread = Thread(target=process_loop, args=(con,lock))
process_thread.setDaemon(1)
process_thread.start()

def send(address, alert, language='en', type='unknown'):
    message = alert.messages.get(language=language, type='email')
    # Get the lock and the send any messages
    if lock.acquire():
        con.send(jabber.Message(address.address, message.message, type='chat'))
        lock.release()


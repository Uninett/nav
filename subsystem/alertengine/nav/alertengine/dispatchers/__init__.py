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
The dispatchers package contains all the methods that alertengine can use to
send out alerts. Adding new messaging channels is a simple matter of writting
a new subclass of ``dispatcher'' overriding send with the following:

    def send(self, address, alert, language='en'):

address - the alertaddress object that is "sending" the alert
  alert - the alertqueue object that we want to send out an notification about

The address to send to is `address.address`. To get the message we want to send
simply call `alert.messages.get(language=language, type='your_message_type')`

For your dispatchers logging please use `logging.getlogger('nav.alertengine.dispatchers.your_dispatcher')`
and try to use sensible log messages, look at the modules that ship with NAV
for examples.
"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"

import logging
import os

from nav.models.event import AlertQueueMessage

logger = logging.getLogger('nav.alertengine.dispatchers')

class dispatcher:
    '''Base class for dispatchers'''

    def __init__(self, config={}):
        self.config = config

    def send(alert, address, language='en'):
        raise NotImplementedError

    def get_message(self, alert, language, message_type):
        try:
            return alert.messages.get(language=language, type=message_type).message
        except AlertQueueMessage.DoesNotExist:
            return self.get_fallback_message(alert, language, message_type)

    def get_fallback_message(self, alert, language, message_type):
        # Try using longest message in english
        messages = list(alert.messages.filter(language='en'))
        messages.sort(key=lambda m: len(m.message))

        if messages:
            return messages[-1].message
        else:
            # Fallback to any message
            messages = list(alert.messages.all())
            messages.sort(key=lambda m: len(m.message))

            if messages:
                return messages[-1].message

        return "%s: No '%s' message for %d" % (alert.netbox, message_type, alert.id)

class DispatcherException(Exception):
    '''Raised when alert could not be sent temporarily and sending should be
       retried'''
    pass

class FatalDispatcherException(DispatcherException):
    '''Raised when alert could not be sent and further attempts at sending
       should be ditched'''
    pass

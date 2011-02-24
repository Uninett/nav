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

import logging
import os
from django.forms import EmailField, ValidationError

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

    @staticmethod
    def is_valid_address(address):
        raise NotImplementedError

class DispatcherException(Exception):
    '''Raised when alert could not be sent temporarily and sending should be
       retried'''
    pass

class FatalDispatcherException(DispatcherException):
    '''Raised when alert could not be sent and further attempts at sending
       should be ditched'''
    pass

def is_valid_email(address):
    # FIXME In Django 1.2 we can use validators
    field = EmailField()
    try:
        field.clean(address)
    except ValidationError, e:
        return False
    return True

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

import logging

from nav.models.profiles import SMSQueue
from nav.alertengine.dispatchers import dispatcher, DispatcherException

logger = logging.getLogger('nav.alertengine.dispatchers.sms')

class sms(dispatcher):
    '''Simple dispatcher that adds alerts to SMSQueue for smsd to handle'''

    def send(self, address, alert, language='en', type='unknown'):
        if address.account.has_perm('alerttype', 'sms'):
            message = alert.messages.get(language=language, type='sms').message

            if not address.DEBUG_MODE:
                SMSQueue.objects.create(account=address.account, message=message, severity=alert.severity, phone=address.address)
                logger.info('alert %d: added message to sms queue for user %s at %s due to %s subscription' % (alert.id, address.account, address.address, type))
            else:
                logger.info('alert %d: In testing mode, would have added message to sms queue for user %s at %s due to %s subscription' % (alert.id, address.account, address.address, type))
        else:
            logger.warn('alert %d: %s does not have SMS priveleges' % (alert.id, address.account))


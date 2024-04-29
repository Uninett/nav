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
"""SMS queue alert dispatcher implementation"""

import logging

from django.db import DatabaseError, IntegrityError

from nav.models.profiles import SMSQueue
from nav.models.event import AlertQueueMessage
from nav.alertengine.dispatchers import Dispatcher, DispatcherException

_logger = logging.getLogger('nav.alertengine.dispatchers.sms')


class Sms(Dispatcher):
    """Simple dispatcher that adds alerts to SMSQueue for smsd to handle"""

    def send(self, address, alert, language='en'):
        if address.account.has_perm('alert_by', 'sms'):
            message = self.get_message(alert, language, 'sms')

            if not address.DEBUG_MODE:
                try:
                    SMSQueue.objects.create(
                        account=address.account,
                        message=message,
                        severity=alert.severity,
                        phone=address.address,
                    )
                except (DatabaseError, IntegrityError) as err:
                    raise DispatcherException("Couldn't add sms to queue: %s" % err)
            else:
                _logger.debug(
                    'alert %d: In testing mode, would have added '
                    'message to sms queue for user %s at %s',
                    alert.id,
                    address.account,
                    address.address,
                )
        else:
            _logger.warning(
                'alert %d: %s does not have SMS privileges', alert.id, address.account
            )

    def get_fallback_message(self, alert, language, message_type):
        try:
            return alert.messages.get(language='en', type=message_type).message
        except AlertQueueMessage.DoesNotExist:
            pass

        try:
            message = alert.messages.get(language='en', type='email').message
            return message.split('\n')[0]
        except AlertQueueMessage.DoesNotExist:
            pass

        return '%s: No sms message for %d' % (alert.netbox, alert.id)

    @staticmethod
    def is_valid_address(address):
        if address.startswith("+"):
            return address[1:].isdigit()
        return address.isdigit()

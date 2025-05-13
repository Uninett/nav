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
"""E-Mail dispatcher implementation"""

import logging
from smtplib import SMTPException, SMTPRecipientsRefused

from django.core.mail import EmailMessage

from nav.alertengine.dispatchers import (
    Dispatcher,
    DispatcherException,
    FatalDispatcherException,
    is_valid_email,
)

_logger = logging.getLogger('nav.alertengine.dispatchers.email')


class Email(Dispatcher):
    """E-Mail dispatcher"""

    def send(self, address, alert, language='en'):
        message = self.get_message(alert, language, 'email')

        # Extract the subject
        subject = message.splitlines(1)[0].lstrip('Subject:').strip()
        # Remove the subject line
        message = '\n'.join(message.splitlines()[1:])

        headers = {
            'X-NAV-Alert-ID': alert.id,
            'X-NAV-Alert-Subsystem': alert.source,
            'X-NAV-Alert-Netbox': alert.netbox,
            'X-NAV-Alert-Device': alert.device,
            'X-NAV-Alert-SubID': alert.subid,
            'X-NAV-Event-Type': alert.event_type_id,
            'X-NAV-Alert-State': alert.get_state_display(),
            'X-NAV-Alert-History-ID': alert.history_id,
        }

        try:
            if not address.DEBUG_MODE:
                email = EmailMessage(
                    subject=subject, body=message, to=[address.address], headers=headers
                )
                email.send(fail_silently=False)
            else:
                _logger.debug(
                    'alert %d: In testing mode, would have sent email to %s',
                    alert.id,
                    address.address,
                )

        except SMTPException as err:
            msg = 'Could not send email: %s" ' % err
            if isinstance(err, SMTPRecipientsRefused) or (
                hasattr(err, "smtp_code") and str(err.smtp_code).startswith('5')
            ):
                raise FatalDispatcherException(msg)

            # Reraise as DispatcherException so that we can catch it further up
            raise DispatcherException(msg)

    @staticmethod
    def is_valid_address(address):
        return is_valid_email(address)

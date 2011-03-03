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
"""

import logging
from smtplib import SMTPException, SMTPRecipientsRefused

from django.core.mail import EmailMessage

from nav.alertengine.dispatchers import dispatcher, DispatcherException, \
FatalDispatcherException, is_valid_email

logger = logging.getLogger('nav.alertengine.dispatchers.email')

class email(dispatcher):
    def send(self, address, alert, language='en'):
        message = self.get_message(alert, language, 'email')

        # Extract the subject
        subject = message.splitlines(1)[0].lstrip('Subject:').strip()
        # Remove the subject line
        message = '\n'.join(message.splitlines()[1:])

        headers = {
            'X-NAV-alert-netbox': alert.netbox,
            'X-NAV-alert-device': alert.device,
            'X-NAV-alert-subsystem': alert.source,
        }

        try:
            if not address.DEBUG_MODE:
                email = EmailMessage(subject=subject, body=message, to=[address.address])
                email.send(fail_silently=False)
            else:
                logger.debug('alert %d: In testing mode, would have sent email to %s' % (alert.id, address.address))

        except SMTPException, e:
            if isinstance(e, SMTPRecipientsRefused) or \
                (hasattr(e, "smtp_code") and str(e.smtp_code).startswith('5')):
                raise FatalDispatcherException('Could not send email: %s" ' % e)
            # Reraise as DispatcherException so that we can catch it further up
            raise DispatcherException('Could not send email: %s' % e)

    @staticmethod
    def is_valid_address(address):
        return is_valid_email(address)

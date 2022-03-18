#
# Copyright (C) 2015-2020 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A sender for slack messages"""

import json
import time

from urllib.request import Request, urlopen
from urllib.error import HTTPError

from nav.alertengine.dispatchers import Dispatcher, DispatcherException

HTTP_TOO_MANY_REQUESTS = 429
FAILURE_BACKOFF = 25  # seconds


class Slack(Dispatcher):
    """Dispatch messages to Slack"""

    _failures = {}

    def __init__(self, *args, **kwargs):
        super(Slack, self).__init__(*args, **kwargs)

        self.config = kwargs.get('config')
        self.username = self.config.get('username')
        self.channel = self.config.get('channel')
        self.emoji = self.config.get('emoji')
        self.verify = self.config.get('verify', True)

    def send(self, address, alert, language='en'):
        """Send a message to Slack"""
        if self._is_still_backing_off_for(address.address):
            raise DispatcherException(
                "Refusing to send Slack alert until backoff period has expired"
            )

        params = {
            'text': alert.messages.get(language=language, type='sms').message,
            'username': self.username,
            'channel': self.channel,
            'icon_emoji': self.emoji,
        }
        payload = json.dumps(params)
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        request = Request(
            address.address, payload, {'Content-Type': 'application/json'}
        )

        try:
            urlopen(request)
        except HTTPError as error:
            if error.code == HTTP_TOO_MANY_REQUESTS:
                self._register_failure_for(address.address)
                raise DispatcherException(
                    "Slack complained there were too many requests; need to back off"
                )
            else:
                raise

    def _register_failure_for(self, address):
        """Register address as an endpoint failing with TOO MANY REQUESTS errors"""
        self._failures[address] = time.time()

    def _is_still_backing_off_for(self, address):
        """Returns True if FAILURE_BACKOFF seconds still haven't passed since the
        endpoint at address last returned a TOO MANY REQUESTS error.
        """
        time_passed = time.time() - self._failures.get(address, 0)
        return time_passed < FAILURE_BACKOFF

    @staticmethod
    def is_valid_address(address):
        return True

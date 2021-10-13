"""A sender for slack messages"""

import json
import time

import six
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.error import HTTPError

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
        if isinstance(payload, six.text_type):
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

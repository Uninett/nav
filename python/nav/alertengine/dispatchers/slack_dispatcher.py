"""A sender for slack messages"""

import json
import urllib2

from nav.alertengine.dispatchers import Dispatcher


class Slack(Dispatcher):
    """Dispatch messages to Slack"""
    def __init__(self, *args, **kwargs):
        super(Slack, self).__init__(*args, **kwargs)

        self.config = kwargs.get('config')
        self.username = self.config.get('username')
        self.channel = self.config.get('channel')
        self.emoji = self.config.get('emoji')
        self.verify = self.config.get('verify', True)

    def send(self, address, alert, language='en'):
        """Send a message to Slack"""
        params = {
            'text': alert.messages.get(language=language, type='sms').message,
            'username': self.username,
            'channel': self.channel,
            'icon_emoji': self.emoji
        }
        request = urllib2.Request(address.address, json.dumps(params),
                                  {'Content-Type': 'application/json'})
        urllib2.urlopen(request)

    @staticmethod
    def is_valid_address(address):
        return True

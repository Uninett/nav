"""A sender for slack messages"""

import json
import requests

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
        requests.post(address.address, data=json.dumps(params),
                      verify=self.verify)

    @staticmethod
    def is_valid_address(address):
        return True

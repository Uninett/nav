import pickle

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class PickleSerializer:
    """
    Simple wrapper around pickle to be used in signing.dumps()/loads() and
    cache backends.
    """

    def __init__(self, protocol=None):
        if settings.SESSION_ENGINE == 'django.contrib.sessions.backends.signed_cookies':
            raise ImproperlyConfigured(
                "PickleSerializer cannot be used with signed_cookies SESSION_ENGINE"
            )
        self.protocol = pickle.HIGHEST_PROTOCOL if protocol is None else protocol

    def dumps(self, obj):
        return pickle.dumps(obj, self.protocol)

    def loads(self, data):
        return pickle.loads(data)

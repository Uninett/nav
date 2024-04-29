import pickle

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class PickleSerializer:
    """
    Simple wrapper around pickle to be used for serializing data to be put in
    cookies.

    This was vendored from the version found in Django 4.2. JSONSerializer has
    been the default in Django since 1.6, deprecated since 4.1 and purged from
    the codebase since 5.0. What Django did not provide is a migration path:
    a test showed that any access of a cookie after the serializer had been
    changed lead to a rather useless exception.

    PickleSerializer was removed due to it being danegerous in the
    signed_cookie session backend. NAV doesn't use that see we can keep the old
    serializer.

    Changes from the original: A deprecation warning has been removed and
    a check that it is not used with the signed_cookie session backend has been
    added.
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

#
# Copyright (C) 2018 Uninett AS
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
"""
Provides a common root package for the NAV python library.
"""

import threading
import time
import warnings

# Ignore stupid warnings about psycopg2-binary package, they're of no concern to us
warnings.filterwarnings("ignore", category=UserWarning, module='psycopg2')


class ObjectCache(dict):
    """An dictionary for caching objects.

    Mostly used for database connection pooling in NAV.

    """

    def __init__(self):
        super(ObjectCache, self).__init__()
        self._lock = threading.RLock()

    def __setitem__(self, key, item):
        with self._lock:
            if key in self:
                # A duplicate insert means the caller lost a race to another
                # thread. Disposing of the redundant object (e.g. closing a
                # database connection) is the caller's responsibility, not the
                # cache's -- this keeps ObjectCache free of any knowledge about
                # what it stores.
                raise CacheError(
                    "An object keyed %r is already stored in the cache" % (key,)
                )

            super(ObjectCache, self).__setitem__(key, item)
            item.cache = self

    def __delitem__(self, key):
        with self._lock:
            self[key].cache = None
            super(ObjectCache, self).__delitem__(key)

    def clear(self):
        """Removes all objects from the cache in a thread-safe manner."""
        with self._lock:
            for item in list(self.values()):
                item.cache = None
            super(ObjectCache, self).clear()

    def cache(self, item):
        """Caches the item, which should be a CacheableObject instance"""
        with self._lock:
            self[item.key] = item

    def invalidate(self):
        """Removes all invalid objects from the cache, and returns the
        number of objects removed.

        """
        # is_invalid() may perform network I/O (a database ping), so evaluate it
        # on a snapshot taken outside the lock; only the actual mutations are
        # locked, to avoid serializing every caller behind a slow ping.
        with self._lock:
            items = list(self.items())

        count = 0
        for key, item in items:
            if item.is_invalid():
                with self._lock:
                    # The entry may have been removed or replaced while we were
                    # unlocked; only delete it if it is still the same object.
                    if self.get(key) is item:
                        super(ObjectCache, self).__delitem__(key)
                        item.cache = None
                        count += 1
        return count

    def refresh(self):
        """Refreshes all invalid objects in the cache, and returns the
        number of objects refreshed.

        """
        # Like invalidate(), refresh() may block on I/O per item, so it operates
        # on a snapshot taken under the lock rather than holding it throughout.
        with self._lock:
            items = list(self.values())

        count = 0
        for item in items:
            if item.is_invalid() and item.refresh():
                count += 1
        return count


class CacheableObject(object):
    """
    A simple class to wrap objects for 'caching'.  It contains the
    object reference and the time the object was loaded.
    """

    def __init__(self, object_=None):
        self.object = object_
        self._cache = None
        self.cache_time = None
        self.key = str(object_)

    def __setattr__(self, name, item):
        if name == 'cache':
            if self._cache is not None and item is not None:
                raise CacheError("%s is already cached" % repr(self))
            elif item is not None:
                self._cache = item
                self.cache_time = time.time()
            else:
                self._cache = None
                self.cache_time = None
        else:
            super(CacheableObject, self).__setattr__(name, item)

    def __getattr__(self, name):
        if name == 'cache':
            return self._cache
        else:
            raise AttributeError(name)

    def is_cached(self):
        """Returns True if this object is stored in an ObjectCache dictionary"""
        return self._cache is not None

    def is_invalid(self):
        """Returns True if this object is too old (or invalid in some
        other way) to remain in the cache."""
        return False

    def refresh(self):
        """Refresh the object, if possible"""
        return False

    def invalidate(self):
        """Delete this object from the cache it is registered in."""
        if self.cache is not None and self.is_invalid():
            del self.cache[self.key]
            return True
        else:
            return False

    def age(self):
        """
        Return the cache age of this object.
        """
        if self.cache_time is None:
            return 0
        else:
            return time.time() - self.cache_time

    def __repr__(self):
        if self._cache is None:
            return "<%s uncached>" % repr(self.object)
        else:
            return "<%s cached at %s>" % (
                repr(self.object),
                time.asctime(time.localtime(self.cache_time)),
            )

    def __str__(self):
        return str(self.object)


class CacheError(Exception):
    """Generic error during an ObjectCache operation"""

    pass

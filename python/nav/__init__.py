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

import time
import warnings

# Ignore stupid warnings about psycopg2-binary package, they're of no concern to us
warnings.filterwarnings("ignore", category=UserWarning, module='psycopg2')


class ObjectCache(dict):
    """An dictionary for caching objects.

    Mostly used for database connection pooling in NAV.

    """

    def __setitem__(self, key, item):
        if key in self:
            raise CacheError("An object keyed %r is already stored in the cache" % key)

        super(ObjectCache, self).__setitem__(key, item)
        item.cache = self

    def __delitem__(self, key):
        self[key].cache = None
        super(ObjectCache, self).__delitem__(key)

    def cache(self, item):
        """Caches the item, which should be a CacheableObject instance"""
        self[item.key] = item

    def invalidate(self):
        """Removes all invalid objects from the cache, and returns the
        number of objects removed.

        """
        count = 0
        for key in list(self.keys()):
            if self[key].is_invalid():
                del self[key]
                count += 1
        return count

    def refresh(self):
        """Refreshes all invalid objects in the cache, and returns the
        number of objects refreshed.

        """
        count = 0
        for key in self.keys():
            if self[key].is_invalid() and self[key].refresh():
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

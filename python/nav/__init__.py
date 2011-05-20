#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
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

class ObjectCache(dict):
    def __setitem__(self, key, item):
        #if not isinstance(item, CacheableObject):
        if 0:
            raise ValueError("%r is not a CacheableObject instance" % item)
        else:
            if self.has_key(key):
                raise CacheError(
                    "An object keyed %r is already stored in the cache" % key)

            dict.__setitem__(self, key, item)
            item.cache = self

    def __delitem__(self, key):
        self[key].cache = None
        dict.__delitem__(self, key)

    def cache(self, item):
        """Caches the item, which must be a CacheableObject instance"""
        #if not isinstance(item, CacheableObject):
        if 0:
            raise ValueError("%r is not a CacheableObject instance" % item)
        else:
            self[item.key] = item

    def invalidate(self):
        """Removes all invalid objects from the cache, and returns the
        number of objects removed."""
        count = 0
        for key in self.keys():
            if self[key].isInvalid():
                del self[key]
                count += 1
        return count

    def refresh(self):
        """Refreshes all invalid objects in the cache, and returns the
        number of objects refreshed."""
        count = 0
        for key in self.keys():
            if self[key].isInvalid() and self[key].refresh():
                count += 1
        return count

class CacheableObject(object):
    """
    A simple class to wrap objects for 'caching'.  It contains the
    object reference and the time the object was loaded.
    """
    def __init__(self, object=None):
        self.object = object
        self._cache = None
        self.cacheTime = None
        self.key = str(object)

    def __setattr__(self, name, item):
        if name == 'cache':
            if (self._cache is not None and item is not None):
                raise CacheError, "%s is already cached" % repr(self)
            elif item is not None:
                self._cache = item
                self.cacheTime = time.time()
            else:
                self._cache = None
                self.cacheTime = None
        else:
            try:
                dict.__setattr__(self, name, item)
            except:
                self.__dict__[name] = item

    def __getattr__(self, name):
        if name == 'cache':
            return self._cache
        else:
            raise AttributeError, name

    def isCached(self):
        return self._cache is not None

    def isInvalid(self):
        """Returns True if this object is too old (or invalid in some
        other way) to remain in the cache."""
        return False

    def refresh(self):
        """Refresh the object, if possible"""
        return False

    def invalidate(self):
        """Delete this object from the cache it is registered in."""
        if self.cache is not None and self.isInvalid():
            del self.cache[self.key]
            return True
        else:
            return False

    def age(self):
        """
        Return the cache age of this object.
        """
        if self.cacheTime is None:
            return 0
        else:
            return time.time() - self.cacheTime

    def __repr__(self):
        if self._cache is None:
            return "<%s uncached>" % repr(self.object)
        else:
            return "<%s cached at %s>" % (
                repr(self.object),
                time.asctime(time.localtime(self.cacheTime)))

    def __str__(self):
        return self.object.__str__()

class CacheError(Exception):
    pass


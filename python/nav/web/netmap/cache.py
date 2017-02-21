#
# Copyright (C) 2017 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Cache utils for NetMap"""

from functools import wraps
from django.core.cache import cache

# TODO: This cache should be shared by all of NAV?
# TODO: This cache should be invalidated only when the topology is changed, which
# is somewhat rare, so set to a reasonable long time for now
CACHE_TIMEOUT = 60*60
# Data is collected every 5 minutes by NAV
TRAFFIC_CACHE_TIMEOUT = 5*60

# Cache model: Index traffic by location, then by traffic layer
def cache_traffic(layer, f):
    "Utility wrapper to cache get_traffic functions for layer 2/3"
    @wraps(f)
    def get_traffic(location_or_room_id):
        cache_key = _cache_key("traffic", location_or_room_id, layer)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        result = f(location_or_room_id)
        cache.set(cache_key, result, TRAFFIC_CACHE_TIMEOUT)
        return result
    return get_traffic

# Cache model: Index by topology layer
def cache_topology(layer, f):
    "Utility decorator to cache the topology graph of Netmap"
    @wraps(f)
    def get_traffic(*args, **kwargs):
        cache_key = _cache_key("topology", layer)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        result = f(*args, **kwargs)
        cache.set(cache_key, result, CACHE_TIMEOUT)
        return result
    return get_traffic

# TODO: Consider using a proper slug generator for this
def _cache_key(*args):
    """Construct a namespace cache key for storing/retrieving memory-cached data

    :param args: The elements which, when joined, set the index of the data

    Example:

    _cache_key("topology", "layer 3")
    => netmap:topology:layer3

    """
    args = (str(a).replace(' ', '-') for a in args)
    return 'netmap:' + ':'.join(args)

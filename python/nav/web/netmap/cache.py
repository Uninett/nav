#
# Copyright (C) 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
# TODO: This cache should be invalidated only when the topology is
# changed, which is somewhat rare, so set to a reasonable long time
# for now

CACHE_TIMEOUT = 60 * 60
# Data is collected every 5 minutes by NAV
TRAFFIC_CACHE_TIMEOUT = 5 * 60


def cache_exists(*args):
    key = _cache_key(*args)
    return cache.get(key) is not None


# Cache model: Index traffic by location, then by traffic layer
def cache_traffic(layer):
    "Utility wrapper to cache get_traffic functions for layer 2/3"

    def _decorator(func):
        @wraps(func)
        def get_traffic(location_or_room_id):
            cache_key = _cache_key("traffic", location_or_room_id, layer)
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            result = func(location_or_room_id)
            cache.set(cache_key, result, TRAFFIC_CACHE_TIMEOUT)
            return result

        return get_traffic

    return _decorator


# Cache model: Index by topology layer and view
def cache_topology(layer):
    "Utility decorator to cache the topology graph of Netmap"

    def _decorator(func):
        @wraps(func)
        def get_traffic(*args, **kwargs):
            view = kwargs["view"]
            if view is None:
                cache_key = _cache_key("topology", "global_view", layer)
            else:
                cache_key = _cache_key("topology", view.pk, layer)
            try:
                cached = cache.get(cache_key)
                if cached is not None:
                    return cached
            except ValueError:
                pass
            result = func(*args, **kwargs)
            cache.set(cache_key, result, CACHE_TIMEOUT)
            return result

        return get_traffic

    return _decorator


# Update all nodes at once to save a couple of hundred/thousand cache lookups
def update_cached_node_positions(viewid, layer, updated_nodes):
    cache_key = _cache_key("topology", viewid, layer)
    to_update = cache.get(cache_key)
    for node in updated_nodes:
        # If the node is new, it is easier just to make an early exit and
        # rebuild the whole topology
        if node["new_node"]:
            return invalidate_topology_cache(viewid, layer)
        # Otherwise, don't update nodes not cached in the topology
        if node["id"] not in to_update["nodes"]:
            continue
        diff = {"x": node["x"], "y": node["y"]}
        to_update["nodes"][node["id"]]["position"] = diff
    cache.set(cache_key, to_update, CACHE_TIMEOUT)


def invalidate_topology_cache(viewid, layer):
    "Resets the topology cache, prompting NAV to rebuild it"
    cache_key = _cache_key("topology", viewid, layer)
    cache.delete(cache_key)


# TODO: Consider using a proper slug generator for this
def _cache_key(*args):
    """Construct a namespace cache key for storing/retrieving memory-cached data

    :param args: The elements which, when joined, set the index of the data

    Example:

    _cache_key("topology", "layer 3")
    => netmap:topology:layer3

    """

    def stringify(thing):
        if isinstance(thing, bytes):
            return thing.decode('utf-8')
        else:
            return str(thing)

    args = (stringify(a).replace(' ', '-') for a in args)
    return 'netmap:' + ':'.join(args)

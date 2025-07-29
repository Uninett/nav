#
# Copyright (C) 2009, 2010, 2013-2015 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Data access for Geomap.

This module abstracts away all the horrendous queries needed to get data for
Geomap from the database, as well as the code for retrieving traffic data
from Graphite, and provides one simple function, get_data, which returns the
stuff we want.

Based on datacollector.py from the old Java-applet based Netmap.

"""

import logging

from django.core.cache import cache
from urllib.error import HTTPError

import nav
from nav.config import NAV_CONFIG
from nav.metrics.data import get_metric_average
from nav.metrics.errors import GraphiteUnreachableError
from nav.metrics.graphs import get_metric_meta
from nav.metrics.names import escape_metric_name
from nav.metrics.templates import (
    metric_path_for_interface,
    metric_path_for_cpu_load,
    metric_path_for_cpu_utilization,
)
from nav.web.geomap.utils import lazy_dict, subdict, is_nan
from nav.util import chunks

_logger = logging.getLogger(__name__)

_domain_suffix = NAV_CONFIG.get('DOMAIN_SUFFIX')


LAYER_3_QUERY = """
    SELECT DISTINCT ON (local_sysname, remote_sysname)
           sysname AS local_sysname,
           ifname AS local_interface,
           netbox.netboxid AS local_netboxid,
           interface_gwport.interfaceid AS local_gwportid,
           interface_gwport.interfaceid AS local_portid,
           NULL AS local_swportid,
           speed AS capacity,
           ifindex,
           conn.*, nettype, netident,
           3 AS layer, NULL AS remote_swportid, vlan.*
    FROM gwportprefix
    JOIN (
        SELECT DISTINCT ON (gwportprefix.prefixid)
               interfaceid AS remote_gwportid,
               interfaceid AS remote_portid,
               NULL AS remote_swportid,
               gwportprefix.prefixid,
               ifindex AS remote_ifindex,
               ifname AS remote_interface,
               sysname AS remote_sysname,
               speed AS remote_speed,
               netboxid AS remote_netboxid,
               room.position AS remote_position
        FROM interface_gwport
        JOIN netbox USING (netboxid)
        JOIN room USING (roomid)
        JOIN gwportprefix USING (interfaceid)
    ) AS conn USING (prefixid)
    JOIN interface_gwport USING (interfaceid)
    JOIN netbox USING (netboxid)
    JOIN room USING (roomid)
    LEFT JOIN prefix ON  (prefix.prefixid = gwportprefix.prefixid)
    LEFT JOIN vlan USING (vlanid)
    WHERE interface_gwport.interfaceid <> remote_gwportid
      AND vlan.nettype NOT IN ('static', 'lan')
      AND ((room.position[1] >= %s AND room.position[0] >= %s AND
            room.position[1] <= %s AND room.position[0] <= %s)
           OR
           (remote_position[1] >= %s AND remote_position[0] >= %s AND
            remote_position[1] <= %s AND remote_position[0] <= %s))
      AND length(lseg(room.position, remote_position)) >= %s
    ORDER BY sysname,remote_sysname, netaddr ASC, speed DESC
"""

LAYER_2_QUERY_1 = """
    SELECT DISTINCT ON (interface_swport.interfaceid)
    interface_gwport.interfaceid AS remote_gwportid,
    interface_gwport.interfaceid AS remote_portid,
    NULL AS remote_swportid,
    interface_gwport.speed AS capacity,
    interface_gwport.ifindex AS remote_ifindex,
    interface_gwport.ifname AS remote_interface,
    netbox.sysname AS remote_sysname,
    netbox.netboxid AS remote_netboxid,

    interface_swport.interfaceid AS local_swportid,
    interface_swport.interfaceid AS local_portid,
    NULL AS local_gwportid,
    interface_swport.ifname AS local_interface,
    swport_netbox.sysname AS local_sysname,
    swport_netbox.netboxid AS local_netboxid,
    interface_swport.ifindex AS ifindex,

    2 AS layer,
    nettype, netident,
    vlan.*

    FROM interface_gwport
     JOIN netbox ON (interface_gwport.netboxid=netbox.netboxid)

     LEFT JOIN gwportprefix
     ON (gwportprefix.interfaceid = interface_gwport.interfaceid)
     LEFT JOIN prefix ON  (prefix.prefixid = gwportprefix.prefixid)
     LEFT JOIN vlan USING (vlanid)

     JOIN interface_swport
     ON (interface_swport.interfaceid = interface_gwport.to_interfaceid)
     JOIN netbox AS swport_netbox
     ON (interface_swport.netboxid = swport_netbox.netboxid)

     JOIN room AS gwport_room ON (netbox.roomid = gwport_room.roomid)
     JOIN room AS swport_room ON (swport_netbox.roomid = swport_room.roomid)

     WHERE interface_gwport.to_interfaceid IS NOT NULL
       AND interface_gwport.to_interfaceid = interface_swport.interfaceid
       AND ((gwport_room.position[1] >= %s AND gwport_room.position[0] >= %s AND
             gwport_room.position[1] <= %s AND gwport_room.position[0] <= %s)
            OR
            (swport_room.position[1] >= %s AND swport_room.position[0] >= %s AND
             swport_room.position[1] <= %s AND swport_room.position[0] <= %s))
       AND length(lseg(gwport_room.position, swport_room.position)) >= %s
"""

LAYER_2_QUERY_2 = """
    SELECT DISTINCT ON (remote_sysname, local_sysname)
    interface_swport.interfaceid AS remote_swportid,
    interface_swport.interfaceid AS remote_portid,
    NULL AS remote_gwportid,
    interface_swport.speed AS capacity,
    interface_swport.ifindex AS remote_ifindex,
    interface_swport.ifname AS remote_interface,
    netbox.sysname AS remote_sysname,
    netbox.netboxid AS remote_netboxid,
    2 AS layer,
    foo.*,
    vlan.*

    FROM interface_swport
     JOIN netbox USING (netboxid)

     JOIN (

         SELECT
         interface_swport.interfaceid AS local_swportid,
         interface_swport.interfaceid AS local_portid,
         NULL AS local_gwportid,
         interface_swport.ifindex AS ifindex,
         interface_swport.ifname AS local_interface,
         netbox.sysname AS local_sysname,
         netbox.netboxid AS local_netboxid,
         room.position AS local_position

         FROM interface_swport
         JOIN netbox USING (netboxid)
         JOIN room USING (roomid)

       ) AS foo ON (foo.local_swportid = to_interfaceid)


    LEFT JOIN swportvlan ON (interface_swport.interfaceid = swportvlan.interfaceid)
    LEFT JOIN vlan USING (vlanid)

    JOIN room AS remote_room ON (netbox.roomid = remote_room.roomid)

    WHERE ((remote_room.position[1] >= %s AND remote_room.position[0] >= %s AND
            remote_room.position[1] <= %s AND remote_room.position[0] <= %s)
           OR
           (foo.local_position[1] >= %s AND foo.local_position[0] >= %s AND
            foo.local_position[1] <= %s AND foo.local_position[0] <= %s))
      AND length(lseg(remote_room.position, foo.local_position)) >= %s

    ORDER BY remote_sysname, local_sysname, interface_swport.speed DESC
"""

LAYER_2_QUERY_3 = """
    SELECT DISTINCT ON (remote_sysname, local_sysname)

    interface_swport.interfaceid AS remote_swportid,
    interface_swport.interfaceid AS remote_portid,
    interface_swport.ifindex AS remote_ifindex,
    interface_swport.ifname AS remote_interface,
    netbox.sysname AS remote_sysname,
    netbox.netboxid AS remote_netboxid,
    interface_swport.speed AS capacity,
    2 AS layer,
    conn.*,
    vlan.*,
    NULL AS remote_gwportid,
    NULL AS local_gwportid,
    NULL AS local_swportid,
    NULL AS local_portid,
    NULL AS local_interface

    FROM interface_swport
     JOIN netbox USING (netboxid)

     JOIN (
        SELECT
          netbox.sysname AS local_sysname,
          netbox.netboxid AS local_netboxid,
          room.position AS local_position
        FROM netbox
        JOIN room USING (roomid)
     ) AS conn ON (conn.local_netboxid = to_netboxid)

    LEFT JOIN swportvlan ON (interface_swport.interfaceid = swportvlan.interfaceid)
    LEFT JOIN vlan USING (vlanid)

    JOIN room AS remote_room ON (netbox.roomid = remote_room.roomid)

    WHERE ((remote_room.position[1] >= %s AND remote_room.position[0] >= %s AND
            remote_room.position[1] <= %s AND remote_room.position[0] <= %s)
           OR
           (conn.local_position[1] >= %s AND conn.local_position[0] >= %s AND
            conn.local_position[1] <= %s AND conn.local_position[0] <= %s))
      AND length(lseg(remote_room.position, conn.local_position)) >= %s

    ORDER BY remote_sysname, local_sysname, interface_swport.speed DESC
"""

QUERY_NETBOXES = """
    SELECT DISTINCT ON (netboxid)
           netbox.netboxid, netbox.sysname, netbox.ip,
           netbox.catid, netbox.up, netbox.roomid,
           type.descr AS type,
           location.descr AS location, room.descr AS room_descr,
           room.position[0] as lat, room.position[1] as lon
    FROM netbox
    LEFT JOIN room using (roomid)
    LEFT JOIN location USING (locationid)
    LEFT JOIN type USING (typeid)
    WHERE room.position IS NOT NULL
"""


def get_data(db_cursor, bounds, time_interval=None):
    """Reads data from database.

    Returns a pair of dictionaries (netboxes, connections).  netboxes
    contains a 'lazy dictionary' (see class lazy_dict in utils.py)
    with information for each netbox; connections contains two lazy
    dictionaries for each connection (one representing each end).
    (The reason for using lazy_dict is that this allows postponing
    reading of RRD files until we know it is necessary, while still
    keeping the code for reading them here).

    """

    if not db_cursor:
        raise nav.errors.GeneralException("No db-cursor given")

    bounds_list = [
        bounds['minLon'],
        bounds['minLat'],
        bounds['maxLon'],
        bounds['maxLat'],
    ]

    network_length_limit = 0

    network_query_args = bounds_list + bounds_list + [network_length_limit]

    if time_interval is None:
        time_interval = {'start': '-10min', 'end': 'now'}

    connections = {}

    db_cursor.execute(LAYER_3_QUERY, network_query_args)
    # Expect DictRows, but want to work with updateable dicts:
    results = [lazy_dict(row) for row in db_cursor.fetchall()]
    db_cursor.execute(LAYER_2_QUERY_1, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])
    db_cursor.execute(LAYER_2_QUERY_2, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])
    db_cursor.execute(LAYER_2_QUERY_3, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])

    for res in results:
        assert (
            res.get('remote_swportid', None) is not None
            or res.get('remote_gwportid', None) is not None
        )

    # Go through all the connections and add them to the connections
    # dictionary:
    for res in results:
        # Remove all data we are not interested in keeping:
        network_properties = [
            'capacity',
            'nettype',
            'netident',
            'layer',
            'vlan',
            'local_sysname',
            'local_netboxid',
            'local_interface',
            'local_portid',
            'local_gwportid',
            'local_swportid',
            'remote_sysname',
            'remote_netboxid',
            'remote_interface',
            'remote_portid',
            'remote_gwportid',
            'remote_swportid',
        ]
        res = subdict(res, network_properties)

        # Create a reversed version of the connection (this has all
        # remote_*/local_* swapped and has load data from the opposite
        # end):
        reverse = res.copy()
        reversable_properties = [
            'sysname',
            'netboxid',
            'interface',
            'portid',
            'gwportid',
            'swportid',
        ]
        for prop in reversable_properties:
            reverse.swap('local_' + prop, 'remote_' + prop)

        for d in res, reverse:
            d['load'] = (float('nan'), float('nan'))
            d['load_in'] = float('nan')
            d['load_out'] = float('nan')

        connection_id = "%s-%s" % (res['local_sysname'], res['remote_sysname'])
        connection_rid = "%s-%s" % (res['remote_sysname'], res['local_sysname'])
        res['id'] = connection_id
        reverse['id'] = connection_rid

        connection = {'forward': res, 'reverse': reverse}

        if connection_id not in connections and connection_rid not in connections:
            connections[connection_id] = connection
        else:
            for existing_id, existing_conn in connections.items():
                if existing_id in (connection_id, connection_rid):
                    existing_capacity = existing_conn["forward"]["capacity"] or 0
                    result_capacity = res["capacity"] or 0
                    if existing_capacity < result_capacity:
                        connections[existing_id] = connection

    db_cursor.execute(QUERY_NETBOXES)
    netboxes = [lazy_dict(row) for row in db_cursor.fetchall()]
    for netbox in netboxes:
        netbox['load'] = float('nan')
        netbox['real_sysname'] = netbox['sysname']
        if _domain_suffix:
            netbox['sysname'] = netbox['sysname'].removesuffix(_domain_suffix)

    return netboxes, connections


# TRAFFIC DATA

MEGABIT = 1e6
METRIC_CHUNK_SIZE = 500  # number of metrics to ask for in a single request
CACHE_TIMEOUT = 5 * 60  # 5 minutes


def get_cached_multiple_link_load(items, time_interval):
    """Cached version of get_multiple_link_load()"""
    item_map = {k: _cache_key(k, time_interval) for k in items.keys()}
    # cache lookup
    cached = cache.get_many(item_map.values())
    _logger.debug(
        "get_cached_multiple_link_load: got %d/%d values from cache (%r)",
        len(cached),
        len(items),
        time_interval,
    )

    # retrieve data for cache misses
    misses = {k: v for k, v in items.items() if item_map[k] not in cached}
    if misses:
        get_multiple_link_load(misses, time_interval)

    # set data from cache
    reverse_item_map = {v: k for k, v in item_map.items()}
    for cache_key, value in cached.items():
        key = reverse_item_map[cache_key]
        properties = items[key]
        properties['load_in'], properties['load_out'] = value

    # add new data to cache
    missed_data = {
        item_map[key]: (properties['load_in'], properties['load_out'])
        for key, properties in misses.items()
    }
    _logger.debug("get_cached_multiple_link_load: caching %d values", len(missed_data))
    cache.set_many(missed_data, CACHE_TIMEOUT)


def _cache_key(*args):
    args = (str(a).replace(' ', '') for a in args)
    return 'geomap:load:' + ':'.join(args)


def get_multiple_link_load(items, time_interval):
    """
    Gets the link load of the interfaces, averaged over a time interval,
    and adds to the load properties of the items.


    :param items: A dictionary of {(sysname, ifname): properties lazy_dict, ...}
    :param time_interval: A dict(start=..., end=...) describing the desired
                          time interval in terms valid to Graphite web.
    """
    target_map = {}
    for (sysname, ifname), properties in items.items():
        if not (sysname and ifname):
            continue

        targets = [
            metric_path_for_interface(sysname, ifname, counter)
            for counter in ('ifInOctets', 'ifOutOctets')
        ]
        targets = [get_metric_meta(t)['target'] for t in targets]
        target_map.update({t: properties for t in targets})

    _logger.debug(
        "getting %s graphite traffic targets in chunks", len(target_map.keys())
    )
    data = {}
    for chunk in chunks(target_map.keys(), METRIC_CHUNK_SIZE):
        data.update(_get_metric_average(chunk, time_interval))

    for key, value in data.items():
        properties = target_map.get(key, None)
        if properties:
            if value:
                bps = value / MEGABIT
                if 'ifInOctets' in key:
                    properties['load_in'] = bps
                elif 'ifOutOctets' in key:
                    properties['load_out'] = bps
        else:
            _logger.error(
                "no match for key %r (%r) in data returned from graphite", key, value
            )

    missing = set(target_map).difference(data)
    if missing:
        _logger.debug("missed %d targets in graphite response", len(missing))


def get_cached_multiple_cpu_load(items, time_interval):
    """Cached version of get_multiple_link_load()"""
    item_map = {k: _cache_key(k, time_interval) for k in items.keys()}
    # cache lookup
    cached = cache.get_many(item_map.values())
    _logger.debug(
        "get_cached_multiple_cpu_load: got %d/%d values from cache (%r)",
        len(cached),
        len(items),
        time_interval,
    )

    # retrieve data for cache misses
    misses = {k: v for k, v in items.items() if item_map[k] not in cached}
    if misses:
        get_multiple_cpu_load(misses, time_interval)

    # set data from cache
    reverse_item_map = {v: k for k, v in item_map.items()}
    for cache_key, value in cached.items():
        key = reverse_item_map[cache_key]
        properties = items[key]
        properties['load'] = value

    # add new data to cache
    missed_data = {
        item_map[key]: properties['load'] for key, properties in misses.items()
    }
    _logger.debug("get_cached_multiple_cpu_load: caching %d values", len(missed_data))
    cache.set_many(missed_data, CACHE_TIMEOUT)


def get_multiple_cpu_load(items, time_interval):
    """
    Gets the CPU load of netboxes, averaged over a time interval, and adds to
    the load properties of the items.

    :param items: A dictionary of {sysname: properties lazy_dict, ...}
    :param time_interval: A dict(start=..., end=...) describing the desired
                          time interval in terms valid to Graphite web.
    """
    target_map = {
        escape_metric_name(sysname): netbox for sysname, netbox in items.items()
    }
    targets = []
    for sysname, netbox in items.items():
        if not sysname:
            continue

        targets.extend(
            [
                'highestMax(%s,1)' % path
                for path in (
                    metric_path_for_cpu_load(sysname, '*', interval=5),
                    metric_path_for_cpu_utilization(sysname, '*'),
                )
            ]
        )

    _logger.debug("getting %s graphite cpu targets in chunks", len(targets))
    data = {}
    for chunk in chunks(targets, METRIC_CHUNK_SIZE):
        data.update(_get_metric_average(chunk, time_interval))

    for key, value in data.items():
        for sysname, netbox in target_map.items():
            if sysname in key:
                if not is_nan(value):
                    netbox['load'] = value
                    break


def _get_metric_average(targets, time_interval):
    try:
        data = get_metric_average(
            targets, start=time_interval['start'], end=time_interval['end']
        )
        _logger.debug(
            "graphite returned %s metrics from %s targets", len(data), len(targets)
        )
        return data
    except GraphiteUnreachableError as err:
        _logger.error(
            "graphite unreachable on load query for %s targets (%r): %s",
            len(targets),
            time_interval,
            err,
        )
        if isinstance(err.cause, HTTPError):
            _logger.debug("error cause: %s", err.cause.read())
        return {}

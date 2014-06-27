#
# Copyright (C) 2009, 2010, 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
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

import nav
from nav.config import read_flat_config
from nav.metrics.data import get_metric_average
from nav.metrics.errors import GraphiteUnreachableError
from nav.metrics.graphs import get_metric_meta
from nav.metrics.templates import (metric_path_for_interface,
                                   metric_path_for_cpu_load, metric_path_for_cpu_utilization)
from nav.web.geomap.utils import lazy_dict, subdict, fix

_logger = logging.getLogger(__name__)

try:
    _nav_conf = read_flat_config('nav.conf')
except IOError:
    _nav_conf = {}
_domain_suffix = _nav_conf.get('DOMAIN_SUFFIX', None)


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

    bounds_list = [bounds['minLon'], bounds['minLat'],
                   bounds['maxLon'], bounds['maxLat']]

    network_length_limit = 0

    network_query_args = bounds_list + bounds_list + [network_length_limit]

    if time_interval is None:
        time_interval = {'start': '-10min',
                         'end': 'now'}

    connections = {}

    layer_3_query = """
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
        WHERE interface_gwport.interfaceid <> remote_gwportid AND vlan.nettype NOT IN ('static', 'lan')
          AND ((room.position[1] >= %s AND room.position[0] >= %s AND
                room.position[1] <= %s AND room.position[0] <= %s)
               OR
               (remote_position[1] >= %s AND remote_position[0] >= %s AND
                remote_position[1] <= %s AND remote_position[0] <= %s))
          AND length(lseg(room.position, remote_position)) >= %s
        ORDER BY sysname,remote_sysname, netaddr ASC, speed DESC
    """



    layer_2_query_1 = """
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

 LEFT JOIN gwportprefix ON (gwportprefix.interfaceid = interface_gwport.interfaceid)
 LEFT JOIN prefix ON  (prefix.prefixid = gwportprefix.prefixid)
 LEFT JOIN vlan USING (vlanid)

 JOIN interface_swport ON (interface_swport.interfaceid = interface_gwport.to_interfaceid)
 JOIN netbox AS swport_netbox ON (interface_swport.netboxid = swport_netbox.netboxid)

 JOIN room AS gwport_room ON (netbox.roomid = gwport_room.roomid)
 JOIN room AS swport_room ON (swport_netbox.roomid = swport_room.roomid)

 WHERE interface_gwport.to_interfaceid IS NOT NULL AND interface_gwport.to_interfaceid = interface_swport.interfaceid
   AND ((gwport_room.position[1] >= %s AND gwport_room.position[0] >= %s AND
         gwport_room.position[1] <= %s AND gwport_room.position[0] <= %s)
        OR
        (swport_room.position[1] >= %s AND swport_room.position[0] >= %s AND
         swport_room.position[1] <= %s AND swport_room.position[0] <= %s))
   AND length(lseg(gwport_room.position, swport_room.position)) >= %s
    """

    layer_2_query_2 = """
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

    layer_2_query_3 = """
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

    db_cursor.execute(layer_3_query, network_query_args)
    # Expect DictRows, but want to work with updateable dicts:
    results = [lazy_dict(row) for row in db_cursor.fetchall()]
    db_cursor.execute(layer_2_query_1, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])
    db_cursor.execute(layer_2_query_2, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])
    db_cursor.execute(layer_2_query_3, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])

    for res in results:
        assert (res.get('remote_swportid', None) is not None or
                res.get('remote_gwportid', None) is not None)

    # Go through all the connections and add them to the connections
    # dictionary:
    for res in results:
        # Remove all data we are not interested in keeping:
        network_properties = \
            ['capacity', 'nettype', 'netident', 'layer', 'vlan',
             'local_sysname', 'local_netboxid', 'local_interface',
             'local_portid', 'local_gwportid', 'local_swportid',
             'remote_sysname', 'remote_netboxid', 'remote_interface',
             'remote_portid', 'remote_gwportid', 'remote_swportid']
        res = subdict(res, network_properties)

        # Create a reversed version of the connection (this has all
        # remote_*/local_* swapped and has load data from the opposite
        # end):
        reverse = res.copy()
        reversable_properties = ['sysname', 'netboxid', 'interface',
                                 'portid', 'gwportid', 'swportid']
        map(reverse.swap,
            map(lambda p: 'local_'+p, reversable_properties),
            map(lambda p: 'remote_'+p, reversable_properties))

        # Add load data to both res and reverse.  We use the laziness
        # of lazy_dict here (see documentation of class lazy_dict in
        # utils.py) to avoid reading the RRD files until we know that
        # they are needed.
        def add_load_properties(d):
            d[['load']] = fix(get_link_load,
                              [d['local_sysname'], d['local_interface'],
                               time_interval])
            d[['load_in']] = lambda: d['load'][0]
            d[['load_out']] = lambda: d['load'][1]
        map(add_load_properties, [res, reverse])

        connection_id = "%s-%s" % (res['local_sysname'], res['remote_sysname'])
        connection_rid = "%s-%s" % (res['remote_sysname'], res['local_sysname'])
        res['id'] = connection_id
        reverse['id'] = connection_rid

        connection = {'forward': res, 'reverse': reverse}

        if (connection_id not in connections and
            connection_rid not in connections):
            connections[connection_id] = connection
        else:
            for existing_id in connections.keys():
                existing_conn = connections[existing_id]
                if ((existing_id == connection_id or
                     existing_id == connection_rid) and
                    (existing_conn['forward']['capacity'] < res['capacity'])):
                    connections[existing_id] = connection

    query_netboxes = """
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

    db_cursor.execute(query_netboxes)
    netboxes = [lazy_dict(row) for row in db_cursor.fetchall()]
    for netbox in netboxes:
        netbox[['load']] = fix(get_cpu_load,
                               [netbox['sysname'], time_interval])
        if netbox['sysname'].endswith(_domain_suffix):
            hostname_length = len(netbox['sysname']) - len(_domain_suffix)
            netbox['sysname'] = netbox['sysname'][0:hostname_length]

    return netboxes, connections


# TRAFFIC DATA

MEGABIT = 1e6


def get_link_load(sysname, ifname, time_interval):
    """Gets the link load of the interface, averaged over a time interval.

    :param sysname: The sysname of the device we're measuring from.
    :param ifname: An interface name.
    :param time_interval: A dict(start=..., end=...) describing the desired
                          time interval in terms valid to Graphite web.
    :returns: An (avg_in_Mbps, avg_out_Mbps) tuple.

    """
    in_bps = out_bps = float('nan')
    if sysname and ifname:
        targets = [metric_path_for_interface(sysname, ifname, counter)
                   for counter in ('ifInOctets', 'ifOutOctets')]
        targets = [get_metric_meta(t)['target'] for t in targets]
        try:
            data = get_metric_average(targets,
                                      start=time_interval['start'],
                                      end=time_interval['end'])
        except GraphiteUnreachableError:
            _logger.error("graphite unreachable on load query for %s:%s (%r)",
                          sysname, ifname, time_interval)
            return in_bps, out_bps

        for key, value in data.iteritems():
            if 'ifInOctets' in key:
                in_bps = value / MEGABIT
            elif 'ifOutOctets' in key:
                out_bps = value / MEGABIT

    return in_bps, out_bps


def get_cpu_load(sysname, time_interval):
    """Returns the average 5 minute CPU load of sysname.

    Question is, of _which_ CPU? Let's just get the one that has the highest
    maximum value.

    :param sysname: The sysname of the device whose CPU load we're to get.
    :param time_interval: A dict(start=..., end=...) describing the desired
                          time interval in terms valid to Graphite web.
    :returns: A floating number representation of the load between 0 and
              100.0 (possibly higher in some multi-CPU settings).

    """
    data = None
    for path in (
        metric_path_for_cpu_load(sysname, '*', interval=5),
        metric_path_for_cpu_utilization(sysname, '*')
    ):
        target = 'highestMax(%s,1)' % path
        try:
            data = get_metric_average(target,
                                      start=time_interval['start'],
                                      end=time_interval['end'],
                                      ignore_unknown=True)
            if data:
                break
        except Exception:
            data = None

    result = data.values()[0] if data else float('nan')
    _logger.debug("get_cpu_load(%r, %r) == %r", sysname, time_interval, result)
    return result

#
# Copyright (C) 2009 UNINETT AS
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

"""Database access for Geomap.

This module abstracts away all the horrendous queries needed to get
data for Geomap from the database and provides one simple function,
get_data, which returns the stuff we want.

Based on datacollector.py in the Netmap subsystem.

"""

import random

import nav
from nav.config import readConfig
import rrdtool
from django.core.cache import cache

from nav.web.geomap.utils import *


_nav_conf = readConfig('nav.conf')
_domain_suffix = _nav_conf.get('DOMAIN_SUFFIX', None)


def get_data(db_cursor, bounds, time_interval=None):
    """Returns a dictionary containing the netboxes with their modules, ports and connections"""

    if not db_cursor:
        raise nav.errors.GeneralException("No db-cursor given")

    bounds_list = [bounds['minLon'], bounds['minLat'],
                   bounds['maxLon'], bounds['maxLat']]

    network_length_limit = 0

    network_query_args = bounds_list + bounds_list + [network_length_limit]

    if time_interval is None:
        time_interval = {'start': 'end-10min',
                         'end': 'now'}

    netboxes = {}
    connections = {}

    layer_3_query = """
SELECT DISTINCT ON (sysname, from_sysname) gwportprefixcount.count,gwport.gwportid,speed, ifindex, interface, sysname, netbox.netboxid, conn.*, nettype, netident, path ||'/'|| filename AS rrdfile,
3 AS layer, NULL AS from_swportid, vlan.*
FROM gwportprefix
  JOIN (
     SELECT DISTINCT ON (gwportprefix.prefixid)
       gwportid AS from_gwportid,
       gwportprefix.prefixid,
       ifindex AS from_ifindex,
       interface AS from_interface,
       sysname AS from_sysname,
       speed AS from_speed,
       netboxid AS from_netboxid
       FROM gwport
       JOIN module USING (moduleid)
       JOIN netbox USING (netboxid)
       JOIN gwportprefix USING (gwportid)
       ) AS conn USING (prefixid)
  JOIN gwport USING (gwportid)
  JOIN module USING (moduleid)
  JOIN ( SELECT gwportid, COUNT(*) AS count FROM gwportprefix GROUP BY gwportid ) AS gwportprefixcount ON (gwportprefix.gwportid = gwport.gwportid)
  JOIN netbox USING (netboxid)
  LEFT JOIN prefix ON  (prefix.prefixid = gwportprefix.prefixid)
  LEFT JOIN vlan USING (vlanid)
  LEFT JOIN rrd_file ON (key='gwport' AND value=conn.from_gwportid::varchar)
WHERE gwport.gwportid <> from_gwportid AND vlan.nettype NOT IN ('static', 'lan') AND gwportprefixcount.count = 2
ORDER BY sysname,from_sysname, netaddr ASC, speed DESC

"""

    # TODO using a modified query for now, since the above query is
    # very slow
    layer_3_query = """
        SELECT DISTINCT ON (sysname, from_sysname)
               gwport.gwportid,speed, ifindex, interface, sysname,
               netbox.netboxid, conn.*, nettype, netident,
               path ||'/'|| filename AS rrdfile,
               3 AS layer, NULL AS from_swportid, vlan.*
        FROM gwportprefix
        JOIN (
            SELECT DISTINCT ON (gwportprefix.prefixid)
                   gwportid AS from_gwportid,
                   gwportprefix.prefixid,
                   ifindex AS from_ifindex,
                   interface AS from_interface,
                   sysname AS from_sysname,
                   speed AS from_speed,
                   netboxid AS from_netboxid,
                   room.position AS from_position
            FROM gwport
            JOIN module USING (moduleid)
            JOIN netbox USING (netboxid)
            JOIN room USING (roomid)
            JOIN gwportprefix USING (gwportid)
        ) AS conn USING (prefixid)
        JOIN gwport USING (gwportid)
        JOIN module USING (moduleid)
        JOIN netbox USING (netboxid)
        JOIN room USING (roomid)
        LEFT JOIN prefix ON  (prefix.prefixid = gwportprefix.prefixid)
        LEFT JOIN vlan USING (vlanid)
        LEFT JOIN rrd_file ON (key='gwport' AND value=conn.from_gwportid::varchar)
        WHERE gwport.gwportid <> from_gwportid AND vlan.nettype NOT IN ('static', 'lan')
          AND ((room.position[1] >= %s AND room.position[0] >= %s AND
                room.position[1] <= %s AND room.position[0] <= %s)
               OR
               (from_position[1] >= %s AND from_position[0] >= %s AND
                from_position[1] <= %s AND from_position[0] <= %s))
          AND length(lseg(room.position, from_position)) >= %s
        ORDER BY sysname,from_sysname, netaddr ASC, speed DESC
    """



    layer_2_query_1 = """
SELECT DISTINCT ON (swport.swportid)
gwport.gwportid AS from_gwportid,
gwport.speed,
gwport.ifindex AS from_ifindex,
gwport.interface AS from_interface,
netbox.sysname AS from_sysname,
netbox.netboxid AS from_netboxid,
gwport.to_swportid AS to_swportid,

swport.swportid AS swportid,
swport.interface  AS interface,
swport_netbox.sysname AS sysname,
swport_netbox.netboxid AS netboxid,
swport.ifindex AS ifindex,

2 AS layer,
path ||'/'|| filename AS rrdfile,
nettype, netident,
NULL AS from_swportid,
NULL AS gwportid,
vlan.*

FROM gwport
 JOIN module ON (gwport.moduleid = module.moduleid)
 JOIN netbox USING (netboxid)

 LEFT JOIN gwportprefix ON (gwportprefix.gwportid = gwport.gwportid)
 LEFT JOIN prefix ON  (prefix.prefixid = gwportprefix.prefixid)
 LEFT JOIN vlan USING (vlanid)
 LEFT JOIN rrd_file ON (key='gwport' AND value=gwport.gwportid::varchar)

 JOIN swport ON (swport.swportid = gwport.to_swportid)
 JOIN module AS swport_module ON (swport.moduleid = swport.moduleid)
 JOIN netbox AS swport_netbox ON (swport_module.netboxid = swport_netbox.netboxid)

 JOIN room AS gwport_room ON (netbox.roomid = gwport_room.roomid)
 JOIN room AS swport_room ON (swport_netbox.roomid = swport_room.roomid)

 WHERE gwport.to_swportid IS NOT NULL AND gwport.to_swportid = swport.swportid AND swport_module.moduleid = swport.moduleid
   AND ((gwport_room.position[1] >= %s AND gwport_room.position[0] >= %s AND
         gwport_room.position[1] <= %s AND gwport_room.position[0] <= %s)
        OR
        (swport_room.position[1] >= %s AND swport_room.position[0] >= %s AND
         swport_room.position[1] <= %s AND swport_room.position[0] <= %s))
   AND length(lseg(gwport_room.position, swport_room.position)) >= %s
    """

    layer_2_query_2 = """
SELECT DISTINCT ON (from_sysname, sysname)
swport.swportid AS from_swportid,
swport.speed,
swport.ifindex AS from_ifindex,
swport.interface AS from_interface,
netbox.sysname AS from_sysname,
netbox.netboxid AS from_netboxid,
swport.to_swportid AS to_swportid,
2 AS layer,
foo.*,
vlan.*,
path ||'/'|| filename AS rrdfile,
NULL AS gwportid,
NULL AS from_gwportid

FROM swport
 JOIN module ON (swport.moduleid = module.moduleid)
 JOIN netbox USING (netboxid)

 JOIN (

     SELECT
     swport.swportid AS swportid,
     swport.speed,
     swport.ifindex AS ifindex,
     swport.interface AS interface,
     netbox.sysname AS sysname,
     netbox.netboxid AS netboxid,
     room.position AS to_position

     FROM swport
     JOIN module ON (swport.moduleid = module.moduleid)
     JOIN netbox USING (netboxid)
     JOIN room USING (roomid)

   ) AS foo ON (foo.swportid = to_swportid)


LEFT JOIN swportvlan ON (swport.swportid = swportvlan.swportid)
LEFT JOIN vlan USING (vlanid)

LEFT JOIN rrd_file  ON (key='swport' AND value=swport.swportid::varchar)

JOIN room AS from_room ON (netbox.roomid = from_room.roomid)

WHERE ((from_room.position[1] >= %s AND from_room.position[0] >= %s AND
        from_room.position[1] <= %s AND from_room.position[0] <= %s)
       OR
       (foo.to_position[1] >= %s AND foo.to_position[0] >= %s AND
        foo.to_position[1] <= %s AND foo.to_position[0] <= %s))
  AND length(lseg(from_room.position, foo.to_position)) >= %s

ORDER BY from_sysname, sysname, swport.speed DESC
    """

    layer_2_query_3 = """
SELECT DISTINCT ON (from_sysname, sysname)

swport.swportid AS from_swportid,
swport.speed,
swport.ifindex AS from_ifindex,
swport.interface AS from_interface,
netbox.sysname AS from_sysname,
netbox.netboxid AS from_netboxid,
2 AS layer,
conn.*,
vlan.*,
path ||'/'|| filename AS rrdfile,
NULL AS gwportid,
NULL AS from_gwportid,
NULL AS to_swportid


FROM swport
 JOIN module ON (swport.moduleid = module.moduleid)
 JOIN netbox USING (netboxid)

 JOIN (
    SELECT *, NULL AS interface, NULL AS swportid, room.position AS to_position
    FROM netbox
    JOIN room USING (roomid)
 ) AS conn ON (conn.netboxid = to_netboxid)

LEFT JOIN swportvlan ON (swport.swportid = swportvlan.swportid)
LEFT JOIN vlan USING (vlanid)
LEFT JOIN rrd_file  ON (key='swport' AND value=swport.swportid::varchar)

JOIN room AS from_room ON (netbox.roomid = from_room.roomid)

WHERE ((from_room.position[1] >= %s AND from_room.position[0] >= %s AND
        from_room.position[1] <= %s AND from_room.position[0] <= %s)
       OR
       (conn.to_position[1] >= %s AND conn.to_position[0] >= %s AND
        conn.to_position[1] <= %s AND conn.to_position[0] <= %s))
  AND length(lseg(from_room.position, conn.to_position)) >= %s

ORDER BY from_sysname, sysname, swport.speed DESC
    """

    db_cursor.execute(layer_3_query, network_query_args)
    # Expect DictRows, but want to work with updateable dicts:
    results = [lazy_dict(row) for row in db_cursor.fetchall()]
    for res in results:
        if res.get('from_swportid', None) is None and res.get('from_gwportid', None) is None:
            assert False, str(res)
    db_cursor.execute(layer_2_query_1, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])
    for res in results:
        if res.get('from_swportid', None) is None and res.get('from_gwportid', None) is None:
            assert False, str(res)
    db_cursor.execute(layer_2_query_2, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])
    for res in results:
        if res.get('from_swportid', None) is None and res.get('from_gwportid', None) is None:
            assert False, str(res)
    db_cursor.execute(layer_2_query_3, network_query_args)
    results.extend([lazy_dict(row) for row in db_cursor.fetchall()])
    for res in results:
        if res.get('from_swportid', None) is None and res.get('from_gwportid', None) is None:
            assert False, str(res)
        if 'from_swportid' not in res and 'from_gwportid' not in res:
            assert False, str(res)
        if res['rrdfile']:
            res.set_lazy('load',
                         lambda file: get_rrd_link_load(file, time_interval),
                         res['rrdfile'])
        else:
            res['load'] = ('unknown','unknown')
        res.set_lazy('load_in', lambda r: r['load'][0], res)
        res.set_lazy('load_out', lambda r: r['load'][1], res)
        if 'from_swportid' in res and res['from_swportid']:
            res['ipdevinfo_link'] = "swport=" + str(res['from_swportid'])
        elif 'from_gwportid' in res and res['from_gwportid']:
            res['ipdevinfo_link'] = "gwport=" + str(res['from_gwportid'])
        else:
            assert False, str(res)

        connection_id = "%s-%s" % (res['sysname'], res['from_sysname'], )
        connection_rid = "%s-%s" % (res['from_sysname'], res['sysname'])
        if connection_id not in connections and connection_rid not in connections:
            connections[connection_id] = res
        else:
            for conn in connections.keys():
                if conn == connection_id or conn == connection_rid:
                    if connections[conn]['speed'] < res['speed']:
                        connections[conn] = res


    query = """
        SELECT DISTINCT ON (netboxid) *,location.descr AS location,room.descr AS room,room.opt3 as utm,  path || '/' || filename AS rrd
        FROM netbox
        LEFT JOIN room using (roomid)
        LEFT JOIN location USING (locationid)
        LEFT JOIN type USING (typeid)
        LEFT JOIN (SELECT netboxid,path,filename FROM rrd_file NATURAL JOIN rrd_datasource WHERE descr = 'cpu5min') AS rrd USING (netboxid)
        LEFT JOIN netmap_position USING (sysname)
        """

    query = """
        SELECT DISTINCT ON (netboxid)
               *, location.descr AS location, room.descr AS room,
               room.position[0] as lat, room.position[1] as lon,
               path || '/' || filename AS rrd
        FROM netbox
        LEFT JOIN room using (roomid)
        LEFT JOIN location USING (locationid)
        LEFT JOIN type USING (typeid)
        LEFT JOIN (SELECT netboxid,path,filename
                   FROM rrd_file
                   NATURAL JOIN rrd_datasource
                   WHERE descr = 'cpu5min') AS rrd USING (netboxid)
        LEFT JOIN netmap_position USING (sysname)
        WHERE room.position IS NOT NULL
        """
#         WHERE room.position[1] >= %s AND room.position[0] >= %s
#           AND room.position[1] <= %s AND room.position[0] <= %s
#         """

    db_cursor.execute(query)
    netboxes = [lazy_dict(row) for row in db_cursor.fetchall()]
    for netbox in netboxes:
        netbox.set_lazy('load',
                        lambda file: get_rrd_cpu_load(file, time_interval),
                        netbox['rrd'])
        if netbox['sysname'].endswith(_domain_suffix):
            netbox['sysname'] = netbox['sysname'][0:len(netbox['sysname'])-len(_domain_suffix)]

    return (netboxes, connections)


def get_rrd_link_load(rrdfile, time_interval):
    """Returns the ds1 and ds2 fields of an rrd-file (ifInOctets,
    ifOutOctets)"""
    if not rrdfile:
        return ('unknown','unknown')
    rrd_data = read_rrd_data(rrdfile, 'AVERAGE', time_interval, [2, 0])
    if rrd_data == 'unknown':
        return ('unknown', 'unknown')
    rrd_data = (rrd_data[0] or float('nan'), rrd_data[1] or float('nan'))
    return ((rrd_data[1])/1024.0, (rrd_data[0])/1024.0)


def get_rrd_cpu_load(rrdfile, time_interval):
    if not rrdfile:
        return 'unknown'
    return read_rrd_data(rrdfile, 'AVERAGE', time_interval, [2, 0, 1])


rrd_statistics = {'cache': 0,
                  'file': 0}

def read_rrd_data(rrdfile, cf, time_interval, indices):
    rrdfile = rrd_file_name(rrdfile)
    key = 'geomap-rrd-%s-%s-(%s,%s)-(%s)' % \
        (rrdfile, cf, time_interval['start'], time_interval['end'],
         ','.join(map(str, indices)))
    timeout_seconds = 60*5
    val = cache.get(key)

    if val is None: rrd_statistics['file'] = rrd_statistics['file']+1
    else: rrd_statistics['cache'] = rrd_statistics['cache']+1

    if val is None:
        try:
            val = apply(rrdtool.fetch, [rrdfile, cf] + rrd_args(time_interval))
            for index in indices:
                val = val[index]
        except:
            val = 'unknown'
        if val is None:
            val = 'unknown'
        cache.set(key, val, timeout_seconds)
    return val


def rrd_file_name(filename):
    # TODO remove the following line (hack for using teknobyen-vk data
    # from navdev)
    filename = filename.replace('/home/nav/cricket-data', '/media/prod-rrd')
    return str(filename)


def rrd_args(time_interval):
    return ['-s ' + str(time_interval['start']),
            '-e ' + str(time_interval['end'])]


def validate_rrd_time(time):
    re_time = 'midnight|noon|teatime|\d\d([:.]\d\d)?([ap]m)?'
    re_day1 = 'yesterday|today|tomorrow'
    re_day2 = '(January|February|March|April|May|June|July|August|' + \
        'September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|' + \
        'Aug|Sep|Oct|Nov|Dec) \d\d?( \d\d(\d\d)?)?'
    re_day3 = '\d\d/\d\d/\d\d(\d\d)?'
    re_day4 = '\d\d[.]\d\d[.]\d\d(\d\d)?'
    re_day5 = '\d\d\d\d\d\d\d\d'
    re_day6 = 'Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|' + \
        'Mon|Tue|Wed|Thu|Fri|Sat|Sun'
    re_day = '(%s)|(%s)|(%s)|(%s)|(%s)|(%s)' % \
        (re_day1, re_day2, re_day3, re_day4, re_day5, re_day6)
    re_ref = 'now|start|end|(((%s) )?(%s))' % (re_time, re_day)

    re_offset_long = '(year|month|week|day|hour|minute|second)s?'
    re_offset_short = 'mon|min|sec'
    re_offset_single = 'y|m|w|d|h|s'
    re_offset_no_sign = '\d+((%s)|(%s)|(%s))' % \
        (re_offset_long, re_offset_short, re_offset_single)
    re_offset = '[+-](%s)([+-]?%s)*' % \
        (re_offset_no_sign, re_offset_no_sign)

    re_total = '^(%s)|((%s) ?(%s)?)$' % (re_offset, re_ref, re_offset)
    return re.match(re_total, time) is not None


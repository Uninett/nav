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

"""Data access for Geomap.

This module abstracts away all the horrendous queries needed to get
data for Geomap from the database, as well as the code for reading RRD
files, and provides one simple function, get_data, which returns the
stuff we want.

Based on datacollector.py in the Netmap subsystem.

"""

import random
import logging
import re
from datetime import datetime, timedelta

import nav
from nav.config import readConfig
import rrdtool
from django.core.cache import cache

from nav.web.geomap.utils import *


logger = logging.getLogger('nav.web.geomap.db')


_nav_conf = readConfig('nav.conf')
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

    The caller of get_data should call get_data_finish when the
    objects returned from get_data are no longer used.

    """

    if not db_cursor:
        raise nav.errors.GeneralException("No db-cursor given")

    bounds_list = [bounds['minLon'], bounds['minLat'],
                   bounds['maxLon'], bounds['maxLat']]

    network_length_limit = 0

    network_query_args = bounds_list + bounds_list + [network_length_limit]

    if time_interval is None:
        time_interval = {'start': 'end-10min',
                         'end': 'now'}

    read_cache(time_interval)

    netboxes = {}
    connections = {}

    layer_3_query = """
        SELECT DISTINCT ON (local_sysname, remote_sysname)
               sysname AS local_sysname,
               interface AS local_interface,
               netbox.netboxid AS local_netboxid,
               gwport.gwportid AS local_gwportid,
               gwport.gwportid AS local_portid,
               NULL AS local_swportid,
               speed AS capacity,
               ifindex,
               conn.*, nettype, netident,
               remote_rrd_file.path ||'/'|| remote_rrd_file.filename AS remote_rrdfile,
               rrd_file.path ||'/'|| rrd_file.filename AS local_rrdfile,
               3 AS layer, NULL AS remote_swportid, vlan.*
        FROM gwportprefix
        JOIN (
            SELECT DISTINCT ON (gwportprefix.prefixid)
                   gwportid AS remote_gwportid,
                   gwportid AS remote_portid,
                   NULL AS remote_swportid,
                   gwportprefix.prefixid,
                   ifindex AS remote_ifindex,
                   interface AS remote_interface,
                   sysname AS remote_sysname,
                   speed AS remote_speed,
                   netboxid AS remote_netboxid,
                   room.position AS remote_position
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
        LEFT JOIN rrd_file AS remote_rrd_file ON (remote_rrd_file.key='gwport' AND remote_rrd_file.value=conn.remote_gwportid::varchar)
        LEFT JOIN rrd_file ON (rrd_file.key='gwport' AND rrd_file.value=gwport.gwportid::varchar)
        WHERE gwport.gwportid <> remote_gwportid AND vlan.nettype NOT IN ('static', 'lan')
          AND ((room.position[1] >= %s AND room.position[0] >= %s AND
                room.position[1] <= %s AND room.position[0] <= %s)
               OR
               (remote_position[1] >= %s AND remote_position[0] >= %s AND
                remote_position[1] <= %s AND remote_position[0] <= %s))
          AND length(lseg(room.position, remote_position)) >= %s
        ORDER BY sysname,remote_sysname, netaddr ASC, speed DESC
    """



    layer_2_query_1 = """
SELECT DISTINCT ON (swport.swportid)
gwport.gwportid AS remote_gwportid,
gwport.gwportid AS remote_portid,
NULL AS remote_swportid,
gwport.speed AS capacity,
gwport.ifindex AS remote_ifindex,
gwport.interface AS remote_interface,
netbox.sysname AS remote_sysname,
netbox.netboxid AS remote_netboxid,

swport.swportid AS local_swportid,
swport.swportid AS local_portid,
NULL AS local_gwportid,
swport.interface AS local_interface,
swport_netbox.sysname AS local_sysname,
swport_netbox.netboxid AS local_netboxid,
swport.ifindex AS ifindex,

2 AS layer,
remote_rrd_file.path ||'/'|| remote_rrd_file.filename AS remote_rrdfile,
rrd_file.path ||'/'|| rrd_file.filename AS local_rrdfile,
nettype, netident,
vlan.*

FROM gwport
 JOIN module ON (gwport.moduleid = module.moduleid)
 JOIN netbox USING (netboxid)

 LEFT JOIN gwportprefix ON (gwportprefix.gwportid = gwport.gwportid)
 LEFT JOIN prefix ON  (prefix.prefixid = gwportprefix.prefixid)
 LEFT JOIN vlan USING (vlanid)
 LEFT JOIN rrd_file AS remote_rrd_file ON (remote_rrd_file.key='gwport' AND remote_rrd_file.value=gwport.gwportid::varchar)

 JOIN swport ON (swport.swportid = gwport.to_swportid)
 JOIN module AS swport_module ON (swport.moduleid = swport.moduleid)
 JOIN netbox AS swport_netbox ON (swport_module.netboxid = swport_netbox.netboxid)

 LEFT JOIN rrd_file ON (rrd_file.key='swport' AND rrd_file.value=swport.swportid::varchar)

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
SELECT DISTINCT ON (remote_sysname, local_sysname)
swport.swportid AS remote_swportid,
swport.swportid AS remote_portid,
NULL AS remote_gwportid,
swport.speed AS capacity,
swport.ifindex AS remote_ifindex,
swport.interface AS remote_interface,
netbox.sysname AS remote_sysname,
netbox.netboxid AS remote_netboxid,
2 AS layer,
foo.*,
vlan.*,
remote_rrd_file.path ||'/'|| remote_rrd_file.filename AS remote_rrdfile,
rrd_file.path ||'/'|| rrd_file.filename AS local_rrdfile

FROM swport
 JOIN module ON (swport.moduleid = module.moduleid)
 JOIN netbox USING (netboxid)

 JOIN (

     SELECT
     swport.swportid AS local_swportid,
     swport.swportid AS local_portid,
     NULL AS local_gwportid,
     swport.ifindex AS ifindex,
     swport.interface AS local_interface,
     netbox.sysname AS local_sysname,
     netbox.netboxid AS local_netboxid,
     room.position AS local_position

     FROM swport
     JOIN module ON (swport.moduleid = module.moduleid)
     JOIN netbox USING (netboxid)
     JOIN room USING (roomid)

   ) AS foo ON (foo.local_swportid = to_swportid)


LEFT JOIN swportvlan ON (swport.swportid = swportvlan.swportid)
LEFT JOIN vlan USING (vlanid)

LEFT JOIN rrd_file AS remote_rrd_file ON (remote_rrd_file.key='swport' AND remote_rrd_file.value=swport.swportid::varchar)
LEFT JOIN rrd_file ON (rrd_file.key='swport' AND rrd_file.value=foo.local_swportid::varchar)

JOIN room AS remote_room ON (netbox.roomid = remote_room.roomid)

WHERE ((remote_room.position[1] >= %s AND remote_room.position[0] >= %s AND
        remote_room.position[1] <= %s AND remote_room.position[0] <= %s)
       OR
       (foo.local_position[1] >= %s AND foo.local_position[0] >= %s AND
        foo.local_position[1] <= %s AND foo.local_position[0] <= %s))
  AND length(lseg(remote_room.position, foo.local_position)) >= %s

ORDER BY remote_sysname, local_sysname, swport.speed DESC
    """

    layer_2_query_3 = """
SELECT DISTINCT ON (remote_sysname, local_sysname)

swport.swportid AS remote_swportid,
swport.swportid AS remote_portid,
swport.ifindex AS remote_ifindex,
swport.interface AS remote_interface,
netbox.sysname AS remote_sysname,
netbox.netboxid AS remote_netboxid,
swport.speed AS capacity,
2 AS layer,
conn.*,
vlan.*,
path ||'/'|| filename AS remote_rrdfile,
NULL AS remote_gwportid,
NULL AS local_rrdfile,
NULL AS local_gwportid,
NULL AS local_swportid,
NULL AS local_portid,
NULL AS local_interface

FROM swport
 JOIN module ON (swport.moduleid = module.moduleid)
 JOIN netbox USING (netboxid)

 JOIN (
    SELECT
      netbox.sysname AS local_sysname,
      netbox.netboxid AS local_netboxid,
      room.position AS local_position
    FROM netbox
    JOIN room USING (roomid)
 ) AS conn ON (conn.local_netboxid = to_netboxid)

LEFT JOIN swportvlan ON (swport.swportid = swportvlan.swportid)
LEFT JOIN vlan USING (vlanid)
LEFT JOIN rrd_file  ON (key='swport' AND value=swport.swportid::varchar)

JOIN room AS remote_room ON (netbox.roomid = remote_room.roomid)

WHERE ((remote_room.position[1] >= %s AND remote_room.position[0] >= %s AND
        remote_room.position[1] <= %s AND remote_room.position[0] <= %s)
       OR
       (conn.local_position[1] >= %s AND conn.local_position[0] >= %s AND
        conn.local_position[1] <= %s AND conn.local_position[0] <= %s))
  AND length(lseg(remote_room.position, conn.local_position)) >= %s

ORDER BY remote_sysname, local_sysname, swport.speed DESC
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
             'local_rrdfile',
             'remote_sysname', 'remote_netboxid', 'remote_interface',
             'remote_portid', 'remote_gwportid', 'remote_swportid',
             'remote_rrdfile']
        res = subdict(res, network_properties)

        # Create a reversed version of the connection (this has all
        # remote_*/local_* swapped and has load data from the opposite
        # end):
        reverse = res.copy()
        reversable_properties = ['sysname', 'netboxid', 'interface',
                                 'portid', 'gwportid', 'swportid',
                                 'rrdfile']
        map(reverse.swap,
            map(lambda p: 'local_'+p, reversable_properties),
            map(lambda p: 'remote_'+p, reversable_properties))

        # Add load data to both res and reverse.  We use the laziness
        # of lazy_dict here (see documentation of class lazy_dict in
        # utils.py) to avoid reading the RRD files until we know that
        # they are needed.
        def add_load_properties(d):
            if d['local_rrdfile']:
                d[['load']] = fix(get_rrd_link_load,
                                  [d['local_rrdfile'], time_interval])
            else:
                d['load'] = (float('nan'), float('nan'))
            d[['load_in']] = lambda: d['load'][0]
            d[['load_out']] = lambda: d['load'][1]
        map(add_load_properties, [res, reverse])

        connection_id = "%s-%s" % (res['local_sysname'], res['remote_sysname'])
        connection_rid = "%s-%s" % (res['remote_sysname'], res['local_sysname'])
        res['id'] = connection_id
        reverse['id'] = connection_rid

        connection = {'forward': res, 'reverse': reverse}

        if connection_id not in connections and connection_rid not in connections:
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

    db_cursor.execute(query_netboxes)
    netboxes = [lazy_dict(row) for row in db_cursor.fetchall()]
    for netbox in netboxes:
        netbox.set_lazy('load',
                        lambda file: get_rrd_cpu_load(file, time_interval),
                        netbox['rrd'])
        if netbox['sysname'].endswith(_domain_suffix):
            netbox['sysname'] = netbox['sysname'][0:len(netbox['sysname'])-len(_domain_suffix)]

    return (netboxes, connections)


def get_data_finish():
    """Pick up loose threads left behind by get_data.

    This should be called when the objects returned by get_data are no
    longer used.  Since reading of data from RRD files is delayed
    until it is needed, this module can never know when it is finished
    reading RRD files unless being told explicitly.

    """
    store_cache()


# RRD FILES

def get_rrd_link_load(rrdfile, time_interval):
    """Returns the ds1 and ds2 fields of an rrd-file (ifInOctets,
    ifOutOctets)"""
    nan = float('nan')
    if not rrdfile:
        return (nan, nan)
    rrd_data = read_rrd_data(rrdfile, 'AVERAGE', time_interval, [2, 0])
    if rrd_data == 'unknown':
        return (nan, nan)
    # Replace unknown values by nan:
    rrd_data = (rrd_data[0] or nan, rrd_data[1] or nan)
    # Make sure values are floats:
    rrd_data = (float(rrd_data[0]), float(rrd_data[1]))

    # Reverse the order (apparently, the original order is (out, in).
    # I have no idea about whether that is correct or how to find out
    # if it is; I know nothing, I only copied this from Netmap's
    # datacollector.py).
    ####rrd_data = (rrd_data[1], rrd_data[0])
    # [Commented out the above line: I _think_ the order actually is
    # (in, out), based on looking at the database (which seems to
    # suggest that ds0=ifInOctets, ds1=ifOutOctets) and the result of
    # doing an rrdtool.fetch (which seems to suggest that the order of
    # the data is (ds0, ds1, ...)) and a whole lot of unqualified
    # guesswork.  Are these things documented anywhere?  Uncomment the
    # line if the order actually _is_ (out, in)]

    # Convert from bit/s to Mibit/s to get same unit as the 'capacity'
    # property:
    rrd_data = (rrd_data[0]/(1024*1024), rrd_data[1]/(1024*1024))
    return rrd_data


def get_rrd_cpu_load(rrdfile, time_interval):
    nan = float('nan')
    if not rrdfile:
        return nan
    rrd_data = read_rrd_data(rrdfile, 'AVERAGE', time_interval, [2, 0, 1])
    if rrd_data == 'unknown':
        return nan
    return rrd_data


def read_rrd_data(rrdfile, cf, time_interval, indices):
    """Read data from an RRD file or cache."""
    rrdfile = rrd_file_name(rrdfile)
    key = '%s-(%s)' % (rrdfile, ','.join(map(str, indices)))
    val = cache_get(key)

    if val is None:
        try:
            val = apply(rrdtool.fetch, [rrdfile, cf] + rrd_args(time_interval))
            for index in indices:
                val = val[index]
        except:
            val = 'unknown'
        if val is None:
            val = 'unknown'
        cache_set(key, val)
    return val


def rrd_file_name(filename):
    """Perform any necessary transformation of an RRD file name."""
    # TODO remove the following line (hack for using teknobyen-vk data
    # from navdev)
    filename = filename.replace('/home/nav/cricket-data', '/media/prod-rrd')
    return str(filename)


def rrd_args(time_interval):
    """Create RRDtool arguments for the specified time interval."""
    return ['-s ' + str(time_interval['start']),
            '-e ' + str(time_interval['end'])]


def validate_rrd_time(time):
    """Validate a time specification in RRDtool format."""
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

def parse_rrd_time(time):
    """Parse a time in RRD format.

    Returns a datetime object.  Only understands one of several
    formats RRD times may have, returns None if the specified string
    is not understood.

    """
    re_rrd = '(\d\d):(\d\d) (\d\d\d\d)(\d\d)(\d\d)'
    match = re.match(re_rrd, time)
    if match:
        return apply(datetime,
                     map(compose(int, match.group),
                         [3, 4, 5, 1, 2]))
    return None



# CACHE
#
# We use Django's cache framework to cache data from RRD files, since
# reading all the files may take a long time. To avoid putting
# extremely many keys into the cache, all data for a single time
# interval is stored under one key, as a dictionary. For a single
# request, only one time interval is interesting, and the cached data
# for this interval is read with the function read_cache by get_data
# and stored by calling store_cache after all processing is
# finished. The functions cache_get/cache_set provide an interface to
# the individual values within the dictionary for the active time
# interval.

_cache_key = None
_cache_data = None
_cache_timeout = None
_cache_statistics = None

def read_cache(time_interval):
    """Read all cached data for given time interval.

    The data will be available by the cache_get function.

    """
    global _cache_data, _cache_key, _cache_timeout, _cache_statistics
    _cache_timeout = cache_timeout(time_interval)
    _cache_key = 'geomap-rrd-(%s,%s)' % \
        (time_interval['start'], time_interval['end'])
    _cache_key = _cache_key.replace(' ', '_')
    _cache_data = cache.get(_cache_key)
    if _cache_data is None:
        _cache_data = {}
    _cache_statistics = {'hit': 0, 'miss': 0}

def cache_timeout(time_interval):
    """Determine how long to keep data for a certain time interval in cache.

    Returns time in number of seconds.

    Arguments:

    time_interval -- dictionary with keys ('start', 'end'), values are
    start and end time in RRD format.

    """
    starttime = parse_rrd_time(time_interval['start'])
    endtime = parse_rrd_time(time_interval['end'])
    minute = 60
    hour = 60*60
    # Intervals which are finished (and then some time to allow data
    # to be collected, arbitrarily chosen as 2 minutes):
    if endtime and (datetime.now() - endtime > timedelta(minutes=2)):
        return hour
    # Small unfinished intervals:
    if starttime and endtime and \
            (endtime - starttime < timedelta(hours=1)):
        return minute
    # Somewhat larger unfinished intervals:
    if starttime and endtime and \
            (endtime - starttime < timedelta(days=1)):
        return 5*minute
    # Large intervals which are not finished:
    else:
        return hour

def cache_get(key):
    """Get an object from the cache loaded by read_cache."""
    obj = _cache_data.get(key)
    if obj is None:
        _cache_statistics['miss'] += 1
    else:
        _cache_statistics['hit'] += 1
    return obj

def cache_set(key, val):
    """Set a value in the cache loaded by read_cache."""
    _cache_data[key] = val

def store_cache():
    """Write back the cache loaded by read_cache."""
    logger.debug('RRD file cache: %d hits, %d misses' %
                 (_cache_statistics['hit'], _cache_statistics['miss']))
    logger.debug('Storing cache with timeout %d seconds' % _cache_timeout)
    cache.set(_cache_key, _cache_data, _cache_timeout)

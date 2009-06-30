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

import os
import sys
import re
from math import pi, sin, cos, tan, sqrt

from django.template import Context, Template

import nav
from nav.config import readConfig
import rrdtool
import cgi


# database interface:

_conf = readConfig('nav.conf')
_domain_suffix = _conf.get('DOMAIN_SUFFIX', None)


def get_data(db_cursor = None):
    """Returns a dictionary containing the netboxes with their modules, ports and connections"""

    if not db_cursor:
        raise nav.errors.GeneralException("No db-cursor given")

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
SELECT DISTINCT ON (sysname, from_sysname) gwport.gwportid,speed, ifindex, interface, sysname, netbox.netboxid, conn.*, nettype, netident, path ||'/'|| filename AS rrdfile,
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
  JOIN netbox USING (netboxid)
  LEFT JOIN prefix ON  (prefix.prefixid = gwportprefix.prefixid)
  LEFT JOIN vlan USING (vlanid)
  LEFT JOIN rrd_file ON (key='gwport' AND value=conn.from_gwportid::varchar)
WHERE gwport.gwportid <> from_gwportid AND vlan.nettype NOT IN ('static', 'lan')
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


 WHERE gwport.to_swportid IS NOT NULL AND gwport.to_swportid = swport.swportid AND swport_module.moduleid = swport.moduleid
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
 netbox.netboxid AS netboxid

 FROM swport
  JOIN module ON (swport.moduleid = module.moduleid)
   JOIN netbox USING (netboxid)
   ) AS foo ON (foo.swportid = to_swportid)


LEFT JOIN swportvlan ON (swport.swportid = swportvlan.swportid)
LEFT JOIN vlan USING (vlanid)

LEFT JOIN rrd_file  ON (key='swport' AND value=swport.swportid::varchar)

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

 SELECT *, NULL AS interface, NULL AS swportid
FROM netbox
   ) AS conn ON (conn.netboxid = to_netboxid)

LEFT JOIN swportvlan ON (swport.swportid = swportvlan.swportid)
LEFT JOIN vlan USING (vlanid)
LEFT JOIN rrd_file  ON (key='swport' AND value=swport.swportid::varchar)

ORDER BY from_sysname, sysname, swport.speed DESC
    """

    db_cursor.execute(layer_3_query)
    # Expect DictRows, but want to work with updateable dicts:
    results = [dict(row) for row in db_cursor.fetchall()]
    for res in results:
        if res.get('from_swportid', None) is None and res.get('from_gwportid', None) is None:
            assert False, str(res)
    db_cursor.execute(layer_2_query_1)
    results.extend([dict(row) for row in db_cursor.fetchall()])
    for res in results:
        if res.get('from_swportid', None) is None and res.get('from_gwportid', None) is None:
            assert False, str(res)
    db_cursor.execute(layer_2_query_2)
    results.extend([dict(row) for row in db_cursor.fetchall()])
    for res in results:
        if res.get('from_swportid', None) is None and res.get('from_gwportid', None) is None:
            assert False, str(res)
    db_cursor.execute(layer_2_query_3)
    results.extend([dict(row) for row in db_cursor.fetchall()])
    for res in results:
        if res.get('from_swportid', None) is None and res.get('from_gwportid', None) is None:
            assert False, str(res)
        if 'from_swportid' not in res and 'from_gwportid' not in res:
            assert False, str(res)
        if res['rrdfile']:
            data = get_rrd_link_load(res['rrdfile'])
            res['load'] = (data[0],data[1])
        else:
            res['load'] = (-1,-1)
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
    db_cursor.execute(query)
    netboxes = [dict(row) for row in db_cursor.fetchall()]
    for netbox in netboxes:
        if netbox['rrd']:
            try:
                netbox['load'] = rrdtool.fetch(netbox['rrd'], 'AVERAGE', '-s -10min')[2][0][1]
            except:
                netbox['load'] = 'unknown'
        else:
            netbox['load'] = 'unknown'
        if netbox['sysname'].endswith(_domain_suffix):
            netbox['sysname'] = netbox['sysname'][0:len(netbox['sysname'])-len(_domain_suffix)]

    return (netboxes, connections)

def get_rrd_link_load(rrdfile):
    """Returns the ds1 and ds2 fields of an rrd-file (ifInOctets,
    ifOutOctets)"""
    if not rrdfile:
        return (-1,-1)
    try:
        data = rrdtool.fetch(rrdfile, 'AVERAGE', '-s -10min')[2][0]
        return ((data[1])/1024.0, (data[0])/1024.0)
    except:
        return (-1,-1)




# coordinate transformation (derived from http://pygps.org/LatLongUTMconversion-1.2.tar.gz):

_deg2rad = pi / 180.0
_rad2deg = 180.0 / pi

_equatorial_radius = 2
_eccentricity_squared = 3

_ellipsoid = [
#  id, Ellipsoid name, Equatorial Radius, square of eccentricity	
# first once is a placeholder only, To allow array indices to match id numbers
	[ -1, "Placeholder", 0, 0],
	[ 1, "Airy", 6377563, 0.00667054],
	[ 2, "Australian National", 6378160, 0.006694542],
	[ 3, "Bessel 1841", 6377397, 0.006674372],
	[ 4, "Bessel 1841 (Nambia] ", 6377484, 0.006674372],
	[ 5, "Clarke 1866", 6378206, 0.006768658],
	[ 6, "Clarke 1880", 6378249, 0.006803511],
	[ 7, "Everest", 6377276, 0.006637847],
	[ 8, "Fischer 1960 (Mercury] ", 6378166, 0.006693422],
	[ 9, "Fischer 1968", 6378150, 0.006693422],
	[ 10, "GRS 1967", 6378160, 0.006694605],
	[ 11, "GRS 1980", 6378137, 0.00669438],
	[ 12, "Helmert 1906", 6378200, 0.006693422],
	[ 13, "Hough", 6378270, 0.00672267],
	[ 14, "International", 6378388, 0.00672267],
	[ 15, "Krassovsky", 6378245, 0.006693422],
	[ 16, "Modified Airy", 6377340, 0.00667054],
	[ 17, "Modified Everest", 6377304, 0.006637847],
	[ 18, "Modified Fischer 1960", 6378155, 0.006693422],
	[ 19, "South American 1969", 6378160, 0.006694542],
	[ 20, "WGS 60", 6378165, 0.006693422],
	[ 21, "WGS 66", 6378145, 0.006694542],
	[ 22, "WGS-72", 6378135, 0.006694318],
	[ 23, "WGS-84", 6378137, 0.00669438]
]

#Reference ellipsoids derived from Peter H. Dana's website- 
#http://www.utexas.edu/depts/grg/gcraft/notes/datum/elist.html
#Department of Geography, University of Texas at Austin
#Internet: pdana@mail.utexas.edu
#3/22/95

#Source
#Defense Mapping Agency. 1987b. DMA Technical Report: Supplement to Department of Defense World Geodetic System
#1984 Technical Report. Part I and II. Washington, DC: Defense Mapping Agency

def ll_to_utm(reference_ellipsoid, lat, lon, zone = None):
    """converts lat/long to UTM coords.  Equations from USGS Bulletin 1532 
    East Longitudes are positive, West longitudes are negative. 
    North latitudes are positive, South latitudes are negative
    lat and Long are in decimal degrees
    Written by Chuck Gantz- chuck.gantz@globalstar.com"""

    a = _ellipsoid[reference_ellipsoid][_equatorial_radius]
    ecc_squared = _ellipsoid[reference_ellipsoid][_eccentricity_squared]
    k0 = 0.9996

#Make sure the longitude is between -180.00 .. 179.9
    lon_tmp = (lon+180)-int((lon+180)/360)*360-180 # -180.00 .. 179.9

    lat_rad = lat*_deg2rad
    lon_rad = lon_tmp*_deg2rad

    if zone is None:
        zone_number = int((lon_tmp + 180)/6) + 1
    else:
        zone_number = zone
  
    if lat >= 56.0 and lat < 64.0 and lon_tmp >= 3.0 and lon_tmp < 12.0:
        zone_number = 32

    # Special zones for Svalbard
    if lat >= 72.0 and lat < 84.0:
        if lon_tmp >= 0.0 and lon_tmp < 9.0:
            zone_number = 31
        elif lon_tmp >= 9.0  and lon_tmp < 21.0:
            zone_number = 33
        elif lon_tmp >= 21.0 and lon_tmp < 33.0:
            zone_number = 35
        elif lon_tmp >= 33.0 and lon_tmp < 42.0:
            zone_number = 37

    lon_origin = (zone_number - 1)*6 - 180 + 3 #+3 puts origin in middle of zone
    lon_origin_rad = lon_origin * _deg2rad

    #compute the UTM Zone from the latitude and longitude
    utm_zone = "%d%c" % (zone_number, _utm_letter_designator(lat))

    ecc_prime_squared = (ecc_squared)/(1-ecc_squared)
    N = a/sqrt(1-ecc_squared*sin(lat_rad)*sin(lat_rad))
    T = tan(lat_rad)*tan(lat_rad)
    C = ecc_prime_squared*cos(lat_rad)*cos(lat_rad)
    A = cos(lat_rad)*(lon_rad-lon_origin_rad)

    M = a*((1
            - ecc_squared/4
            - 3*ecc_squared*ecc_squared/64
            - 5*ecc_squared*ecc_squared*ecc_squared/256)*lat_rad 
           - (3*ecc_squared/8
              + 3*ecc_squared*ecc_squared/32
              + 45*ecc_squared*ecc_squared*ecc_squared/1024)*sin(2*lat_rad)
           + (15*ecc_squared*ecc_squared/256 + 45*ecc_squared*ecc_squared*ecc_squared/1024)*sin(4*lat_rad) 
           - (35*ecc_squared*ecc_squared*ecc_squared/3072)*sin(6*lat_rad))
    
    utm_easting = (k0*N*(A+(1-T+C)*A*A*A/6
                        + (5-18*T+T*T+72*C-58*ecc_prime_squared)*A*A*A*A*A/120)
                  + 500000.0)

    utm_northing = (k0*(M+N*tan(lat_rad)*(A*A/2+(5-T+9*C+4*C*C)*A*A*A*A/24
                                        + (61
                                           -58*T
                                           +T*T
                                           +600*C
                                           -330*ecc_prime_squared)*A*A*A*A*A*A/720)))

    if lat < 0:
        utm_northing = utm_northing + 10000000.0; #10000000 meter offset for southern hemisphere
    return (utm_zone, utm_easting, utm_northing)


def _utm_letter_designator(lat):
    """This routine determines the correct UTM letter designator for the given latitude
    returns 'Z' if latitude is outside the UTM limits of 84N to 80S
    Written by Chuck Gantz- chuck.gantz@globalstar.com"""

    if 84 >= lat >= 72: return 'X'
    elif 72 > lat >= 64: return 'W'
    elif 64 > lat >= 56: return 'V'
    elif 56 > lat >= 48: return 'U'
    elif 48 > lat >= 40: return 'T'
    elif 40 > lat >= 32: return 'S'
    elif 32 > lat >= 24: return 'R'
    elif 24 > lat >= 16: return 'Q'
    elif 16 > lat >= 8: return 'P'
    elif  8 > lat >= 0: return 'N'
    elif  0 > lat >= -8: return 'M'
    elif -8> lat >= -16: return 'L'
    elif -16 > lat >= -24: return 'K'
    elif -24 > lat >= -32: return 'J'
    elif -32 > lat >= -40: return 'H'
    elif -40 > lat >= -48: return 'G'
    elif -48 > lat >= -56: return 'F'
    elif -56 > lat >= -64: return 'E'
    elif -64 > lat >= -72: return 'D'
    elif -72 > lat >= -80: return 'C'
    else: return 'Z'	# if the Latitude is outside the UTM limits

def utm_to_ll(reference_ellipsoid, northing, easting, zone):
    """converts UTM coords to lat/long.  Equations from USGS Bulletin 1532 
    East Longitudes are positive, West longitudes are negative. 
    North latitudes are positive, South latitudes are negative
    lat and lon are in decimal degrees. 
    Written by Chuck Gantz- chuck.gantz@globalstar.com
    Converted to Python by Russ Nelson <nelson@crynwr.com>"""

    k0 = 0.9996
    a = _ellipsoid[reference_ellipsoid][_equatorial_radius]
    ecc_squared = _ellipsoid[reference_ellipsoid][_eccentricity_squared]
    e1 = (1-sqrt(1-ecc_squared))/(1+sqrt(1-ecc_squared))
    #northern_hemisphere; //1 for northern hemispher, 0 for southern

    x = easting - 500000.0 #remove 500,000 meter offset for longitude
    y = northing

    zone_letter = zone[-1]
    zone_number = int(zone[:-1])
    if zone_letter >= 'N':
        northern_hemisphere = 1  # point is in northern hemisphere
    else:
        northern_hemisphere = 0  # point is in southern hemisphere
        y -= 10000000.0         # remove 10,000,000 meter offset used for southern hemisphere

    lon_origin = (zone_number - 1)*6 - 180 + 3  # +3 puts origin in middle of zone

    ecc_prime_squared = (ecc_squared)/(1-ecc_squared)

    M = y / k0
    mu = M/(a*(1-ecc_squared/4-3*ecc_squared*ecc_squared/64-5*ecc_squared*ecc_squared*ecc_squared/256))

    phi1_rad = (mu + (3*e1/2-27*e1*e1*e1/32)*sin(2*mu) 
               + (21*e1*e1/16-55*e1*e1*e1*e1/32)*sin(4*mu)
               +(151*e1*e1*e1/96)*sin(6*mu))
    phi1 = phi1_rad*_rad2deg;

    N1 = a/sqrt(1-ecc_squared*sin(phi1_rad)*sin(phi1_rad))
    T1 = tan(phi1_rad)*tan(phi1_rad)
    C1 = ecc_prime_squared*cos(phi1_rad)*cos(phi1_rad)
    R1 = a*(1-ecc_squared)/pow(1-ecc_squared*sin(phi1_rad)*sin(phi1_rad), 1.5)
    D = x/(N1*k0)

    lat = phi1_rad - (N1*tan(phi1_rad)/R1)*(D*D/2-(5+3*T1+10*C1-4*C1*C1-9*ecc_prime_squared)*D*D*D*D/24
                                          +(61+90*T1+298*C1+45*T1*T1-252*ecc_prime_squared-3*C1*C1)*D*D*D*D*D*D/720)
    lat = lat * _rad2deg

    lon = (D-(1+2*T1+C1)*D*D*D/6+(5-2*C1+28*T1-3*C1*C1+8*ecc_prime_squared+24*T1*T1)
            *D*D*D*D*D/120)/cos(phi1_rad)
    lon = lon_origin + lon * _rad2deg
    return (lat, lon)


def parse_utm(utm_str):
    """Parse UTM coordinates from a string.

    utm_str should be a string of the form 'zh n e', where z is a zone
    number, h a hemisphere identifier ('N' or 'S') and n and e the
    northing and easting.  h may be omitted, in which case 'N' is
    assumed.

    Return value: dictionary with keys (zone, hemisphere, n, e).

    """
    default_hemisphere = 'N'
    utm_re = '^\W*([0-9][0-9])([NS]?)\W+([0-9]*[.]?[0-9]+)\W+([0-9]*[.]?[0-9]+)\W*$'
    m = re.match(utm_re, utm_str)
    if m == None:
        raise Exception('incorrectly formatted UTM string "' + utm_str)
    utm = {}
    utm['zone'] = int(m.group(1))
    utm['hemisphere'] = m.group(2)
    if utm['hemisphere'] == '':
        utm['hemisphere'] = default_hemisphere
    utm['n'] = float(m.group(3))
    utm['e'] = float(m.group(4))
    return utm


def utm_str_to_lonlat(utm_str):
    """Convert UTM coordinates in string form (see parse_utm) to a
    (longitude,latitude) pair.

    """
    utm = parse_utm(utm_str)
    (lat,lon) = utm_to_ll(23, utm['n'], utm['e'],
                          '%d%s'%(utm['zone'], utm['hemisphere']))
    return (lon,lat)



# general utility functions:

def group(property, lst):
    """Group a list into sublists based on equality of some property.

    Returns a list of sublists of lst, where every item of lst appears
    in exactly one sublist, and two items are in the same sublist iff
    the result of applying property (a function) to either of them
    gives the same result.

    """
    hash = {}
    for x in lst:
        p = property(x)
        if p in hash:
            hash[p].append(x)
        else:
            hash[p] = [x]
    return hash.values()


def avg(lst):
    """Return the average of the values in lst.  lst should be a list
    of numbers.

    """
    return float(sum(lst))/len(lst)


def subdict(d, keys):
    """Restriction of dictionary to some keys.

    d should be a dictionary and keys a list whose items are keys of
    d.  Returns a new dictionary object.

    """
    return dict([(k, d[k]) for k in keys])


def filter_dict(fun, d):
    """Filter a dictionary on values.

    Like the built-in filter, except that d is a dictionary, and fun
    is applied to each value. The result is a new dictionary
    containing those (key,value) pairs from d for which fun(value) is
    true.

    """
    return subdict(d, filter(lambda key: fun(d[key]), d))


def union_dict(*dicts):
    """Combine all arguments (which should be dictionaries) to a
    single dictionary. If several dictionaries contain the same key,
    the last is used.

    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def concat_list(objs):
    """Concatenate a list of lists."""
    return reduce(lambda a,b: a+b, objs, [])


# graph functions and classes:

def build_graph(db_results):
    """Make a Graph object based on the dictionaries resulting from
    get_data.

    """
    (netboxes,connections) = db_results
    graph = Graph()

    # fix coordinates (remove when database has (lon,lat)
    # coordinates), and create Node objects:
    netboxes = filter(lambda n: n['utm'] is not None, netboxes)
    for netbox in netboxes:
        (lon,lat) = utm_str_to_lonlat(netbox['utm'])
        graph.add_node(Node(netbox['netboxid'], lon, lat, netbox))

    # create Edge objects:
    for connection in connections.values():
        if (not connection['from_netboxid'] in graph.nodes or
            not connection['netboxid'] in graph.nodes):
            continue
        id = connection['netident']
        if id == None:
            id = str(connection['from_netboxid'])+'-'+str(connection['netboxid'])
        # TODO name?
        graph.add_edge(Edge(id,
                           graph.nodes[connection['from_netboxid']],
                           graph.nodes[connection['netboxid']],
                           connection))
    return graph


def simplify(graph, bounds, viewport_size, limit):
    """Remove and combine edges and nodes in a graph.

    Objects outside the interesting area (given by bounds) are
    removed, and those that are inside are combined so that they are
    not too close together (based on viewport_size and limit).

    Arguments:

    graph -- the Graph object to simplify.  It is destructively
    modified.

    bounds -- a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    viewport_size -- a dictionary with keys (width, height), the width
    and height of the user's viewport for the map in pixels.

    limit -- the minimum distance (in pixels) there may be between two
    points without them being collapsed to one.

    """
    area_filter(graph, bounds)
    create_rooms(graph)
    create_places(graph, bounds, viewport_size, limit)
    combine_edges(graph)


def area_filter(graph, bounds):
    """Restrict a graph to a geographical area.

    Removes objects outside bounds from graph.  An edge is retained if
    at least one of its endpoints is inside bounds.  A node is
    retained if it is an endpoint of such an edge (even if the node
    itself is outside bounds).

    Arguments:

    graph -- the Graph object to filter.  It is destructively
    modified.

    bounds -- a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    """
    def in_bounds(n):
        return \
            n.lon>=bounds['minLon'] and n.lon<=bounds['maxLon'] and \
            n.lat>=bounds['minLat'] and n.lat<=bounds['maxLat']
    def edge_connected_to(edge, nodehash):
        return edge.source.id in nodehash or edge.target.id in nodehash
    nodes = filter_dict(in_bounds, graph.nodes)
    edges = filter_dict(lambda edge: edge_connected_to(edge, nodes),
                        graph.edges)
    node_ids = (set(nodes.keys())
                | set([e.source.id for e in edges.values()])
                | set([e.target.id for e in edges.values()]))
    graph.nodes = subdict(graph.nodes, node_ids)
    graph.edges = edges


def create_rooms(graph):
    """Convert a graph of netboxes to a graph of rooms.

    graph is assumed to have one nodes representing netboxes.  These
    are combined so that there is one node for each room.  Each room
    node has a property 'netboxes' (available as
    roomnode.properties['netboxes']) which is a list of the original
    nodes it is based on.

    Arguments:

    graph -- a Graph object.  It is destructively modified.
    
    """
    collapse_nodes(graph,
                   group(lambda node: node.properties['roomid'],
                         graph.nodes.values()),
                   'netboxes')


def create_places(graph, bounds, viewport_size, limit):
    """Convert a graph of rooms to a graph of 'places'.

    A 'place' is a set of one or more rooms.  The position of a place
    is the average of the positions of its rooms.  The places are
    created such that no two places are closer than limit to each
    other.  Each place node has a property 'rooms' (available as
    placenode.properties['rooms']) which is a list of the room nodes
    it is based on.

    Arguments:

    graph -- a Graph object.  It is destructively modified.
    
    bounds -- a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    viewport_size -- a dictionary with keys (width, height), the width
    and height of the user's viewport for the map in pixels.

    limit -- the minimum distance (in pixels, integer) there may be
    between two points without them being collapsed to one.

    """
    # TODO may give division by zero with bogus input:
    lon_scale = float(viewport_size['width'])/(bounds['maxLon']-bounds['minLon'])
    lat_scale = float(viewport_size['height'])/(bounds['maxLat']-bounds['minLat'])
    def square(x): return x*x
    def distance(n1, n2):
        return sqrt(square((n1.lon-n2.lon)*lon_scale) +
                    square((n1.lat-n2.lat)*lat_scale))
    places = []
    for node in graph.nodes.values():
        for place in places:
            if distance(node, place[0]) < limit:
                place.append(node)
                break
        else:
            places.append([node])
    collapse_nodes(graph, places, 'rooms')


def collapse_nodes(graph, node_sets, subnode_list_name):
    """Collapse sets of nodes to single nodes.

    Replaces each set of nodes in node_sets by a single (new) node and
    redirects the edges correspondingly.  Edges which would end up
    having both endpoints in the same node are removed.

    Each new node is positioned at the average of the positions of the
    node set it represents.  It also gets a property containing the
    original nodes; the name of this property is given by
    subnode_list_name.

    Arguments:

    graph -- a Graph object.  It is destructively modified.

    node_sets -- a list of lists of nodes in graph.  Each node should
    occur in exactly one of the lists.

    subnode_list_name -- name for the property containing the original
    nodes a newly created node represents.

    """
    graph.nodes = {}
    nodehash = {}
    for s in node_sets:
        new_node = Node('cn[%s]' % (';'.join([str(n.id) for n in s])),
                        avg([n.lon for n in s]), avg([n.lat for n in s]),
                        {subnode_list_name: s})
        for n in s:
            nodehash[n.id] = new_node
        graph.add_node(new_node)
    for edge in graph.edges.values():
        edge.source = nodehash[edge.source.id]
        edge.target = nodehash[edge.target.id]
    graph.edges = filter_dict(lambda edge: edge.source != edge.target,
                              graph.edges)
    

def combine_edges(graph):
    """Combine edges with the same endpoints.

    Replaces the edges in graph with new edge objects, where any set
    of edges between the same two nodes is replaced by a single edge.
    Each new edge has a property 'subedges'
    (edge.properties['subedges']) which contains the original edge
    objects.

    Arguments:

    graph -- a Graph object.  It is destructively modified.

    """
    edges_by_node = dict([(id, set()) for id in graph.nodes])
    for edge in graph.edges.values():
        edges_by_node[edge.source.id].add(edge)
        edges_by_node[edge.target.id].add(edge)
    edge_sets = {}
    for edge in graph.edges.values():
        if edge.id in edge_sets:
            continue
        eset = list(edges_by_node[edge.source.id] & edges_by_node[edge.target.id])
        for e in eset:
            edge_sets[e] = eset

    # TODO: edges in a set may not have the same direction
    edges = map(
        lambda eset:
            Edge('ce[%s]' % (';'.join([e.id for e in eset])),
                 eset[0].source,
                 eset[0].target,
                 {'subedges': eset}),
        edge_sets.values())
    graph.edges = dict([(e.id,e) for e in edges])


class Node:
    """Representation of a node in a graph."""
    def __init__(self, id, lon, lat, properties):
        self.id = id
        self.lon = lon
        self.lat = lat
        self.properties = properties


class Edge:
    """Representation of an edge in a graph."""
    def __init__(self, id, source, target, properties):
        self.id = id
        self.source = source
        self.target = target
        self.properties = properties


class Graph:
    """Representation of a graph of geographical positions."""
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, n):
        self.nodes[n.id] = n

    def add_edge(self, e):
        self.edges[e.id] = e




# features:

def create_features(graph):
    nodes = map(create_node_feature, graph.nodes.values())
    edges = concat_list(map(create_edge_features, graph.edges.values()))
    return nodes+edges

_node_feature_properties = []
_edge_feature_properties = []

_place_popup_template = None
_network_popup_template = None

def template_from_config(filename):
    abs_filename = os.path.join(nav.path.sysconfdir, filename)
    file = open(abs_filename, 'r')
    content = file.read()
    file.close()
    return Template(content)

def load_place_popup_template():
    global _place_popup_template
    if _place_popup_template is None:
        _place_popup_template = \
            template_from_config('geomap/popup_place.html')

def load_network_popup_template():
    global _network_popup_template
    if _network_popup_template is None:
        _network_popup_template = \
            template_from_config('geomap/popup_network.html')


def create_node_feature(node):
    return Feature(node.id, 'node', Geometry('Point', [node.lon, node.lat]),
                   'blue', 12, create_node_popup(node),
                   subdict(node.properties, _node_feature_properties))

def create_node_popup(node):
    load_place_popup_template()
    content = _place_popup_template.render(Context({'place': node}))
    return Popup('popup-' + node.id, [300,250], content, True)

def create_edge_features(edge):
    popup = create_edge_popup(edge)
    properties = subdict(edge.properties, _edge_feature_properties)
    def make_feature(id_suffix, source_coords, target_coords):
        return Feature(str(edge.id)+id_suffix, 'edge',
                       Geometry('LineString', [source_coords, target_coords]),
                       'black', 5, popup, properties)
    source = [edge.source.lon, edge.source.lat]
    middle = [(edge.source.lon+edge.target.lon)/2,
              (edge.source.lat+edge.target.lat)/2]
    target = [edge.target.lon, edge.target.lat]
    return [make_feature('[1]', source, middle),
            make_feature('[2]', middle, target)]

def create_edge_popup(edge):
    load_network_popup_template()
    content = _network_popup_template.render(Context({'network': edge}))
    return Popup('popup-' + edge.id, [300,250], content, True)
    
class Feature:
    def __init__(self, id, type, geometry, color, size, popup, properties):
        self.id = id
        self.type = type
        self.geometry = geometry
        self.color = color
        self.size = size
        self.popup = popup
        self.properties = properties

class Geometry:
    def __init__(self, type, coordinates):
        self.type = type
        self.coordinates = coordinates
        
class Popup:
    def __init__(self, id, size, content, closable):
        self.id = id
        self.size = size
        self.content = content
        self.closable = closable



# GeoJSON:

def make_geojson(featurelist):
    geojson = {'type': 'FeatureCollection',
               'features': map(make_geojson_feature, featurelist)}
    return write_json(geojson)

def make_geojson_feature(feature):
    popup = None
    if feature.popup:
        popup = {'id': feature.popup.id,
                 'size': feature.popup.size,
                 'content': feature.popup.content,
                 'closable': feature.popup.closable}
    return {'type': 'Feature',
            'id': feature.id,
            'geometry':
                {'type': feature.geometry.type,
                 'coordinates': feature.geometry.coordinates},
            'properties':
                union_dict({'type': feature.type,
                            'color': feature.color,
                            'size': feature.size,
                            'popup': popup},
                           feature.properties)}

# should use json.dumps, but navdev has too old Python version
json_escapes = [('\\', '\\\\'),
               ('"', '\\"'),
               ('\n', '\\n'),
               ('\r', '\\r')]

def write_json(obj):
    if isinstance(obj, list):
        return '[' + ', '.join(map(write_json, obj)) + ']'
    if isinstance(obj, dict):
        return '{' + ', '.join(map(lambda kv: kv[0]+':'+kv[1],
                                   zip(map(write_json, obj.keys()),
                                       map(write_json, obj.values())))) + '}'
    if isinstance(obj, bool):
        if obj: return 'true'
        return 'false'
    if isinstance(obj, basestring):
        return '"%s"' % reduce(lambda s,esc: s.replace(esc[0], esc[1]),
                               json_escapes, obj)
    if isinstance(obj, int) or isinstance(obj, float):
        return str(obj)
    if obj == None:
        return 'null'
    return '"ERROR: unrecognized type ' + str(type(obj)) + '"'



# High-level functions

def get_geojson(db, bounds, viewport_size, limit):
    """Get GeoJSON output for given conditions.

    db is a database connection object.

    bounds is a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    viewport_size is a dictionary with keys (width, height), the width
    and height of the user's viewport for the map in pixels.

    limit is the minimum distance (in pixels, integer) there may be
    between two points without them being collapsed to one.

    Return value: GeoJSON data as a string.

    """
    graph = build_graph(get_data(db))
    simplify(graph, bounds, viewport_size, limit)
    return make_geojson(create_features(graph))

_formats = {
    'geojson': (make_geojson, 'application/json'),
#    'kml': (make_kml, 'application/vnd.google-earth.kml+xml')
    };

def get_formatted_data(db, format, bounds, viewport_size, limit):
    """Get GeoJSON output for given conditions.

    db is a database connection object.

    bounds is a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    viewport_size is a dictionary with keys (width, height), the width
    and height of the user's viewport for the map in pixels.

    limit is the minimum distance (in pixels, integer) there may be
    between two points without them being collapsed to one.

    Return value: GeoJSON data as a string.

    """
    graph = build_graph(get_data(db))
    simplify(graph, bounds, viewport_size, limit)
    if not format in _formats:
        raise Exception('unknown format %s' % format)
    formatter = _formats[format][0]
    return formatter(create_features(graph))

def format_mime_type(format):
    if not format in _formats:
        raise Exception('unknown format %s' % format)
    return _formats[format][1]




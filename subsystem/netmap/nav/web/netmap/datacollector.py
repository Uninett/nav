# -*- coding: UTF-8 -*-
#
# Copyright 2007 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Kristian Klette <klette@samfundet.no>

import sys
from common import *
import nav
import rrdtool
import cgi

log = unbuffered()

def getData(db_cursor = None):
    """Returns a dictionary containing the netboxes with their modules, ports and connections"""

    if not db_cursor:
        raise nav.errors.GeneralException("No db-cursor given")

    netboxes = {}
    connections = {}

    layer_2_query = """
SELECT gwportid,speed, ifindex, interface, sysname, netbox.netboxid, conn.*, nettype, netident, path || filename AS rrdfile,
2 AS layer, NULL AS from_swportid
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
WHERE gwportid <> from_gwportid
ORDER BY sysname, speed DESC
"""

    layer_3_query_1 = """
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

3 AS layer,
path || filename AS rrdfile,
nettype, netident,
NULL AS gwportid,
NULL AS from_gwportid,
NULL AS from_swportid

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

    layer_3_query_2 = """
SELECT DISTINCT ON (from_sysname, sysname)
swport.swportid AS from_swportid,
swport.speed,
swport.ifindex AS from_ifindex,
swport.interface AS from_interface,
netbox.sysname AS from_sysname,
netbox.netboxid AS from_netboxid,
swport.to_swportid AS to_swportid,
3 AS layer,
foo.*,
vlan.*,
path || filename AS rrdfile,
NULL AS gwportid,
NULL AS from_gwportid,
NULL AS from_swportid


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

    layer_3_query_3 = """
SELECT DISTINCT ON (from_sysname, sysname)

swport.swportid AS from_swportid,
swport.speed,
swport.ifindex AS from_ifindex,
swport.interface AS from_interface,
netbox.sysname AS from_sysname,
netbox.netboxid AS from_netboxid,
3 AS layer,
conn.*,
vlan.*,
path || filename AS rrdfile,
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

    db_cursor.execute(layer_2_query)
    results = db_cursor.dictfetchall()
    db_cursor.execute(layer_3_query_1)
    results.extend(db_cursor.dictfetchall())
    db_cursor.execute(layer_3_query_2)
    results.extend(db_cursor.dictfetchall())
    db_cursor.execute(layer_3_query_3)
    results.extend(db_cursor.dictfetchall())
    for res in results:
        if res['rrdfile']:
            data = get_rrd_link_load(res['rrdfile'])
            res['load'] = (data[0],data[1])
        else:
            res['load'] = (-1,-1)

        connection_id = "%s-%s" % (res['sysname'], res['from_sysname'])
        connection_rid = "%s-%s" % (res['from_sysname'], res['sysname'])
        if connection_id not in connections and connection_rid not in connections:
            connections[connection_id] = res
        else:
            for conn in connections.keys():
                if conn == connection_id or conn == connection_rid:
                    if connections[conn]['speed'] < res['speed']:
                        connections[conn] = res


    query = """
        SELECT DISTINCT ON (netboxid) *,  path || '/' || filename AS rrd
        FROM netbox
        LEFT JOIN room using (roomid)
        LEFT JOIN location USING (locationid)
        LEFT JOIN type USING (typeid)
        LEFT JOIN (SELECT netboxid,path,filename FROM rrd_file NATURAL JOIN rrd_datasource WHERE descr = 'cpu5min') AS rrd USING (netboxid)
        LEFT JOIN netmap_position USING (sysname)"""
    db_cursor.execute(query)
    netboxes = db_cursor.dictfetchall()
    for netbox in netboxes:
        if netbox['rrd']:
            try:
                netbox['load'] = rrdtool.fetch(netbox['rrd'], 'AVERAGE', '-r 5m', '-s -10m')[2][0][1]
            except:
                netbox['load'] = 'unknown'
        else:
            netbox['load'] = 'unknown'





    return (netboxes, connections)

def get_rrd_link_load(rrdfile):
    """ Returns the ds1 and ds2 fields of an rrd-file (ifInOctets, ifOutOctets)"""
    if not rrdfile:
        return (-1,-1)
    try:
        data = rrdtool.fetch(rrdfile, 'AVERAGE', '-r 5m','-s -10m')[2][0]
        return ((data[1])/1024.0, (data[0])/1024.0)
    except:
        return (-1,-1)


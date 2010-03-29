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

from nav.rrd import presenter
from nav.config import readConfig

log = unbuffered()

conf = readConfig('nav.conf')
domain_suffix = conf.get('DOMAIN_SUFFIX', None)

def getData(db_cursor = None):
    """Returns a dictionary containing the netboxes with their modules, ports and connections"""

    if not db_cursor:
        raise nav.errors.GeneralException("No db-cursor given")


    netboxes = {}
    connections = {}

    layer_3_query = """
SELECT DISTINCT ON (sysname, from_sysname)
    gwportprefixcount.count,
    gwport.gwportid,
    speed,
    ifindex,
    interface,
    sysname,
    netbox.netboxid,
    conn.*,
    nettype,
    netident,
    path ||'/'|| filename AS rrdfile,
    rrd_in.rrd_datasourceid AS rrd_datasource_in,
    rrd_out.rrd_datasourceid AS rrd_datasource_out,
    3 AS layer,
    NULL AS from_swportid,
    vlan.*
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
  LEFT JOIN rrd_datasource AS rrd_in  ON (rrd_file.rrd_fileid = rrd_in.rrd_fileid AND rrd_in.descr IN ('ifHCInOctets', 'ifInOctets'))
  LEFT JOIN rrd_datasource AS rrd_out ON (rrd_file.rrd_fileid = rrd_out.rrd_fileid AND rrd_out.descr IN ('ifHCOutOctets', 'ifOutOctets'))
WHERE gwport.gwportid <> from_gwportid AND vlan.nettype NOT IN ('static', 'lan') AND gwportprefixcount.count = 2
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
rrd_in.rrd_datasourceid AS rrd_datasource_in,
rrd_out.rrd_datasourceid AS rrd_datasource_out,
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
 LEFT JOIN rrd_datasource AS rrd_in  ON (rrd_file.rrd_fileid = rrd_in.rrd_fileid AND rrd_in.descr IN ('ifHCInOctets', 'ifInOctets'))
 LEFT JOIN rrd_datasource AS rrd_out ON (rrd_file.rrd_fileid = rrd_out.rrd_fileid AND rrd_out.descr IN ('ifHCOutOctets', 'ifOutOctets'))

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
rrd_in.rrd_datasourceid AS rrd_datasource_in,
rrd_out.rrd_datasourceid AS rrd_datasource_out,
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
LEFT JOIN rrd_datasource AS rrd_in  ON (rrd_file.rrd_fileid = rrd_in.rrd_fileid AND rrd_in.descr IN ('ifHCInOctets', 'ifInOctets'))
LEFT JOIN rrd_datasource AS rrd_out ON (rrd_file.rrd_fileid = rrd_out.rrd_fileid AND rrd_out.descr IN ('ifHCOutOctets', 'ifOutOctets'))

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
rrd_in.rrd_datasourceid AS rrd_datasource_in,
rrd_out.rrd_datasourceid AS rrd_datasource_out,
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
LEFT JOIN rrd_datasource AS rrd_in  ON (rrd_file.rrd_fileid = rrd_in.rrd_fileid AND rrd_in.descr IN ('ifHCInOctets', 'ifInOctets'))
LEFT JOIN rrd_datasource AS rrd_out ON (rrd_file.rrd_fileid = rrd_out.rrd_fileid AND rrd_out.descr IN ('ifHCOutOctets', 'ifOutOctets'))

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
        link_load = [-1,-1]
        if 'rrd_datasource_in' in res:
            link_load[0] = get_rrd_link_load(res['rrd_datasource_in'])
        if 'rrd_datasource_out' in res:
            link_load[1] = get_rrd_link_load(res['rrd_datasource_out'])
        res['load'] = link_load
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
        SELECT DISTINCT ON (netboxid) *,location.descr AS location,room.descr AS room,  path || '/' || filename AS rrd
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
        if netbox['sysname'].endswith(domain_suffix):
            netbox['sysname'] = netbox['sysname'][0:len(netbox['sysname'])-len(domain_suffix)]

    return (netboxes, connections)

def get_rrd_link_load(rrd_datasourceid):
    """Use the rrd presenter to fetch the average load for the last 10 minutes"""
    if not rrd_datasourceid:
        return -1
    try:
        rrd_presenter = presenter.presentation()
        rrd_presenter.addDs(rrd_datasourceid)
        rrd_presenter.timeLast('min', '10')
        return rrd_presenter.average()[0]
    except:
        return -1


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
    tmpConnections = {}
    connections = []

    # Get links from the database (give postgresql something to chew on :)
    #TODO: Remove union stuff as soon as we get a common port-model.
    query = """
SELECT DISTINCT ON (swport.swportid, to_swport)
        netbox.netboxid,
        connection.netboxid AS to_netboxid,
        netbox.sysname AS from_sysname,
        connection.to_sysname,
        CASE WHEN swport.speed > connection.to_speed
          THEN swport.speed
          ELSE connection.to_speed
        END AS speed,
        interface AS from_interface,
        connection.to_interface,
        module.model AS from_module_model,
        module.descr AS from_module_desc,
        connection.model AS to_module_model,
        connection.descr AS to_module_descr,
        rrd.path || '/' || rrd.filename AS rrdfile,
        CASE
          WHEN rrd.value::integer = swport.swportid THEN 'n'
          ELSE 'y'
        END AS reversed,
        netident,
        nettype,
        0 AS is_gwport,
        swport.swportid AS from_portid,
        connection.to_swport AS to_portid
FROM netbox
  JOIN module USING (netboxid)
  JOIN swport USING (moduleid)
  JOIN (
        SELECT  swport.swportid AS to_swport,
                swport.speed AS to_speed,
                netbox.sysname AS to_sysname,
                netbox.netboxid,
                interface AS to_interface,
                module.model,
                module.descr
        FROM swport
          JOIN module USING (moduleid)
          JOIN netbox USING (netboxid)
        ) AS connection
    ON (connection.to_swport = to_swportid)
    LEFT JOIN swportvlan USING(swportid)
    LEFT JOIN vlan USING (vlanid)
  LEFT JOIN (SELECT path, filename, value FROM rrd_file) AS rrd ON (rrd.value::integer = swport.swportid OR rrd.value::integer = connection.to_swport)

  UNION

SELECT DISTINCT ON (gwport.gwportid, to_gwport)
        netbox.netboxid,
        connection.netboxid AS to_netboxid,
        netbox.sysname AS from_sysname,
        connection.sysname AS to_sysname,
        CASE WHEN gwport.speed > connection.to_speed
          THEN gwport.speed
          ELSE connection.to_speed
        END AS speed,
        interface AS from_interface,
        connection.to_interface,
        module.model AS from_module_model,
        module.descr AS from_module_desc,
        connection.model AS to_module_model,
        connection.descr AS to_module_descr,
        rrd.path || '/' || rrd.filename AS rrdfile,
        CASE
                WHEN rrd.value::integer = gwport.gwportid THEN 'n'
                ELSE 'y'
        END AS reversed,
        netident,
        nettype,
        1 AS is_gwport,
        gwport.gwportid AS from_portid,
        connection.to_gwport AS to_portid
  FROM gwportprefix
   JOIN gwport USING (gwportid)
   JOIN module USING (moduleid)
   JOIN netbox USING (netboxid)
   JOIN (SELECT gwportprefix.prefixid,
                netbox.netboxid,
                gwport.gwportid AS to_gwport,
                speed AS to_speed,
                sysname,
                interface AS to_interface,
                module.model,
                module.descr
         FROM gwportprefix
           JOIN gwport USING (gwportid)
           JOIN module USING (moduleid)
           JOIN netbox USING (netboxid)
          ) AS connection
    ON (gwportprefix.prefixid = connection.prefixid AND connection.sysname != netbox.sysname)
    LEFT JOIN prefix ON (prefix.prefixid = gwportprefix.prefixid)
    LEFT JOIN vlan USING (vlanid)
   LEFT JOIN (SELECT path, filename, value FROM rrd_file) AS rrd ON (rrd.value::integer = gwport.gwportid OR rrd.value::integer = connection.to_gwport)
"""

    db_cursor.execute(query)
    results = db_cursor.dictfetchall()

    for res in results:
        data = get_rrd_link_load(res['rrdfile'])
        if data[0] == -1:
            if res['reversed'] == 'y':
                if res['is_gwport'] == 1:
                    db_cursor.execute("""SELECT path || '/' || filename FROM rrd_file WHERE key = 'gwport' AND value::integer = %s""" % res['from_portid'])
                else:
                    db_cursor.execute("""SELECT path || '/' || filename FROM rrd_file WHERE key = 'swport' AND value::integer = %s""" % res['from_portid'])
                res['reversed'] = 'n'
            else:
                if res['is_gwport'] == 1:
                    db_cursor.execute("""SELECT path || '/' || filename FROM rrd_file WHERE key = 'gwport' AND value::integer = %s""" % res['to_portid'])
                else:
                    db_cursor.execute("""SELECT path || '/' || filename AS file FROM rrd_file WHERE key = 'swport' AND value::integer = %s""" % res['to_portid'])
            new_rrd = db_cursor.fetchone()
            if new_rrd:
                data = get_rrd_link_load(new_rrd[0])
        if res['reversed'] == 'y':
            res['load'] = (data[1],data[0])
        else:
            res['load'] = (data[0],data[1])


    query = """
        SELECT DISTINCT ON (netboxid) *,  path || '/' || filename AS rrd
        FROM netbox
        JOIN room using (roomid)
        JOIN location USING (locationid)
        JOIN type USING (typeid)
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

    return (netboxes, results)

def get_rrd_link_load(rrdfile):
    """ Returns the ds1 and ds2 fields of an rrd-file (ifInOctets, ifOutOctets)"""
    if not rrdfile:
        return (-1,-1)
    try:
        data = rrdtool.fetch(rrdfile, 'AVERAGE', '-r 5m','-s -10m')[2][0]
        return ((data[1])/1024.0, (data[0])/1024.0)
    except:
        return (-1,-1)


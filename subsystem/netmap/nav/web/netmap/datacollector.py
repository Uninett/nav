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
        CASE WHEN swport.speed < connection.to_speed
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
          WHEN rrd.value = swport.swportid THEN 'n'
          ELSE 'y'
        END AS reversed
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
  LEFT JOIN (SELECT path, filename, value FROM rrd_file) AS rrd ON (rrd.value = swport.swportid OR rrd.value = connection.to_swport)

  UNION

SELECT DISTINCT ON (gwport.gwportid, to_gwport)
        netbox.netboxid,
        connection.netboxid AS to_netboxid,
        netbox.sysname AS from_sysname,
        connection.sysname AS to_sysname,
        CASE WHEN gwport.speed < connection.to_speed
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
                WHEN rrd.value = gwport.gwportid THEN 'n'
                ELSE 'y'
        END AS reversed
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
   LEFT JOIN (SELECT path, filename, value FROM rrd_file) AS rrd ON (rrd.value = gwport.gwportid OR rrd.value = connection.to_gwport)
    """

    db_cursor.execute(query)
    results = db_cursor.dictfetchall()

    for res in results:
        if res['rrdfile']:
            data = [a for a in rrdtool.fetch(res['rrdfile'], 'AVERAGE', '-r','350','-s','-10m')[2] if not None in a][0]
            if res['reversed'] == 'y':
                res['load'] = ((data[1]/8)/1024.0, (data[0]/8)/1024.0)
            else:
                res['load'] = ((data[0]/8)/1024.0, (data[1]/8)/1024.0)
        else:
            #TODO: Find rrd-data for the other interface - hard to do in the sql-query
            res['load'] = (-1,-1)

    query = """SELECT DISTINCT ON (netboxid) * FROM netbox
                JOIN room using (roomid)
                JOIN location USING (locationid)
                JOIN type USING (typeid)"""
    db_cursor.execute(query)
    netboxes = db_cursor.dictfetchall()

    return (netboxes, results)

# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
NAV snmptrapd handler plugin to handle traps from Weathergoose Climate Monitor.
Tested on a WxGoos-1 v2.80
"""

import logging
from nav.smidumps.itw_mib import MIB 

import nav.event
from nav.db import getConnection

logger = logging.getLogger('nav.snmptrapd.weathergoose')

# Define supported traps and relations
TRAPS = MIB['notifications']
NODES = MIB['nodes']
TRIPTYPE = "." + NODES['alarmTripType']['oid']
GOOSENAME = "." + NODES['climateName']['oid'] + '.1'
TRIGGERTRAPS = ['cmClimateTempCTRAP', 'cmClimateHumidityTRAP',
                'cmClimateAirflowTRAP', 'cmClimateLightTRAP',
                'cmClimateSoundTRAP']
CLEARTRAPS = ['cmClimateTempCCLEAR', 'cmClimateHumidityCLEAR',
                'cmClimateAirflowCLEAR', 'cmClimateLightCLEAR',
                'cmClimateSoundCLEAR']
CLIMATEOIDS = ['climateTempC', 'climateHumidity', 'climateAirflow',
               'climateLight', 'climateSound']
TRIPTYPES = {'0': 'None', '1': 'Low', '2': 'High', '3': 'Unplugged'}

# Alternative:
# EVENTTYPES = {('eventtypeid', 'description', True):
#               [alerttypes],
#               ...
#              }
EVENTTYPES = {'weathergoose_temperature':
              ['cmClimateTempCTRAP','cmClimateTempCCLEAR'],
              'weathergoose_humidity':
              ['cmClimateHumidityTRAP','cmClimateHumidityCLEAR'],
              'weathergoose_airflow':
              ['cmClimateAirflowTRAP','cmClimateAirflowCLEAR'],
              'weathergoose_light':
              ['cmClimateLightTRAP','cmClimateLightCLEAR'],
              'weathergoose_sound':
              ['cmClimateSoundTRAP','cmClimateSoundCLEAR'],
              }

def handleTrap(trap, config=None):
    """ This function is called from snmptrapd """

    conn = getConnection('default')
    cur = conn.cursor()
    cur.execute("SELECT netboxid, sysname, roomid FROM netbox WHERE ip = %s",
                (trap.agent,))

    if cur.rowcount < 1:
        logger.error("Could not find trapagent %s in database." %trap.agent)
        return False

    netboxid, sysname, roomid = cur.fetchone()

    # Initialize event-variables
    source = "snmptrapd"
    target = "eventEngine"
    eventtypeid = ""

    oid = trap.snmpTrapOID

    state = ''
    climatevalue = ""
    climatedescr = ""
    triptype = ""
    name = ""
    foundtrap = False

    # For each trap in predefined lists, see if it matches the oid in this
    # trap. If so, find the information we're interested in.
    for trigger in TRIGGERTRAPS + CLEARTRAPS:
        if oid != "." + TRAPS[trigger]['oid']:
            continue
        
        logger.info("Got %s" %TRAPS[trigger]['description'])
        foundtrap = True
        alerttype = trigger

        # Find eventtype
        for eventtype in EVENTTYPES:
            if trigger in EVENTTYPES[eventtype]:
                eventtypeid = eventtype
                break

        # Name of sending weathergoose
        name = trap.varbinds.get(GOOSENAME, 'N/A')
        # Type of alarm trip. 0 = None, 1 = Low, 2 = High, 3 = Unplugged
        triptype = TRIPTYPES.get(trap.varbinds[TRIPTYPE], 'N/A')

        # Find the values that triggered trap
        for c in CLIMATEOIDS:
            possiblekey = "." + NODES[c]['oid'] + '.1' # table has only one row
            if trap.varbinds.has_key(possiblekey):
                climatevalue = trap.varbinds[possiblekey]
                climatedescr = NODES[c]['description']
                break
                
        # Set eventstate based on type of trap
        if trigger in TRIGGERTRAPS:
            state = 's'
        elif trigger in CLEARTRAPS:
            state = 'e'

        break

    if not foundtrap:
        return False

    # Create and populate event
    e = nav.event.Event(source=source, target=target, netboxid=netboxid,
                        eventtypeid=eventtypeid, state=state)
    e['alerttype'] = alerttype
    e['triptype'] = triptype
    e['climatedescr'] = climatedescr
    e['climatevalue'] = climatevalue
    e['goosename'] = name
    e['sysname'] = sysname
    e['room'] = roomid

    logger.debug(e)

    # Post event on eventqueue
    try:
        e.post()
    except Exception, e:
        logger.error(e)
        return False

    return True


def initialize_eventdb():
    """ Populate the database with eventtype and alerttype information """
    h = {}
    for eventtype in EVENTTYPES:
        # We don't need description...? See alternate build of EVENTTYPES
        h[(eventtype, '', True)] = []
        for alerttype in EVENTTYPES[eventtype]:
            h[(eventtype, '', True)].append(
                (alerttype, TRAPS[alerttype]['description']))

    #logger.debug(h)

    try:
        nav.event.create_type_hierarchy(h)
    except Exception, e:
        logger.error(e)
        return False


initialize_eventdb()

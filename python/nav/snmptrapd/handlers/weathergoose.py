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
"""NAV snmptrapd handler plugin to handle traps from Weathergoose Climate
Monitor.

Tested on a WxGoos-1 v2.80

"""

import logging

import nav.event
from nav.db import getConnection

logger = logging.getLogger('nav.snmptrapd.weathergoose')

class WeatherGoose1(object):
    from nav.smidumps.itw_mib import MIB

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

    @classmethod
    def can_handle(cls, oid):
        return bool(cls.map_oid_to_trigger(oid))

    @classmethod
    def map_oid_to_trigger(cls, oid):
        for trigger in cls.TRIGGERTRAPS + cls.CLEARTRAPS:
            if oid == "." + cls.TRAPS[trigger]['oid']:
                return trigger

    def __init__(self, trap, netboxid, sysname, roomid):
        self.trap = trap
        self.netboxid = netboxid
        self.sysname = sysname
        self.roomid = roomid
        self.trigger = None

        self._parse()

    def _parse(self):
        oid = self.trap.snmpTrapOID
        self.trigger = self.map_oid_to_trigger(oid)
        if self.trigger:
            logger.info("Got %s" % self.TRAPS[self.trigger]['description'])
        else:
            raise Exception("This trap cannot be handled by this plugin")

        self.goosename = self.trap.varbinds.get(self.GOOSENAME, 'N/A')

        # Type of alarm trip. 0 = None, 1 = Low, 2 = High, 3 = Unplugged
        self.triptype = self.TRIPTYPES.get(self.trap.varbinds[self.TRIPTYPE],
                                           'N/A')

        self.climatevalue, self.climatedescr = self._get_trigger_values()

    def _get_trigger_values(self):
        """Returns the trigger variable's value and description.

        :returns: A tuple: (climatevalue, climatedescr)

        """
        for c in self.CLIMATEOIDS:
            possiblekey = "." + self.NODES[c]['oid'] + '.1' # table has only one row
            if self.trap.varbinds.has_key(possiblekey):
                return (self.trap.varbinds[possiblekey],
                        self.NODES[c]['description'])
        return (None, None)

    def post_event(self):
        # Create and populate event
        e = nav.event.Event(source="snmptrapd", target="eventEngine",
                            netboxid=self.netboxid,
                            eventtypeid=self._get_event_type(),
                            state=self._get_event_state())
        e['alerttype'] = self._get_alert_type()
        e['triptype'] = self.triptype
        e['climatedescr'] = self.climatedescr
        e['climatevalue'] = self.climatevalue
        e['goosename'] = self.goosename
        e['sysname'] = self.sysname
        e['room'] = self.roomid

        logger.debug(e)

        # Post event on eventqueue
        try:
            e.post()
        except Exception, e:
            logger.error(e)
            return False

        return True

    def _get_event_type(self):
        # Find eventtype
        for eventtype in self.EVENTTYPES:
            if self.trigger in self.EVENTTYPES[eventtype]:
                return eventtype

    def _get_event_state(self):
        if self.trigger in self.TRIGGERTRAPS:
            return 's'
        elif self.trigger in self.CLEARTRAPS:
            return 'e'
        else:
            return 'x'

    def _get_alert_type(self):
        return self.trigger #FIXME map to proper name


class WeatherGoose2(WeatherGoose1):
    from nav.smidumps.itw2_mib import MIB

    # Define supported traps and relations
    TRAPS = MIB['notifications']
    NODES = MIB['nodes']
    TRIPTYPE = "." + NODES['alarmTripType']['oid'] + '.0'

    TRIGGERTRAPS = ['cmClimateTempCNOTIFY', 'cmClimateHumidityNOTIFY',
                    'cmClimateAirflowNOTIFY', 'cmClimateLightNOTIFY',
                    'cmClimateSoundNOTIFY']

    # Alternative:
    # EVENTTYPES = {('eventtypeid', 'description', True):
    #               [alerttypes],
    #               ...
    #              }
    EVENTTYPES = {'weathergoose_temperature':
                  ['cmClimateTempCNOTIFY','cmClimateTempCCLEAR'],
                  'weathergoose_humidity':
                  ['cmClimateHumidityNOTIFY','cmClimateHumidityCLEAR'],
                  'weathergoose_airflow':
                  ['cmClimateAirflowNOTIFY','cmClimateAirflowCLEAR'],
                  'weathergoose_light':
                  ['cmClimateLightNOTIFY','cmClimateLightCLEAR'],
                  'weathergoose_sound':
                  ['cmClimateSoundNOTIFY','cmClimateSoundCLEAR'],
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

    oid = trap.snmpTrapOID
    for handler_class in WeatherGoose1, WeatherGoose2:
        if handler_class.can_handle(oid):
            handler = handler_class(trap, netboxid, sysname, roomid)
            return handler.post_event()

    return False

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

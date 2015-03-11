#
# Copyright (C) 2009 Norwegian University of Science and Technology
# Copyright (C) 2011 UNINETT AS
# Copyright (C) 2011 Narvik University College
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
"""NAV snmptrapd plugin to handle traps from IT Watchdogs' WeatherGoose
Climate Monitor, versions 1 and 2.

"""

import logging

import nav.event
from nav.db import getConnection

logger = logging.getLogger('nav.snmptrapd.weathergoose')


EVENTTYPES = {
    'weathergoose_temperature':
        ['cmClimateTempCTRAP', 'cmClimateTempCCLEAR', 'cmClimateTempCNOTIFY',
         'cmTempSensorTempCNOTIFY', 'cmTempSensorTempCCLEAR'],
    'weathergoose_humidity':
        ['cmClimateHumidityTRAP', 'cmClimateHumidityCLEAR',
         'cmClimateHumidityNOTIFY'],
    'weathergoose_airflow':
        ['cmClimateAirflowTRAP', 'cmClimateAirflowCLEAR',
         'cmClimateAirflowNOTIFY'],
    'weathergoose_light':
        ['cmClimateLightTRAP', 'cmClimateLightCLEAR', 'cmClimateLightNOTIFY'],
    'weathergoose_sound':
        ['cmClimateSoundTRAP', 'cmClimateSoundCLEAR', 'cmClimateSoundNOTIFY'],
    }

class WeatherGoose1(object):
    from nav.smidumps.itw_mib import MIB

    # Define supported traps and relations
    TRAPS = MIB['notifications']
    NODES = MIB['nodes']
    TRIPTYPE = "." + NODES['alarmTripType']['oid']
    GOOSENAME = "." + NODES['climateName']['oid'] + '.1'
    SUBID = None

    # Values in TRIGGERTRAPS and CLEARTRAPS are used as event types
    TRIGGERTRAPS = {
        'cmClimateTempCTRAP': 'weathergoose_temperature',
        'cmClimateHumidityTRAP': 'weathergoose_humidity',
        'cmClimateAirflowTRAP': 'weathergoose_airflow',
        'cmClimateLightTRAP': 'weathergoose_light',
        'cmClimateSoundTRAP': 'weathergoose_sound',
        }
    CLEARTRAPS = {
        'cmClimateTempCCLEAR': 'weathergoose_temperature',
        'cmClimateHumidityCLEAR': 'weathergoose_humidity',
        'cmClimateAirflowCLEAR': 'weathergoose_airflow',
        'cmClimateLightCLEAR': 'weathergoose_light',
        'cmClimateSoundCLEAR': 'weathergoose_sound',
        }
    CLIMATEOIDS = ['climateTempC', 'climateHumidity', 'climateAirflow',
                   'climateLight', 'climateSound', 'tempSensorTempC']
    SENSORNAMES = ['climateName']
    TRIPTYPES = {0: 'None', 1: 'Low', 2: 'High', 3: 'Unplugged'}

    @classmethod
    def can_handle(cls, oid):
        return bool(cls.map_oid_to_trigger(oid))

    @classmethod
    def map_oid_to_trigger(cls, oid):
        for trigger in cls.TRIGGERTRAPS.keys() + cls.CLEARTRAPS.keys():
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
            logger.info("Got %s", self.TRAPS[self.trigger]['description'])
        else:
            raise Exception("This trap cannot be handled by this plugin")

        self.goosename = self.trap.varbinds.get(self.GOOSENAME, 'N/A')

        self.triptype = self.TRIPTYPES.get(self.trap.varbinds[self.TRIPTYPE],
                                           'N/A')

        self.climatevalue, self.climatedescr = self._get_trigger_values()

    def _get_trigger_values(self):
        """Returns the trigger variable's value and description.

        :returns: A tuple: (climatevalue, climatedescr)

        """
        for c in self.CLIMATEOIDS:
            # table has only one row
            possiblekey = "." + self.NODES[c]['oid'] + '.1'
            if self.trap.varbinds.has_key(possiblekey):
                return (self.trap.varbinds[possiblekey],
                        self.NODES[c]['description'])
        return (None, None)

    def post_event(self):
        # Create and populate event
        e = nav.event.Event(source="snmptrapd", target="eventEngine",
                            netboxid=self.netboxid,
                            eventtypeid=self._get_event_type(),
                            subid=self._get_subid(),
                            state=self._get_event_state())
        e['alerttype'] = self._get_alert_type()
        e['triptype'] = self.triptype
        e['climatedescr'] = self.climatedescr
        e['climatevalue'] = self.climatevalue
        e['goosename'] = self.goosename
        e['sensorname'] = self._get_sensorname()
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
        for trigdict in (self.TRIGGERTRAPS, self.CLEARTRAPS):
            if self.trigger in trigdict:
                return trigdict[self.trigger]

    def _get_event_state(self):
        if self.trigger in self.TRIGGERTRAPS:
            return 's'
        elif self.trigger in self.CLEARTRAPS:
            return 'e'
        else:
            return 'x'

    def _get_alert_type(self):
        return self.trigger

    def _get_subid(self):
        """For external sensors we need a subid."""
        return self.trap.varbinds.get(self.SUBID)

    def _get_sensorname(self):
        for sensor_name in self.SENSORNAMES:
            oid = "." + self.NODES[sensor_name]['oid'] + '.1'
            value = self.trap.varbinds.get(oid)
            if value:
                return value

class WeatherGoose2(WeatherGoose1):
    from nav.smidumps.itw_mibv3 import MIB

    # Define supported traps and relations
    TRAPS = MIB['notifications']
    NODES = MIB['nodes']
    TRIPTYPE = "." + NODES['alarmTripType']['oid'] + '.0'
    GOOSENAME = "." + NODES['productFriendlyName']['oid'] + '.0'
    SUBID = "." + NODES['alarmInstance']['oid'] + '.0'
    SENSORNAMES = ['tempSensorName', 'climateName']

    # Values in TRIGGERTRAPS and CLEARTRAPS are used as event types
    TRIGGERTRAPS = {
        'cmClimateTempCNOTIFY': 'weathergoose_temperature',
        'cmClimateHumidityNOTIFY': 'weathergoose_humidity',
        'cmClimateAirflowNOTIFY': 'weathergoose_airflow',
        'cmClimateLightNOTIFY': 'weathergoose_light',
        'cmClimateSoundNOTIFY': 'weathergoose_sound',
        'cmTempSensorTempCNOTIFY': 'weathergoose_temperature',
        }

    CLEARTRAPS = WeatherGoose1.CLEARTRAPS.copy()
    CLEARTRAPS.update({'cmTempSensorTempCCLEAR':
                       'weathergoose_temperature', })


# pylint: disable=unused-argument
def handleTrap(trap, config=None):
    """ This function is called from snmptrapd """

    conn = getConnection('default')
    cur = conn.cursor()
    cur.execute("SELECT netboxid, sysname, roomid FROM netbox WHERE ip = %s",
                (trap.agent,))

    if cur.rowcount < 1:
        logger.error("Could not find trapagent %s in database.", trap.agent)
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
        eventdescr = (eventtype, '', True)
        h[eventdescr] = []
        for alerttype in EVENTTYPES[eventtype]:
            h[eventdescr].append((alerttype,
                                  _get_alert_description(alerttype)))

    try:
        nav.event.create_type_hierarchy(h)
    except Exception, e:
        logger.error(e)
        return False

def _get_alert_description(alerttype):
    for goose_ver in WeatherGoose1, WeatherGoose2:
        if alerttype in goose_ver.TRAPS:
            return goose_ver.TRAPS[alerttype]['description']

def initialize():
    """Initialize method for snmpdtrap daemon so it can initialize plugin
    after __import__
    """
    initialize_eventdb()

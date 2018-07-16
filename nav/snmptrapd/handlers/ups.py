#
# Copyright 2011 (C) Uninett AS
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
"""NAV snmptrapd handler plugin to handle on battery, battery-time and
off battery traps from APC and Eation UPSes.

It should also handle UPSes that are UPS-MIB (RFC1628) compliant like
Liebert UPSes,- but it looks like UPS-MIB do not have any alarm for
off battery.

"""

import logging
from nav.db import getConnection
from nav.event import Event
from nav.Snmp import Snmp

# Create logger with modulename here
logger = logging.getLogger('nav.snmptrapd.ups')

# upsonbattery traps
ONBATTERY = {'APC': ['.1.3.6.1.4.1.318.0.5'],
             'Eaton': ['.1.3.6.1.4.1.534.1.0.0.0.3',
                        # XUPS-MIB: xupstdOnBattery
                       '.1.3.6.1.4.1.534.1.11.4.1.0.3',
                       '.1.3.6.1.4.1.534.1.11.4.2.0.3'],
                        # MG-SNMP-UPS-MIB: upsmgOnBattery'
             'MGE': ['1.3.6.1.4.1.705.1.11.0.11'],
                        # UPS-MIB: upsAlarmOnBattery
             'RFC1628': ['.1.3.6.1.2.1.33.1.6.3.2'],
             }
BATTERYTIME = {'APC': ('.1.3.6.1.4.1.318.1.1.1.2.2.3.0', 'TIMETICKS'),
                        # XUPS-MIB: xupsBatTimeRemaining
               'Eaton': ('.1.3.6.1.4.1.534.1.2.1.0', 'SECONDS'),
                        # MG-SNMP-UPS-MIB: upsmgBatteryRemainingTime
               'MGE': ('1.3.6.1.4.1.705.1.5.1.0', 'SECONDS'),
                        # UPS-MIB: upsEstimatedMinutesRemaining
               'RFC1628': ('.1.3.6.1.2.1.33.1.2.3.0', 'MINUTES'),
            }

# upsoffbattery traps
OFFBATTERY = {'APC': ['.1.3.6.1.4.1.318.0.9'],
              'Eaton': ['.1.3.6.1.4.1.534.1.0.0.0.5',
                        # XUPS-MIBS: xupstdUtilityPowerRestored
                        '.1.3.6.1.4.1.534.1.11.4.1.0.5',
                        '.1.3.6.1.4.1.534.1.11.4.2.0.5'],
                        # MG-SNMP-UPS-MIB: upsmgReturnFromBattery
              'MGE': ['1.3.6.1.4.1.705.1.11.0.12'],
              }


# pylint: disable=unused-argument
def handleTrap(trap, config=None):
    """
    handleTrap is run by snmptrapd every time it receives a
    trap. Return False to signal trap was discarded, True if trap was
    accepted.
    """

    db = getConnection('default')

    # Event variables
    source = "snmptrapd"
    target = "eventEngine"
    eventtypeid = "upsPowerState"

    # Use the trap-object to access trap-variables and do stuff.
    for vendor in ONBATTERY.keys():
        if trap.snmpTrapOID in ONBATTERY[vendor]:
            logger.debug("Got ups on battery trap (%s)", vendor)

            # Get time to live
            try:
                batterytimeoid, format = BATTERYTIME[vendor]
                s = Snmp(trap.agent, trap.community)
                batterytime = s.get(batterytimeoid)
            except Exception as err:
                logger.info("Could not get battery time from %s: %s",
                            trap.agent, err)
                batterytime = False
            else:
                batterytime = format_batterytime(batterytime, format)
                logger.debug("batterytime: %s", batterytime)

            # Get netboxid from database
            c = db.cursor()
            c.execute("SELECT netboxid, sysname FROM netbox WHERE ip = %s",
                      (trap.agent,))
            if not c.rowcount > 0:
                logger.error("Could not find netbox in database, no event \
                will be posted")
                return False

            netboxid, sysname = c.fetchone()
            state = 's'

            # Create event-object, fill it and post event.
            e = Event(source=source, target=target, netboxid=netboxid,
                      eventtypeid=eventtypeid, state=state)
            e['alerttype'] = "upsOnBatteryPower"
            e['batterytime'] = batterytime
            e['sysname'] = sysname

            # Post event
            try:
                e.post()
            except Exception as e:
                logger.error(e)
                return False

            return True

    for vendor in OFFBATTERY.keys():
        if trap.snmpTrapOID in OFFBATTERY[vendor]:
            logger.debug("Got ups on utility power trap (%s)", vendor)

            # Get netboxid from database
            c = db.cursor()
            c.execute("SELECT netboxid, sysname FROM netbox WHERE ip = %s",
                      (trap.agent,))
            if not c.rowcount > 0:
                logger.error("Could not find netbox in database, no event \
                will be posted")
                return False

            netboxid, sysname = c.fetchone()
            state = 'e'

            # Create event-object, fill it and post event.
            e = Event(source=source, target=target, netboxid=netboxid,
                      eventtypeid=eventtypeid, state=state)
            e['sysname'] = sysname
            e['alerttype'] = "upsOnUtilityPower"

            # Post event
            try:
                e.post()
            except Exception as e:
                logger.error(e)
                return False

            return True

    return False


def format_batterytime(timeunit, format):
    if isinstance(timeunit, int):
        seconds = timeunit
        if 'MINUTES' == format:
            # UPS-MIB
            seconds = (timeunit * 60)
        if 'TIMETICKS' == format:
            seconds = timeunit / 100
        return "%sh:%sm" %(int(seconds / 60 / 60), (seconds/60) % 60)


# This function is a nice to run to make sure the event and alerttypes
# exist in the database if you post events for alerting.
def verifyEventtype():
    """
    Safe way of verifying that the event- and alarmtypes exist in the
    database. Should be run when module is imported.
    """

    db = getConnection('default')
    c = db.cursor()

    # NB: Remember to replace the values with the one you need.

    sql = """
    INSERT INTO eventtype (
    SELECT 'upsPowerState','UPS running on battery or utility power','y'
    WHERE NOT EXISTS (
    SELECT * FROM eventtype WHERE eventtypeid = 'upsPowerState'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'upsPowerState',
    'upsOnBatteryPower', 'Ups running on battery power' WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'upsOnBatteryPower'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'upsPowerState',
    'upsOnUtilityPower', 'Ups running on utility power' WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'upsOnUtilityPower'));
    """

    queries = sql.split(';')
    for q in queries:
        if len(q.rstrip()) > 0:
            c.execute(q)

    db.commit()


def initialize():
    """Initialize method for snmpdtrap daemon so it can initialize plugin
    after __import__
    """
    verifyEventtype()

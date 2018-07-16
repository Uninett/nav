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
"""NAV snmptrapd handler plugin to handle LINKUP and LINKDOWN traps from
network equipment.

"""
import logging
import nav.errors

from nav.db import getConnection
from nav.event import Event

_logger = logging.getLogger('nav.snmptrapd.linkupdown')


def handleTrap(trap, config=None):
    """Handles LINKUP/LINKDOWN traps, discarding anything else"""

    # Linkstate-traps are generictypes. Check for linkup/down and post
    # events on eventq.
    if not trap.genericType in ['LINKUP', 'LINKDOWN']:
        return False

    _logger.debug("Module linkupdown got trap %s %s",
                  trap.snmpTrapOID, trap.genericType)

    ifindex = get_ifindex_from_trap(trap, config)
    netboxid = find_corresponding_netbox(trap.agent)
    if not netboxid:
        _logger.error("Could not find agent %s in database", trap.agent)
        return False
    (interfaceid, deviceid, modulename, ifname,
     ifalias) = get_interface_details(netboxid, ifindex)

    # Check for traptype, post event on queue
    down = trap.genericType == 'LINKDOWN'
    success = post_link_event(down,
                              netboxid, deviceid, interfaceid,
                              modulename, ifname, ifalias)
    if success:
        _logger.info("Interface %s (%s) on %s is %s.",
                     ifname, ifalias, trap.agent, 'down' if down else 'up')
    return success


def get_ifindex_from_trap(trap, config):
    """Gets the interface index from the trap's varbinds"""
    port_oid = config.get('linkupdown', 'portOID')
    for key, value in trap.varbinds.items():
        if key.find(port_oid) >= 0:
            return value
    return ""


def find_corresponding_netbox(ipaddr):
    """Find a netboxid corresponding to the given ip address"""
    cursor = getConnection('default').cursor()
    try:
        query = "SELECT netboxid FROM netbox WHERE ip = %s"
        cursor.execute(query, (ipaddr,))
        row = cursor.fetchone()
        if row:
            return row[0]

    except Exception:
        _logger.exception("Unexpected error when querying database")
    finally:
        _logger.debug("Query was: %s", cursor.query)


def get_interface_details(netboxid, ifindex):
    """Get interfaceid, deviceid, modulename, ifname, ifalias for interface"""
    idquery = """SELECT
                   interfaceid, module.deviceid,
                   module.name AS modulename,
                   interface.ifname, interface.ifalias
                 FROM netbox
                 JOIN interface USING (netboxid)
                 LEFT JOIN module USING (moduleid)
                 WHERE netbox.netboxid=%s AND ifindex = %s"""
    _logger.debug(idquery)
    cursor = getConnection('default').cursor()
    try:
        cursor.execute(idquery, (netboxid, ifindex))
    except nav.db.driver.ProgrammingError:
        _logger.exception("Unexpected error when querying database")
    else:
        if cursor.rowcount > 0:
            return cursor.fetchone()
        else:
            _logger.debug('Could not find ifindex %s on %s',
                          ifindex, netboxid)

    return (None, None, None, None, None)


def post_link_event(down, netboxid, deviceid, interfaceid, modulename, ifname,
                    ifalias):
    """Posts a linkState event on the event qeueue"""
    state = 's' if down else 'e'

    event = Event(source="snmptrapd", target="eventEngine",
                  netboxid=netboxid, deviceid=deviceid,
                  subid=interfaceid, eventtypeid="linkState",
                  state=state)
    event['alerttype'] = 'linkDown' if down else 'linkUp'
    event['module'] = modulename or ''
    event['interface'] = ifname or ''
    event['ifalias'] = ifalias or ''

    try:
        event.post()
    except nav.errors.GeneralException:
        _logger.exception("Unexpected exception while posting event")
        return False
    else:
        return True


def verify_event_type():
    """
    Safe way of verifying that the event- and alarmtypes exist in the
    database. Should be run when module is imported.
    """
    connection = getConnection('default')
    cursor = connection.cursor()

    sql = """
    INSERT INTO eventtype (
    SELECT 'linkState','Tells us whether a link is up or down.','y'
    WHERE NOT EXISTS (
    SELECT * FROM eventtype WHERE eventtypeid = 'linkState'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'linkState', 'linkUp',
    'Link active'
    WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'linkUp'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'linkState', 'linkDown',
    'Link inactive'
    WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'linkDown'));
    """

    queries = sql.split(';')
    for query in queries:
        if len(query.rstrip()) > 0:
            cursor.execute(query)

    connection.commit()


def initialize():
    """Initialize method for snmpdtrap daemon so it can initialize plugin
    after __import__
    """
    verify_event_type()

#
# Copyright 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV snmptrapd handler plugin for Juniper syslog traps"""

# From JUNIPER-SYSLOG-MIB:
#
#     jnxSyslogTrap NOTIFICATION-TYPE
#         OBJECTS { jnxSyslogEventName, jnxSyslogTimestamp,
#                   jnxSyslogSeverity, jnxSyslogFacility,
#                   jnxSyslogProcessId, jnxSyslogProcessName,
#                   jnxSyslogHostName, jnxSyslogMessage
#                 }
#         STATUS  current
#         DESCRIPTION
#             "Notification of a generated syslog message. Apart from
#              the jnxSyslogTrap objects, this notification can include
# 	     one or more attribute-value pairs. The attribute-value
# 	     pairs shall be identified by objects jnxSyslogAvAttribute
# 	     and jnxSyslogAvValue."
#         ::= { jnxSyslogNotificationPrefix 1 }

import logging
from collections import defaultdict
from pprint import pformat
from typing import Any, Optional, Union

import nav.errors
from nav.db import getConnection
from nav.event import Event
from nav.oids import OID
from nav.smidumps import get_mib
from nav.snmptrapd.trap import SNMPTrap, AgentNetbox

_logger = logging.getLogger("nav.snmptrapd.sysloghandler")


MIB = get_mib("JUNIPER-SYSLOG-MIB")
TRAPS = MIB["notifications"]
NODES = MIB["nodes"]
JNX_SYSLOG_TRAP = TRAPS["jnxSyslogTrap"]["oid"]
OID_MAP: dict[OID, str] = {node["oid"]: name for name, node in NODES.items()}
STATE_ALERT_TYPE_MAPPING = {
    "INELIGIBLE": "haSrgStateIneligible",
    "BACKUP": "haSrgStateBackup",
    "ACTIVE": "haSrgStateActive",
}


def handleTrap(trap, config=None):
    """Handles JUNIPER-SYSLOG-MIB traps"""

    if OID(trap.snmpTrapOID) not in (JNX_SYSLOG_TRAP,):
        return False

    # Ignore traps from unknown netboxes
    netbox: Optional[AgentNetbox] = trap.netbox
    if not netbox:
        _logger.info("Ignoring syslog trap from unknown netbox")
        return False

    _logger.debug(
        "Module sysloghandler got trap %s %s", trap.snmpTrapOID, trap.genericType
    )

    trap_vars = _map_trap_variables(trap)
    trap_attributes = _map_trap_attributes(trap_vars)
    event_name = trap_vars["jnxSyslogEventName"][0][1]
    message = trap_vars["jnxSyslogMessage"][0][1]
    _logger.info("Got jnxSyslogTrap from %s:\n%s", netbox, pformat(trap_vars))

    if event_name == "JSRPD_HA_SRG_STATE_CHANGE":
        return _handle_ha_srg_change_trap(netbox, trap_attributes, message)

    _logger.debug(
        "jnxSyslogTrap from %s ignored since it has for us irrelevant event name '%s'",
        netbox.sysname,
        event_name,
    )
    return False


def _map_trap_variables(
    trap: SNMPTrap,
) -> dict[Union[str, OID], list[tuple[Optional[OID], Any]]]:
    """NAV/snmptrapd provides very poor utilities for symbolic parsing of MIB data, so
    we do it here instead. Even if all the OIDs and values of an SNMP trap's varbinds
    have been converted to strings before the plugin receives them
    """
    variables = defaultdict(list)

    for oid, value in trap.varbinds.items():
        oid = OID(oid)
        name, instance = _break_down_oid(oid)
        if name:
            variables[name].append((instance, value))
        else:
            # Could not translate (within this MIB, at least)
            variables[oid].append((oid, value))

    return variables


def _break_down_oid(oid: OID) -> tuple[Optional[str], Optional[OID]]:
    # Try to match an OID prefix by processing the longest OIDs first:
    sorted_map = sorted(OID_MAP.items(), key=lambda item: len(item[0]), reverse=True)

    for candidate, name in sorted_map:
        if candidate.is_a_prefix_of(oid):
            instance = oid.strip_prefix(candidate)
            return name, instance
        elif candidate == oid:
            return name, None
    return None, None


def _map_trap_attributes(
    trap_vars: dict[Union[str, OID], list[tuple[Optional[OID], Any]]],
) -> dict[Any, Any]:
    attributes = trap_vars["jnxSyslogAvAttribute"]
    values = trap_vars["jnxSyslogAvValue"]

    mapped_attributes = dict()

    for i in range(len(attributes)):
        mapped_attributes[attributes[i][1]] = values[i][1]

    return mapped_attributes


def _handle_ha_srg_change_trap(
    netbox: AgentNetbox, trap_attributes: dict[str, str], message: str
):
    """Handles relevant high-availability services-redundancy-group state changes"""
    if trap_attributes["new-state"] == "INELIGIBLE" or (
        trap_attributes["old-state"] in ["HOLD", "INELIGIBLE"]
        and trap_attributes["new-state"]
        in [
            "BACKUP",
            "ACTIVE",
        ]
    ):
        return _post_ha_srg_state_change_event(
            netboxid=netbox.netboxid,
            srg_id=trap_attributes["srg-id"],
            old_state=trap_attributes["old-state"],
            new_state=trap_attributes["new-state"],
            description=message,
        )

    _logger.debug(
        "jnxSyslogTrap from %s ignored since it has for us irrelevant change from old state '%s' to new state '%s'",  # noqa: E501
        netbox.sysname,
        trap_attributes["old-state"],
        trap_attributes["new-state"],
    )
    return False


def _post_ha_srg_state_change_event(
    netboxid: int, srg_id: str, old_state: str, new_state: str, description: str
):
    """Posts a haSrgStateChange event on the event queue"""
    state = "s" if new_state == "INELIGIBLE" else "e"

    event = Event(
        source="snmptrapd",
        target="eventEngine",
        netboxid=netboxid,
        subid=srg_id,
        eventtypeid="haSrgStateChange",
        state=state,
    )
    event["alerttype"] = STATE_ALERT_TYPE_MAPPING[new_state]
    event["description"] = description or ""
    event["old_state"] = old_state
    event["new_state"] = new_state

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
    connection = getConnection("default")
    cursor = connection.cursor()

    sql = """
    INSERT INTO eventtype (
    SELECT 'haSrgStateChange',
    'Tells us what the high-availability services-redundancy-group state is.','y'
    WHERE NOT EXISTS (
    SELECT * FROM eventtype WHERE eventtypeid = 'haSrgStateChange'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'haSrgStateChange',
    'haSrgStateIneligible',
    'High-availability services-redundancy-group state ineligible'
    WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'haSrgStateIneligible'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'haSrgStateChange', 'haSrgStateActive',
    'High-availability services-redundancy-group state active'
    WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'haSrgStateActive'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'haSrgStateChange', 'haSrgStateBackup',
    'High-availability services-redundancy-group state backup'
    WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'haSrgStateBackup'));
    """

    queries = sql.split(";")
    for query in queries:
        if query.rstrip():
            cursor.execute(query)

    connection.commit()


def initialize():
    """Initialization called at module import time"""
    verify_event_type()

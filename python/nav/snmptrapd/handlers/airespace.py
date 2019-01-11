#
# Copyright (C) 2018 Uninett AS
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
"""NAV snmptrapd handler plugin to handle AP assocation traps from a Cisco
Wireless LAN Controller.

All values from AIRESPACE-WIRELESS-MIB

"""

from nav.smidumps.airespace_wireless_mib import MIB
from nav.event import Event
import logging

logger = logging.getLogger('nav.snmptrapd.airespace')

NODES = MIB['nodes']
TRAPS = MIB['notifications']


# pylint: disable=unused-argument
def handleTrap(trap, config=None):

    # Two interesting traps:
    # bsnAPAssociated and bsnAPDisassociated

    if trap.snmpTrapOID not in ["." + TRAPS['bsnAPAssociated']['oid'],
                                "." + TRAPS['bsnAPDisassociated']['oid']]:
        return False

    logger.debug("Got trap %s", trap.snmpTrapOID)

    # Eventvariables:
    source = "snmptrapd"
    target = "eventEngine"
    eventtypeid = 'apState'
    alerttype = ""
    state = ""
    subid = ""
    mac = ""
    apname = ""

    # Name of AP: bsnAPName
    # MAC: bsnAPMacAddrTrapVariable
    for key, val in trap.varbinds.items():
        if key.find(NODES['bsnAPName']['oid']) >= 0:
            apname = val
            logger.debug("Set apname to %s", apname)
        elif key.find(NODES['bsnAPMacAddrTrapVariable']['oid']) >= 0:
            mac = val
            subid = mac

    if trap.snmpTrapOID == "." + TRAPS['bsnAPAssociated']['oid']:
        state = 'e'
        alerttype = 'apUp'
    elif trap.snmpTrapOID == "." + TRAPS['bsnAPDisassociated']['oid']:
        state = 's'
        alerttype = 'apDown'

    e = Event(source=source, target=target, subid=subid,
              eventtypeid=eventtypeid, state=state)
    e['alerttype'] = alerttype
    e['mac'] = mac
    e['apname'] = apname

    logger.debug(e)

    try:
        e.post()
    except Exception as e:
        logger.error(e)
        return False

    return True

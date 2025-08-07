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

import logging

from nav.smidumps import get_mib
from nav.event import Event

_logger = logging.getLogger(__name__)

MIB = get_mib('AIRESPACE-WIRELESS-MIB')
NODES = MIB['nodes']
TRAPS = MIB['notifications']


def handleTrap(trap, config=None):
    # Two interesting traps:
    # bsnAPAssociated and bsnAPDisassociated

    if trap.snmpTrapOID not in [
        str(TRAPS['bsnAPAssociated']['oid']),
        str(TRAPS['bsnAPDisassociated']['oid']),
    ]:
        return False

    _logger.debug("Got trap %s", trap.snmpTrapOID)

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
        if key.find(str(NODES['bsnAPName']['oid'])) >= 0:
            apname = val
            _logger.debug("Set apname to %s", apname)
        elif key.find(str(NODES['bsnAPMacAddrTrapVariable']['oid'])) >= 0:
            mac = val
            subid = mac

    if trap.snmpTrapOID == str(TRAPS['bsnAPAssociated']['oid']):
        state = 'e'
        alerttype = 'apUp'
    elif trap.snmpTrapOID == str(TRAPS['bsnAPDisassociated']['oid']):
        state = 's'
        alerttype = 'apDown'

    e = Event(
        source=source, target=target, subid=subid, eventtypeid=eventtypeid, state=state
    )
    e['alerttype'] = alerttype
    e['mac'] = mac
    e['apname'] = apname

    _logger.debug(e)

    try:
        e.post()
    except Exception as e:  # noqa: BLE001
        _logger.error(e)
        return False

    return True

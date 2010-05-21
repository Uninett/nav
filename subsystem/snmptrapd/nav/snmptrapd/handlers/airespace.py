"""
NAV snmptrapd handler plugin to handle AP assocation traps from a Cisco
-Wireless LAN Controller.

All values from AIRESPACE-WIRELESS-MIB
"""
from nav.smidumps.airespace_wireless_mib import MIB
from nav.event import Event
import logging

logger = logging.getLogger('nav.snmptrapd.airespace')

NODES = MIB['nodes']
TRAPS = MIB['notifications']

def handleTrap(trap, config=None):

    # Two interesting traps:
    # bsnAPAssociated and bsnAPDisassociated

    if trap.snmpTrapOID not in [ "." + TRAPS['bsnAPAssociated']['oid'],
                                 "." + TRAPS['bsnAPDisassociated']['oid']
                                 ]:

        return False


    logger.debug("Got trap %s" %trap.snmpTrapOID)

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
            logger.debug("Set apname to %s" %apname)
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
    except Exception, e:
        logger.error(e)
        return False

    return True

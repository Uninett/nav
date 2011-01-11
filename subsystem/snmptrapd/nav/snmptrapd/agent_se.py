#
# Copyright 2007 (C) Norwegian University of Science and Technology
# Copyright 2010 (C) UNINETT
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
"""PySNMP-SE specific trap agent functions."""
import select
import logging

from pysnmp.mapping.udp.role import Agent
from pysnmp.proto.api import alpha

from trap import SNMPTrap

logger = logging.getLogger(__name__)

class TrapListener:
    def __init__(self, iface):
        """Initializes a TrapListener.

        iface -- A (srcadr, port) tuple.

        """
        self.iface = iface
        self._agent = Agent(ifaces=[iface])

    def open(self):
        """Opens the server socket at port 162."""
        self._agent.open()

    def close(self):
        """Closes the server socket."""
        self._agent.close()

    def _decode(self, request, src):
        """Decodes incoming trap to an SNMPTrap object."""
        meta_req = alpha.MetaMessage()
        meta_req.decode(request)
        message = meta_req.values()[0]
        pdu = message.apiAlphaGetPdu()

        agent_addr = None
        type = None
        generic_type = None

        varbinds = pdu.apiAlphaGetVarBindList()
        # Prepare variables for making of SNMPTrap-object
        if message.apiAlphaGetVersion() == 0:
            agent_addr = pdu.apiAlphaGetAgentAddr().get()
            # There's no doc on what type is supposed to indicate, and it's not
            # used by any current handlers, so this setting is just guesswork
            # (from looking at the PySNMP v2 version of this module)
            type = str(pdu.tagClass)
            uptime = str(pdu.apiAlphaGetTimeStamp().get())
            # Create snmpoid based on RFC2576
            snmp_trap_oid, generic_type = transform(pdu)
        else:
            # We expect the two first varbinds to be the uptime and trap oids
            time_oid, time_val = varbinds.pop(0).apiAlphaGetOidVal()
            trap_oid_oid, trap_oid = varbinds.pop(0).apiAlphaGetOidVal()

            uptime = time_val.get()
            snmp_trap_oid = trap_oid.get()

        # Dump varbinds to debug log
        logger.debug("varbinds: %r", varbinds)

        # Add remaining varbinds to dict
        varbind_dict = {}
        for (oid, val) in [v.apiAlphaGetOidVal() for v in varbinds]:
            key = oid_to_str(oid.get())
            varbind_dict[key] = str(val.get())

        community = message.apiAlphaGetCommunity().get()
        version = str(message.apiAlphaGetVersion().get() + 1)
        src = src[0]
        snmp_trap_oid = oid_to_str(snmp_trap_oid)

        # Create trap object, let callback decide what to do with it.
        trap = SNMPTrap(str(src), agent_addr or str(src), type, generic_type,
                        snmp_trap_oid, uptime, community, version,
                        varbind_dict)
        return trap


    def listen(self, community, callback):
        """Listens for and dispatches incoming traps to callback.

        Any exceptions that occur, except SystemExit, are logged and
        subsequently ignored to avoid taking down the entire snmptrapd
        process by accident.

        """
        while 1:
            try:
                (request, src) = self._agent.receive()
            except SystemExit:
                raise
            except Exception, why:
                logger.exception("Unknown exception while receiving snmp trap")
                continue

            if not request:
                # Just resume loop if we timed out
                continue

            try:
                trap = self._decode(request, src)
            except Exception, why:
                logger.exception("Unknown exception while decoding snmp trap "
                                 "packet from %r, ignoring trap", src)
                logger.debug("Packet content: %r", request)
                continue
            else:
                callback(trap)


def transform(pdu):
    """Transforms from SNMP-v1 to SNMP-v2 format. Returns snmpTrapOID and
    genericType as string.

    """
    enterprise = pdu.apiAlphaGetEnterprise().get()
    generic = pdu.apiAlphaGetGenericTrap()

    # According to RFC2576 "Coexistence between Version 1, Version 2,
    # and Version 3 of the Internet-standard Network Management
    # Framework", we build snmpTrapOID from the snmp-v1 trap by
    # combining enterprise + 0 + specific trap parameter IF the
    # generic trap parameter is 6. If not, the traps are defined as
    # 1.3.6.1.6.3.1.1.5 + (generic trap parameter + 1)
    if generic.get() == 6:
        snmp_trap_oid = enterprise + [0, pdu.apiAlphaGetSpecificTrap().get()]
    else:
        snmp_trap_oid = [1,3,6,1,6,3,1,1,5] + [generic.get() + 1]

    type_name_map = dict(enumerate(generic.verboseTraps))
    if generic.get() < len(type_name_map):
        generic_type = type_name_map[generic.get()].upper()
    else:
        generic_type = str(generic.get())

    return snmp_trap_oid, generic_type

def oid_to_str(oid):
    """Converts an OID object/tuplet to a dotted string representation.

    This is needed since that's what snmptrapd expects.

    """
    if not isinstance(oid, basestring):
        oid = "." + ".".join(str(i) for i in oid)
    return oid

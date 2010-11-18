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
"""PySNMP v2 specific trap agent functions."""
import select
import logging

from pysnmp import asn1, v1, v2c
from pysnmp import role

from trap import SNMPTrap

logger = logging.getLogger(__name__)

class TrapListener:
    def __init__(self, iface):
        """Initializes a TrapListener.

        iface -- A (srcadr, port) tuple.

        """
        self.iface = iface
        self._agent = role.manager(iface=iface)

    def open(self):
        """Opens the server socket at port 162."""
        self._agent.open()

    def close(self):
        """Closes the server socket."""
        self._agent.close()

    def listen(self, community, callback):
        """Listens for and dispatches incoming traps to callback."""
        # Listen for SNMP messages from remote SNMP managers
        while 1:
            # Receive a request message
            try:
                (question, src) = self._agent.receive()
            except select.error, why:
                # resume loop if a signal interrupted the receive operation
                if why.args[0] == 4: # error 4 = system call interrupted
                    continue
                else:
                    raise why
            if question is None:
                continue

            try:
                # Decode request of any version
                (req, rest) = v2c.decode(question)

                # Decode BER encoded Object IDs.
                oids = map(lambda x: x[0], map(asn1.OBJECTID().decode,
                                               req['encoded_oids']))

                # Decode BER encoded values associated with Object IDs.
                vals = map(lambda x: x[0](), map(asn1.decode, req['encoded_vals']))

            except Exception, why:
                # We must not die because of any malformed packets; log
                # and ignore any exception
                logger.exception("Exception while decoding snmp trap packet from "
                                 "%r, ignoring trap", src)
                logger.debug("Packet content: %r", question)
                continue

            agent = None
            type = None
            genericType = None

            varbinds = {}
            # Prepare variables for making of SNMPTrap-object
            if req['version'] == 0:
                agent = str(req['agent_addr'])
                type = str(req['tag'])
                uptime = str(req['time_stamp'])
                # Create snmpoid based on RFC2576
                snmpTrapOID, genericType = transform(req)
            else:
                uptime = vals.pop(0)
                oids.pop(0)
                snmpTrapOID = vals.pop(0)
                oids.pop(0)

            # Add varbinds to array
            for (oid, val) in map(None, oids, vals):
                varbinds[oid] = str(val)

            community = req['community']
            version = str(req['version'] + 1)
            src = src[0]


            # Create trap object, let callback decide what to do with it.
            trap = SNMPTrap(str(src), agent, type, genericType, snmpTrapOID,
                            uptime, community, version, varbinds)
            callback(trap)

        # Exit nicely
        sys.exit(0)


def transform(req):
    """Transforms from SNMP-v1 to SNMP-v2 format. Returns snmpTrapOID and
    genericType as string.

    """
    enterprise = str(req['enterprise'])

    # According to RFC2576 "Coexistence between Version 1, Version 2,
    # and Version 3 of the Internet-standard Network Management
    # Framework", we build snmpTrapOID from the snmp-v1 trap by
    # combining enterprise + 0 + specific trap parameter IF the
    # generic trap parameter is 6. If not, the traps are defined as
    # 1.3.6.1.6.3.1.1.5 + generic trap parameter + 1
    for t in v1.GENERIC_TRAP_TYPES.keys():
        if req['generic_trap'] == v1.GENERIC_TRAP_TYPES[t]:
            genericType = t
            if req['generic_trap'] == 6:
                snmpTrapOID = enterprise + ".0." + str(req['specific_trap'])
            else:
                snmpTrapOID = ".1.3.6.1.6.3.1.1.5." + str(req['generic_trap'] + 1)
            break
    else:
        snmpTrapOID = enterprise + ".0." + str(req['specific_trap'])

    return snmpTrapOID, genericType

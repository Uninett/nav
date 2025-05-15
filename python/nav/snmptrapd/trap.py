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
"""Trap related data structures."""

import string
import logging
from collections import namedtuple

from nav.db import getConnection

_logger = logging.getLogger(__name__)


AgentNetbox = namedtuple('Agent', 'netboxid sysname roomid')


class SNMPTrap(object):
    """Represents an SNMP trap or notification, in a structure agnostic to
    SNMP v1 and v2c differences.

    :
    """

    def __init__(
        self,
        src,
        agent,
        type,
        genericType,
        snmpTrapOID,
        uptime,
        community,
        version,
        varbinds,
    ):
        self.src = src
        self.agent = agent
        self.type = type
        self.genericType = genericType
        self.snmpTrapOID = snmpTrapOID
        self.uptime = uptime
        self.community = community
        self.varbinds = varbinds
        self.version = version
        # Print string if printable else assume hex and write hex-string
        for key, val in self.varbinds.items():
            if not val.strip(string.printable) == '':
                val = ':'.join(["%02x" % ord(c) for c in val])
                self.varbinds[key] = val

    def _lookup_agent(self):
        """Attempts to look up the corresponding netbox of this trap"""
        conn = getConnection('snmptrapd')
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT netboxid, sysname, roomid "
            "FROM netbox "
            "LEFT JOIN interface USING (netboxid) "
            "LEFT JOIN gwportprefix USING (interfaceid) "
            "WHERE %s IN (ip, gwip) ",
            (self.agent,),
        )

        if cur.rowcount < 1:
            _logger.warning(
                "Unable to match trap agent %s to a NAV-monitored device", self.agent
            )
            return None

        return AgentNetbox(*cur.fetchone())

    @property
    def netbox(self):
        if not hasattr(self, '_netbox'):
            setattr(self, '_netbox', self._lookup_agent())
        return getattr(self, '_netbox')

    def __str__(self):
        text = "Got snmp version %s trap\n" % self.version
        text = (text + "Src: %s, Community: %s, Uptime: %s\n") % (
            self.src,
            self.community,
            self.uptime,
        )
        text = (text + "Type %s, snmpTrapOID: %s\n") % (
            self.genericType,
            self.snmpTrapOID,
        )

        for key in sorted(self.varbinds.keys()):
            val = self.varbinds[key]
            text = text + "%s -> %s\n" % (key, val)

        return text

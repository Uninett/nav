#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""ipdevpoll plugin to collect LLDP neighbors

TODO: Identify known neighbors and update NAV database.

"""
from pprint import pformat

from twisted.internet import defer

from nav.mibs.lldp_mib import LLDPMib
from nav.ipdevpoll import Plugin

class LLDP(Plugin):
    "Collects devices' table of remote LLDP devices"

    @defer.inlineCallbacks
    def handle(self):
        mib = LLDPMib(self.agent)
        remote = yield mib.get_remote_table()
        if remote:
            self._logger.debug("LLDP neighbors:\n %s", pformat(remote))

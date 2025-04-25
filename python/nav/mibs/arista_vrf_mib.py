#
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from twisted.internet.defer import inlineCallbacks, Deferred

from nav.mibs import mibretriever
from nav.oids import OID
from nav.smidumps import get_mib


class AristaVrfMib(mibretriever.MibRetriever):
    """MibRetriever implementation for ARISTA-VRF-MIB"""

    mib = get_mib('ARISTA-VRF-MIB')

    @inlineCallbacks
    def get_vrf_states(self, only: str = None) -> Deferred:
        """Returns a Deferred whose result is a dict mapping VRF names to their states.

        :param only: If set, only VRFs that match this state will be returned.
        """
        states = yield self.retrieve_columns(['aristaVrfState']).addCallback(
            self.translate_result
        )

        states = {
            _vrf_index_to_string(k): v['aristaVrfState']
            for k, v in states.items()
            if only is None or v['aristaVrfState'] == only
        }
        return states


def _vrf_index_to_string(index: OID) -> str:
    """Translates a aristaVrfTable index OID to a string"""
    return "".join(chr(i) for i in index[1:])

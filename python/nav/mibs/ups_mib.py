#
# Copyright 2008 - 2011 (C) UNINETT AS
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
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever

class UpsMib(mibretriever.MibRetriever):
    from nav.smidumps.ups_mib import MIB as mib

    def get_module_name(self):
        """return the MIB-name."""
        return self.mib.get('moduleName', None)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ .... """
        return {}

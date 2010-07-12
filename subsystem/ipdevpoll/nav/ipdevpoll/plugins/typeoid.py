# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
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
"""ipdevpoll type detection plugin.

Collects sysObjectId and compares with the registered type of the
netbox.

TODO: If netbox type has changed, NAVdb needs to be updated, an event
      must be dispatched, and the poll run restarted.

"""

from twisted.internet import threads

from nav.ipdevpoll import Plugin, storage, shadows
from nav.ipdevpoll.models import OID
from nav.mibs.snmpv2_mib import Snmpv2Mib
from nav.models import manage

class InvalidResponseError(Exception):
    pass

class TypeOid(Plugin):
    @classmethod
    def can_handle(self, netbox):
        return True

    def handle(self):
        """Collects sysObjectID and looks for type changes."""
        self.logger.debug("Collecting sysObjectId")
        snmpv2_mib = Snmpv2Mib(self.agent)
        df = snmpv2_mib.get_sysObjectID()
        df.addCallback(self._response_handler)
        return df

    def _response_handler(self, result):
        """Handles a sysObjectID response."""
        if not result:
            raise InvalidResponseError("No response on sysObjectID query.",
                                       result, self.agent)
        # Just pick the first result, there should never really be multiple
        self.sysobjectid = str( OID(result) )
        # ObjectIDs in the database are stored without the preceding dot.
        if self.sysobjectid[0] == '.':
            self.sysobjectid = self.sysobjectid[1:]


        self.logger.debug("sysObjectID is %s", self.sysobjectid)
        if self.netbox.type is None or \
                self.netbox.type.sysobjectid != self.sysobjectid:
            self.logger.warning("Netbox has changed type from %r",
                                self.netbox.type)

        df = self._get_type_from_db()
        df.addCallback(self._set_type)
        return df

    def _get_type_from_db(self):
        """Loads from db a type object matching the sysobjectid."""
        def single_result(result):
            if result:
                return result[0]

        # Look up existing type entry
        types = manage.NetboxType.objects.filter(sysobjectid=self.sysobjectid)
        df = threads.deferToThread(storage.shadowify_queryset_and_commit,
                                   types)
        df.addCallback(single_result)
        return df

    def _set_type(self, type_):
        """Sets the netbox type to type_."""
        if not type_:
            self.logger.warn("sysObjectID %r is unknown to NAV",
                             self.sysobjectid)
        else:
            netbox_container = self.containers.factory(None, shadows.Netbox)
            netbox_container.type = type_


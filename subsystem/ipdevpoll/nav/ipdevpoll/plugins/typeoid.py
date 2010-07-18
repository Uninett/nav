# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 UNINETT AS
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

"""

from twisted.internet import threads

from nav.ipdevpoll import Plugin, storage, shadows, signals
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
        self.snmpv2_mib = Snmpv2Mib(self.agent)
        df = self.snmpv2_mib.get_sysObjectID()
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

        df = self._get_type_from_db()
        df.addCallback(self._check_for_typechange)
        df.addCallback(self._set_type)
        return df

    def has_type_changed(self):
        """Returns True if the netbox' type has changed."""
        return (self.netbox.type is None and self.sysobjectid) or \
            self.netbox.type.sysobjectid != self.sysobjectid

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
        netbox_container = self.containers.factory(None, shadows.Netbox)
        netbox_container.type = type_

        if self.has_type_changed():
            signals.netbox_type_changed.send(
                sender=self, netbox_id=self.netbox.id, new_type=type_)

    def _check_for_typechange(self, type_):
        if self.has_type_changed():
            oldname = self.netbox.type and self.netbox.type.name or 'unknown'
            newname = type_ and type_.name or \
                'unknown (sysObjectID %s)' % self.sysobjectid
            self.logger.warning("Netbox has changed type from %s to %s",
                                oldname, newname)
            self.logger.debug("old=%r new=%r", self.netbox.type, type_)

            if not type_:
                return self.create_new_type()
        return type_

    def create_new_type(self):
        """Creates a new NetboxType from the collected sysObjectID."""
        vendor_id = 'unknown'
        vendor = self.containers.factory(vendor_id, shadows.Vendor)
        vendor.id = vendor_id

        type_ = self.containers.factory(self.sysobjectid, shadows.NetboxType)
        type_.vendor = vendor
        type_.name = self.sysobjectid
        type_.sysobjectid = self.sysobjectid

        def set_sysdescr(descr):
            self.logger.debug("Creating new type with descr=%r", descr)
            type_.description = descr
            return type_

        df = self.snmpv2_mib.get_sysDescr()
        df.addCallback(set_sysdescr)
        return df


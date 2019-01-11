# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2012 Uninett AS
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
"""ipdevpoll type detection plugin.

Collects sysObjectId and compares with the registered type of the
netbox.

"""
from twisted.internet import defer

from nav.ipdevpoll import Plugin, storage, shadows, signals, db
from nav.oids import OID, get_enterprise_id
from nav.mibs.snmpv2_mib import Snmpv2Mib
from nav.models import manage
from django.db import connection

from nav.enterprise import ids
CONSTANT_PREFIX = 'VENDOR_ID_'
_enterprise_map = {value: constant
                   for constant, value in vars(ids).items()
                   if constant.startswith(CONSTANT_PREFIX)}


class InvalidResponseError(Exception):
    pass


class TypeOid(Plugin):
    def handle(self):
        """Collects sysObjectID and looks for type changes."""
        self._logger.debug("Collecting sysObjectId")
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
        self.sysobjectid = str(OID(result))
        # ObjectIDs in the database are stored without the preceding dot.
        if self.sysobjectid[0] == '.':
            self.sysobjectid = self.sysobjectid[1:]

        self._logger.debug("sysObjectID is %s", self.sysobjectid)

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
        def _single_result(result):
            if result:
                return result[0]

        # Look up existing type entry
        types = manage.NetboxType.objects.filter(sysobjectid=self.sysobjectid)
        df = db.run_in_thread(storage.shadowify_queryset_and_commit,
                              types)
        df.addCallback(_single_result)
        return df

    def _set_type(self, new_type):
        """Sets the netbox type to type_."""
        netbox_container = self.containers.factory(None, shadows.Netbox)
        netbox_container.type = new_type
        self._send_signal_if_changed_from_known_to_new_type(new_type)

    def _send_signal_if_changed_from_known_to_new_type(self, new_type):
        if self.netbox.type and self.has_type_changed():
            signals.netbox_type_changed.send(
                sender=self, netbox_id=self.netbox.id, new_type=new_type)

    def _check_for_typechange(self, type_):
        if self.has_type_changed():
            oldname = self.netbox.type and self.netbox.type.name or 'unknown'
            newname = type_ and type_.name or \
                'unknown (sysObjectID %s)' % self.sysobjectid
            self._logger.warning("Netbox has changed type from %s to %s",
                                 oldname, newname)
            self._logger.debug("old=%r new=%r", self.netbox.type, type_)

            if not type_:
                return self.create_new_type()
        return type_

    @defer.inlineCallbacks
    def create_new_type(self):
        """Creates a new NetboxType from the collected sysObjectID."""
        vendor_id = yield db.run_in_thread(get_vendor_id, self.sysobjectid)
        vendor = self.containers.factory(vendor_id, shadows.Vendor)
        vendor.id = vendor_id

        type_ = self.containers.factory(self.sysobjectid, shadows.NetboxType)
        type_.vendor = vendor
        type_.name = self.sysobjectid
        type_.sysobjectid = self.sysobjectid

        def _set_sysdescr(descr):
            self._logger.debug("Creating new type with descr=%r", descr)
            type_.description = descr
            return type_

        yield self.snmpv2_mib.get_sysDescr().addCallback(_set_sysdescr)

#
# Helper functions
#


def get_vendor_id(sysobjectid):
    """Looks up the most likely vendorid based on a sysObjectID"""
    enterprise = get_enterprise_id(sysobjectid)
    cx = connection.cursor()
    cx.execute("SELECT vendorid FROM enterprise_number "
               "WHERE enterprise = %s LIMIT 1", (enterprise,))
    vendorid = cx.fetchone()
    return vendorid[0] if vendorid else make_new_vendor_id(sysobjectid)


def make_new_vendor_id(sysobjectid):
    """Makes up a new vendorid based on a sysObjectID"""
    enterprise = get_enterprise_id(sysobjectid)
    if enterprise in _enterprise_map:
        name = _enterprise_map[enterprise]
        name = name.replace(CONSTANT_PREFIX, '').replace('_', '').lower()[:15]
        return name
    else:
        return u'unknown'

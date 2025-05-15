#
# Copyright (C) 2008-2012, 2019 Uninett AS
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

from nav.ipdevpoll import Plugin, shadows, signals, db
from nav.oids import OID, get_enterprise_id
from nav.mibs.snmpv2_mib import Snmpv2Mib
from nav.models import manage

from nav.enterprise import ids

UNKNOWN_VENDOR_ID = UNKNOWN_TYPE_ID = "unknown"
CONSTANT_PREFIX = "VENDOR_ID_"
_enterprise_map = {
    value: constant
    for constant, value in vars(ids).items()
    if constant.startswith(CONSTANT_PREFIX)
}


class InvalidResponseError(Exception):
    pass


class TypeOid(Plugin):
    """SNMP Agent type detector plugin"""

    def __init__(self, *args, **kwargs):
        super(TypeOid, self).__init__(*args, **kwargs)
        self.snmpv2_mib = Snmpv2Mib(self.agent)
        self.sysobjectid = None

    @defer.inlineCallbacks
    def handle(self):
        """Collects sysObjectID and looks for type changes."""
        self._logger.debug("Collecting sysObjectId")

        oid = yield self._fetch_sysobjectid()
        if self._is_sysobjectid_changed(oid):
            yield self._switch_type(oid)

    @defer.inlineCallbacks
    def _fetch_sysobjectid(self):
        result = yield self.snmpv2_mib.get_sysObjectID()
        if not result:
            raise InvalidResponseError(
                "No response on sysObjectID query.", result, self.agent
            )
        oid = OID(result)
        self._logger.debug("sysObjectID is %s", oid)
        return oid

    def _is_sysobjectid_changed(self, oid):
        current_oid = OID(self.netbox.type.sysobjectid) if self.netbox.type else None
        return current_oid != OID(oid)

    @defer.inlineCallbacks
    def _switch_type(self, oid):
        new_type = yield self._get_type_from_oid(oid)
        if not new_type:
            new_type = yield self._create_new_type(oid)
        self._set_type(shadows.NetboxType(new_type))

    @staticmethod
    @db.synchronous_db_access
    def _get_type_from_oid(oid):
        """Loads from db a type object matching the sysobjectid."""
        term = str(oid).strip(".")
        try:
            return manage.NetboxType.objects.get(sysobjectid=term)
        except manage.NetboxType.DoesNotExist:
            return None

    def _set_type(self, new_type):
        """Sets the netbox type to type_."""
        netbox_container = self.containers.factory(None, shadows.Netbox)
        netbox_container.type = new_type

        self._send_signal_if_changed_from_known_to_new_type(new_type)
        self._logger.info(
            "%s has changed type from %s to %s",
            self.netbox.sysname,
            type_to_string(self.netbox.type),
            type_to_string(new_type),
        )

        self.netbox.type = new_type

    def _send_signal_if_changed_from_known_to_new_type(self, new_type):
        if self.netbox.type is not None:
            signals.netbox_type_changed.send(
                sender=self, netbox_id=self.netbox.id, new_type=new_type
            )

    @defer.inlineCallbacks
    def _create_new_type(self, oid):
        """Creates a new NetboxType from the given sysobjectid."""
        self._logger.debug("Creating a new type from %r", oid)
        description = yield self.snmpv2_mib.get_sysDescr()

        def _create():
            vendor = self._get_vendor(oid)
            type_ = manage.NetboxType(
                vendor=vendor,
                name=str(oid),
                sysobjectid=str(oid).strip("."),
                description=description,
            )
            type_.save()
            return type_

        new_type = yield db.run_in_thread(_create)
        return new_type

    @classmethod
    def _get_vendor(cls, sysobjectid):
        """Looks up the most likely vendor based on a sysObjectID"""
        enterprise_id = get_enterprise_id(sysobjectid)
        query = (
            "vendorid IN (SELECT vendorid FROM enterprise_number WHERE enterprise=%s)"
        )
        try:
            return manage.Vendor.objects.extra(where=[query], params=[enterprise_id])[0]
        except IndexError:
            return cls._make_new_vendor(sysobjectid)

    @classmethod
    def _make_new_vendor(cls, sysobjectid):
        """Makes up a new Vendor based on a sysObjectID"""
        enterprise_id = get_enterprise_id(sysobjectid)
        if enterprise_id in _enterprise_map:
            name = _enterprise_map[enterprise_id]
            name = name.replace(CONSTANT_PREFIX, "").replace("_", "").lower()[:15]
        else:
            name = UNKNOWN_VENDOR_ID

        cls._logger.debug("Making new vendor %r from %r", name, sysobjectid)
        vendor, _created = manage.Vendor.objects.get_or_create(id=name)
        return vendor


def type_to_string(type_):
    """Returns a string representation of a NetboxType for logging use. Should work
    with both ORM models and Shadow instances, as well as None values.
    """
    if not type_:
        return UNKNOWN_TYPE_ID
    else:
        return "{} ({})".format(type_.name, type_.vendor.id)

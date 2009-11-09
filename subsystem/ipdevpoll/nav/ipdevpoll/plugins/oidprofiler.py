# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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
"""SNMP OID profiler plugin for ipdevpoll.

Basically performs the same task as the OID tester did in
getDeviceData.  It creates an SNMP profile in the database for each
netbox.  

Although the SNMP profiles are no longer used by NAV internal tools,
it is required to produce a useful Cricket configuration.  Without a
pre-collected SNMP profile, Cricket would attempt to collect
non-supported objects from many hosts and end up spewing errors to the
administrators email inbox.

"""
from twisted.internet import defer, threads, reactor
from pysnmp.asn1.oid import OID

import socket

from nav.models.oid import SnmpOid, NetboxSnmpOid
from nav.ipdevpoll import storage, shadows
from nav.ipdevpoll import Plugin, FatalPluginError

class OidProfiler(Plugin):
    """Make SNMP profile for a device."""
    def __init__(self, *args, **kwargs):
        super(OidProfiler, self).__init__(*args, **kwargs)
        self.agent = self.job_handler.agent

    @classmethod
    def can_handle(cls, netbox):
        """We handle everything that supports SNMP"""
        return True

    def handle(self):
        if self.netbox.up_to_date:
            # Nothing to do here.
            self.logger.debug("profile is already up-to-date")
            df = defer.Deferred()
            reactor.callLater(0, df.callback, True)
            return df

        return get_all_snmpoids().addCallback(self._query_oids)

    @defer.deferredGenerator
    def _query_oids(self, all_oids):
        """Query the netbox for all oids in all_oids"""
        supported_oids = []
        for snmpoid in all_oids:
            waiter = defer.waitForDeferred(
                self._verify_support(snmpoid))
            yield waiter
            support = waiter.getResult()

            if support:
                self.logger.debug("%s is supported", snmpoid.oid_key)
                supported_oids.append(snmpoid)
            else:
                self.logger.debug("%s is NOT supported", snmpoid.oid_key)

        deferred = self._get_current_profile()
        deferred.addCallback(self._update_profile, supported_oids)
        waiter = defer.waitForDeferred(deferred)
        yield waiter
        waiter.getResult()

    def _get_current_profile(self):
        """Get the current snmp profile of the box."""
        current_profile_queryset = \
            NetboxSnmpOid.objects.filter(netbox=self.netbox.id)
        return threads.deferToThread(
            storage.shadowify_queryset, current_profile_queryset
            )

    def _update_profile(self, current_profile, supported_oids):
        """Update the netbox' SNMP profile.

        Looks at the current profile and a list of newly tested and
        supported OIDs, and creates containers to add new ones and
        delete removed ones.

        Arguments:

          current_profile -- A list of shadow.NetboxSnmpOid objects.
          supported_oids -- A list of shadow.SnmpOid objects.

        """
        # Set up a few sets and dictionaries to find what to add and
        # what to delete
        supported_oid_ids = set(o.id for o in supported_oids)
        oid_id_profile_id_map = dict((p.snmp_oid.id, p.id) 
                                     for p in current_profile)
        profile_oid_ids = set(oid_id_profile_id_map)
        
        ids_to_add = supported_oid_ids.difference(profile_oid_ids)
        ids_to_remove = profile_oid_ids.difference(supported_oid_ids)

        if ids_to_add or ids_to_remove:
            self.logger.info("profile update: add %d / del %d",
                             len(ids_to_add), len(ids_to_remove))

        netbox = self.job_handler.container_factory(shadows.Netbox, key=None)

        for snmpoid_id in ids_to_add:
            profile_entry = self.job_handler.container_factory(
                shadows.NetboxSnmpOid, key=snmpoid_id)
            profile_entry.snmp_oid_id = snmpoid_id
            profile_entry.netbox = netbox
            # Hard code frequency, which no longer has any meaning,
            # but is required by the data model
            profile_entry.frequency = 3600

        for snmpoid_id in ids_to_remove:
            profile_entry = self.job_handler.container_factory(
                shadows.NetboxSnmpOid, key=snmpoid_id)
            profile_entry.id = oid_id_profile_id_map[snmpoid_id]
            profile_entry.delete = True

        netbox.up_to_date = True

    def _verify_support(self, snmpoid):
        """Verify whether the device answers this OID.

        Will first try a GET request.  If that fails, a GET-NEXT
        request is attempted.

        """
        oid = OID(snmpoid.snmp_oid)

        def getnext_result_checker(result):
            if len(result) > 0:
                response_oid = result.keys()[0]
                if oid.isaprefix(response_oid):
                    self.logger.debug("%s support found using GET-NEXT: %r",
                                      snmpoid.oid_key, result)
                    return True
            return False

        def get_result_checker(result):
            if oid in result:
                self.logger.debug("%s support found using GET: %r",
                                  snmpoid.oid_key, result)
                return True
            else:
                df = get_next(self.agent, oid)
                df.addCallback(getnext_result_checker)
                return df

        df = self.agent.get([oid])
        df.addCallback(get_result_checker)
        return df
        
# Impressively enough, twistedsnmp's AgentProxy class does not provide
# a simple getNext method - unless you want to pull an entire table.
def get_next(agent, oid, timeout=2.0, retry_count=4):
    """Our own low-level implementation of a GET-NEXT operation for a
    twistedsnmp AgentProxy, since the latter doesn't provide its own.

    """
    oids = [OID(oid)]
    try:
        request = agent.encode(oids, agent.community, next=True)
        key = agent.getRequestKey(request)
        agent.send(request.encode())
    except socket.error, err:
        return defer.fail(failure.Failure())

    def as_dictionary(value):
        try:
            return dict(value)
        except Exception, err:
            logger = logging.getLogger(__name__)
            logger.exception(
                "Failure converting query results %r to dictionary", value)
            return {}

    df = defer.Deferred()
    df.addCallback(agent.getResponseResults)
    df.addCallback(as_dictionary)
    timer = reactor.callLater(timeout, agent._timeout, 
                              key, df, oids, timeout, retry_count)
    agent.protocol.requests[key] = df, timer
    return df


def get_all_snmpoids():
    """Get all SnmpOid objects from the database.

    Returns:

      A deferred whose result is a list of shadow.SnmpOid objects.

    """
    all_oids_queryset = SnmpOid.objects.all()
    return threads.deferToThread(
        storage.shadowify_queryset, all_oids_queryset
        )

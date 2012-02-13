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
"ipdevpoll plugin to collect CDP (Cisco Discovery Protocol) information"
import re

from twisted.internet import defer
from twisted.internet.threads import deferToThread

from nav.models import manage
from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll.log import ContextLogger
from nav.mibs.cisco_cdp_mib import CiscoCDPMib

from django.db.models import Q

class CDP(Plugin):
    """Finds neighboring devices from a device's CDP cache.

    If the neighbor can be identified as something monitored by NAV, a
    topology adjacency candidate will be registered. Otherwise, the
    neighboring device will be noted as an unrecognized neighbor to this
    device.

    TODO: Actually fill some containers to store to db
    """
    cache = None
    neighbors = None

    @defer.inlineCallbacks
    def handle(self):
        cdp = CiscoCDPMib(self.agent)
        cache = yield cdp.get_cdp_neighbors()
        if cache:
            self._logger.debug("found CDP cache data: %r", cache)
            self.cache = cache
            yield deferToThread(self._process_cache)

    def _process_cache(self):
        "Tries to synchronously identify CDP cache entries in NAV's database"
        neighbors = [Neighbor(cdp) for cdp in self.cache]
        identified = [n for n in neighbors if n.netbox]
        for neigh in identified:
            self._logger.debug("identified neighbor %r from %r",
                               (neigh.netbox, neigh.interface), neigh.cdp)
        self.neighbors = neighbors

# pylint: disable=R0903
class Neighbor(object):
    "A device neighbor"
    _logger = ContextLogger()

    def __init__(self, cdpneighbor):
        self.cdp = cdpneighbor
        self.netbox = self._identify_netbox()
        self.interface = self._identify_interface()
        self.identified = bool(self.netbox or self.interface)

    def _identify_netbox(self):
        if self.cdp.ip:
            netbox = self._netbox_from_ip()

        if not netbox and self.cdp.deviceid:
            netbox = self._netbox_from_deviceid()

        return netbox

    def _netbox_from_ip(self):
        """Tries to find a Netbox from NAV's database based on an IP address.

        :returns: A shadows.Netbox object representing the netbox, or None if no
                  corresponding netbox was found.

        """
        ip = unicode(self.cdp.ip)
        assert ip
        return (self._netbox_query(Q(ip=ip)) or
                self._netbox_query(Q(interface__gwportprefix__gw_ip=ip)))

    ID_PATTERN = re.compile(r'(.*\()?(?P<sysname>[^\)]+)\)?')
    def _netbox_from_deviceid(self):
        """Tries to find a Netbox from NAV's database based on a CDP device id
        value.

        The deviceid is interpreted in various ways that have been seen in the
        wild.  Valid examples are the remote device's sysname, with or without a
        qualified domain name, or a string following the "SERIAL(sysname)"
        pattern.

        :returns: A shadows.Netbox object representing the netbox, or None if no
                  corresponding netbox was found.

        """
        match = self.ID_PATTERN.search(self.cdp.deviceid)
        sysname = match.group('sysname').lower()
        assert sysname
        try:
            sysname.decode('ascii')
        except UnicodeDecodeError:
            return None
        query = Q(sysname=sysname)

        is_fqdn = '.' in sysname
        if not is_fqdn:
            query = query | Q(sysname__startswith=sysname + '.')

        return self._netbox_query(query)

    @staticmethod
    def _netbox_query(query):
        """Runs a Django get()-query on the Netbox model, based on query.

        :param query: A Q object usable in a Netbox query.
        :returns: A shadows.Netbox object if a db object was found, otherwise
                  None.

        """
        assert query
        try:
            netbox = manage.Netbox.objects.values('id', 'sysname').get(query)
        except manage.Netbox.DoesNotExist:
            return None
        return shadows.Netbox(**netbox)

    def _identify_interface(self):
        """Tries to find an Interface in NAV's database based on a netbox and
        a CPD remote portid.

        The remote portid is usually either an ifDescr or ifName value.

        :returns: A shadows.Interface object representing the interface, or None
                  if no corresponding interface was found.

        """
        if not (self.netbox and self.cdp.deviceport):
            return

        values = manage.Interface.objects.values('id', 'ifname', 'ifdescr')
        try:
            ifc = values.get(netbox__id=self.netbox.id,
                             ifdescr=self.cdp.deviceport)
        except manage.Interface.DoesNotExist:
            try:
                ifc = values.get(netbox__id=self.netbox.id,
                                 ifname=self.cdp.deviceport)
            except manage.Interface.DoesNotExist:
                return None

        return shadows.Interface(**ifc)

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
"""ipdevpoll plugin to pull vlan information.

Just a prototype, will only log info, not store it in NAVdb.

"""

import logging
import pprint
import re

from twisted.internet import defer
from twisted.python.failure import Failure

from nav.mibs import IfMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage

LAN_REGEXP = re.compile('([\w-]+),([\w-]+),?([\w-]+)?,?(\d+)?')
CORE_REGEXP = re.compile('([\w-]+),([\w-]+),?([\w-]+)?,?(\d+)?')
ELINK_REGEXP = re.compile('([\w-]+),([\w-]+),?([\w-]+)?,?(\d+)?')
LINK_REGEXP = re.compile('([\w-]+),?([\w-]+)?,?(\d+)?')

class Vlans(Plugin):
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self.logger.debug("Collecting interface data")
        self.qbridgemib = QBridgeMib(self.job_handler.agent)
        df = self.qbridgemib.retrieve_columns([
                'dot1qPvid',
                'dot1dBasePortIfIndex',
                ])
        df.addCallback(self.got_vlans)
        df.addErrback(self.error)
        return self.deferred

    def error(self, failure):
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        self.deferred.errback(failure)

    def got_vlans(self, result):
        self.logger.debug("Found %d vlans", len(result))

        # Now save stuff to containers and signal our exit
        for (ifIndex,),row in result.items():
            interface = self.job_handler.container_factory(storage.Interface,
                                                           key=ifIndex)

            data = self.parse_ifDescr(interface.ifDescr)
            if not data:
                logger.warning("Interface description %s does not follow NAV guidelines. Unable to parse" % interface.ifDescr)

        self.deferred.callback(True)
        return result

    @staticmethod
    def parse_ifDescr(ifDescr):
        """
        Parses an ifDescr as described in
        http://metanav.uninett.no/subnetsandvlans#guide_lines_for_configuring_router_interface_descriptions
        Returns a dictionary with the values
        """
        type = ifDescr[:ifDescr.find(',')]
        if type not in ('lan','core','link','elink'):
            return None

        if type == 'lan':
            data = LAN_REGEXP.findall(ifDescr[4:])
            if not data:
                return None
            return dict(zip(('organisation','usage','comment','vlan'), data[0]))
        elif type == 'core':
            data = CORE_REGEXP.findall(ifDescr[5:])
            if not data:
                return None
            return dict(zip(('organisation','usage','comment','vlan'), data[0]))
        elif type == 'link':
            data = LINK_REGEXP.findall(ifDescr[5:])
            if not data:
                return None
            return dict(zip(('to_router','comment','vlan'), data[0]))
        elif type == 'elink':
            data = ELINK_REGEXP.findall(ifDescr[6:])
            if not data:
                return None
            return dict(zip(('to_router','to_organisation', 'comment','vlan'), data[0]))

        return None


"""ipdevpoll plugin to pull iftable date.

Just a prototype, will only log info, not store it in NAVdb.

"""
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import logging
import pprint

from pysnmp.asn1.oid import OID

from twisted.internet import defer
from twisted.python.failure import Failure

from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll.plugins import register

class Interfaces(Plugin):
    def __init__(self, netbox):
        Plugin.__init__(self, netbox)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        return netbox.is_supported_oid("ifDescr")

    def handle(self):
        self.logger.debug("Collecting ifDescr")
        df = self.netbox.get_table("ifDescr")
        df.addCallback(self.got_results)
        df.addErrback(self.error)
        return self.deferred

    def error(self, failure):
        failure.trap(defer.TimeoutError)
        # Handle TimeoutErrors
        self.logger.error(failure.getErrorMessage())
        # Report this failure to the waiting plugin manager (RunHandler)
        exc = FatalPluginError("Cannot continue due to device timeouts")
        failure = Failure(exc)
        self.deferred.errback(failure)

    def got_results(self, result):
        ifdescrs = result.values()[0]
        self.logger.debug("Found %d interfaces", len(ifdescrs))
        #self.logger.debug('Results: %s', pprint.pformat(result))
        self.deferred.callback(True)
        return result

register(Interfaces)

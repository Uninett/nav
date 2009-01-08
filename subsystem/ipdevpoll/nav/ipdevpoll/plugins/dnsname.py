"""
ipdevpoll plugin to perform reverse DNS lookups on netbox IP addresses.

Will generate events if there are mismatches between device sysname
and dnsname.
"""
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

from IPy import IP

from twisted.internet import defer
#from twisted.python.failure import Failure
from twisted.names import client, dns

from nav.util import round_robin
from nav.ipdevpoll import Plugin
from nav.ipdevpoll.plugins import register

resolvers = round_robin([client.Resolver('/etc/resolve.conf') for i in range(3)])

class DnsName(Plugin):

    """Performs reverse DNS lookup on netbox IP address"""

    def __init__(self, netbox):
        Plugin.__init__(self, netbox)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        """Return true for all netboxes, as this plugin doesn't require SNMP
        support.
        """
        return True

    def handle(self):
        ip = IP(self.netbox.ip)
        self.logger.debug("Doing DNS PTR lookup for %s", ip.reverseName())
        # Use the OS configured DNS resolver method
        resolver = resolvers.next()
        df = resolver.lookupPointer( ip.reverseName() )
        df.addCallback(self.got_result)
        df.addErrback(self.got_failure)
        return self.deferred

    def got_failure(self, failure):
        """Failure callback"""
        failure.trap(defer.TimeoutError)
        # Handle TimeoutErrors
        self.logger.warning("DNS lookup timed out")
        # DNS timeout is not fatal to the poll run, so we signal
        # plugin success to the runhandler
        self.deferred.callback(True)

    def got_result(self, result):
        """Result callback"""
        self.logger.debug("DNS response: %s", result)
        # Disclaimer: I'm no DNS expert, so my terminology may be way
        # off.  
        #
        # We can get several series of responses, each with up to
        # several response records.  One series may contain the PTR
        # record we are looking for, while others may contain DNS
        # authority records or whatever else extra stuff the DNS
        # server wants to tell us.
        #
        # We're satisfied with the first PTR record we can find in the
        # response.
        dns_name = None
        for record_list in result:
            for record in record_list:
                if record.type == dns.PTR:
                    dns_name = str(record.payload.name)
                    self.logger.debug("PTR record payload: %s", record.payload)
                    break
            if dns_name:
                break
        if not dns_name:
            self.logger.warning("Unable to find PTR record for %s (%s)",
                                self.netbox.ip, 
                                IP(self.netbox.ip).reverseName())
        elif dns_name.strip().lower() != self.netbox.sysname.strip().lower():
            self.logger.warning("Box dnsname has changed from %s to %s",
                                repr(self.netbox.sysname), repr(dns_name))
        # Our work here is done
        self.logger.info("Reverse DNS lookup result: %s -> %s", self.netbox.ip, dns_name)
        self.deferred.callback(True)
        return dns_name

register(DnsName)

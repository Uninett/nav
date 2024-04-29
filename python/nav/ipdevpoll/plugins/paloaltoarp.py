#
# Copyright (C) 2023 University of Tromsø
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""ipdevpoll plugin for fetching arp mappings from Palo Alto firewalls

Add [paloaltoarp] section to ipdevpoll.conf
add hostname = key to [paloaltoarp] section
for example:
[paloaltoarp]
10.0.0.0 = abcdefghijklmnopqrstuvwxyz1234567890

"""

import xml.etree.ElementTree as ET

from IPy import IP
from twisted.internet import defer, reactor, ssl
from twisted.internet.defer import returnValue
from twisted.web import client
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from nav import buildconf
from nav.ipdevpoll.plugins.arp import Arp


class PaloaltoArp(Arp):
    def __init__(self, *args, **kwargs):
        self._logger.debug("PaloaltoArp initialized")

        self.paloalto_devices = []

        if 'paloaltoarp' in self.config:
            self._logger.debug("PaloaltoArp config section found")
            for key in self.config['paloaltoarp']:
                self.paloalto_devices.append(
                    {'key': self.config['paloaltoarp'][key], 'hostname': key}
                )
        else:
            self._logger.debug("PaloaltoArp config section NOT found")

        super().__init__(*args, **kwargs)

    @classmethod
    def can_handle(cls, netbox):
        """Return True if this plugin can handle the given netbox."""
        PaloaltoArp_Instance = cls(None, None, None)

        for device in PaloaltoArp_Instance.paloalto_devices:
            if device['hostname'] == netbox.sysname or device['hostname'] == netbox.ip:
                return True

    @defer.inlineCallbacks
    def handle(self):
        """Handle plugin business, return a deferred."""

        for device in self.paloalto_devices:
            if (
                self.netbox.ip == device['hostname']
                or self.netbox.sysname == device['hostname']
            ):
                self._logger.debug(
                    "Collecting IP/MAC mappings for Paloalto device: %s",
                    device['hostname'],
                )

                mappings = yield self._get_paloalto_arp_mappings(
                    self.netbox.ip, device['key']
                )
                if mappings is None:
                    self._logger.info(
                        "No mappings found for Paloalto device: %s", device['hostname']
                    )
                    returnValue(None)

                yield self._process_data(mappings)

        returnValue(None)

    @defer.inlineCallbacks
    def _get_paloalto_arp_mappings(self, ip, key):
        """Get mappings from Paloalto device"""

        arptable = yield self._do_request(ip, key)
        if arptable is None:
            returnValue(None)

        # process arpdata into an array of mappings
        mappings = parse_arp(arptable.decode('utf-8'))
        returnValue(mappings)

    @defer.inlineCallbacks
    def _do_request(self, ip, key):
        """Make request to Paloalto device"""

        class sslPolicy(client.BrowserLikePolicyForHTTPS):
            def creatorForNetloc(self, hostname, port):
                return ssl.CertificateOptions(verify=False)

        url = f'https://{ip}/api/?type=op&cmd=<show><arp><entry+name+=+\'all\'/></arp></show>&key={key}'
        self._logger.debug("making request: %s", url)

        agent = Agent(reactor, contextFactory=sslPolicy())

        try:
            response = yield agent.request(
                b'GET',
                url.encode('utf-8'),
                Headers(
                    {'User-Agent': [f'NAV/PaloaltoArp; version {buildconf.VERSION}']}
                ),
                None,
            )
        except:
            self._logger.info(
                "make sure the device is reachable and the key is correct"
            )
            returnValue(None)

        response = yield client.readBody(response)
        returnValue(response)


def parse_arp(arp):
    """
    Create mappings from arp table
    xml.etree.ElementTree is considered insecure: https://docs.python.org/3/library/xml.html#xml-vulnerabilities
    However, since we are not parsing untrusted data, this should not be a problem.
    """

    arps = []

    root = ET.fromstring(arp)
    entries = root[0][4]
    for entry in entries:
        status = entry[0].text
        ip = entry[1].text
        mac = entry[2].text
        if status.strip() != "i":
            if mac != "(incomplete)":
                arps.append(('ifindex', IP(ip), mac))

    return arps

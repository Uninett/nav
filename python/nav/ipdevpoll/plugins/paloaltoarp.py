#
# Copyright (C) 2023, 2024 University of Tromsø
# Copyright (C) 2024 Sikt
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
from nav.models.manage import Netbox
from twisted.internet import defer, reactor, ssl
from twisted.internet.defer import returnValue
from twisted.web import client
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from nav import buildconf
from nav.ipdevpoll.plugins.arp import Arp


class PaloaltoArp(Arp):
    @classmethod
    def can_handle(cls, netbox):
        """Return True if this plugin can handle the given netbox."""
        return netbox.get_http_rest_management_profiles("Palo Alto ARP").exists()

    @defer.inlineCallbacks
    def handle(self):
        """Handle plugin business, return a deferred."""
        self._logger.debug("Collecting IP/MAC mappings for Paloalto device")

        api_keys = self._get_paloalto_api_keys(self.netbox)
        mappings = self._get_paloalto_arp_mappings(self.netbox.ip, api_keys)
        if mappings is not None:
            yield self._process_data(mappings)

    @defer.inlineCallbacks
    def _get_paloalto_arp_mappings(self, ip: IP, api_keys: list[str]):
        """
        Get ARP mappings from Paloalto device

        The Paloalto device is expected to give the same result for two correct but different keys in api_keys.
        Hence, a request to the Paloalto device is made for each api key only until a successful response from the device.
        """

        mappings = None
        for i, api_key in enumerate(api_keys):
            arptable = yield self._do_request(ip, api_key)
            if arptable is not None:
                # process arpdata into an array of mappings
                mappings = parse_arp(arptable.decode('utf-8'))
                break
            self._logger.info(
                "Could not fetch ARP table from Paloalto device When using API key %d of %d",
                i,
                len(api_keys),
            )

        returnValue(mappings)

    def _get_paloalto_api_keys(self, netbox: Netbox) -> list[str]:
        api_profiles = netbox.get_http_rest_management_profiles(service="Palo Alto ARP")
        api_keys = [profile.configuration["api_key"] for profile in api_profiles]
        return api_keys

    @defer.inlineCallbacks
    def _do_request(self, address: IP, key: str):
        """Make request to Paloalto device"""

        class SslPolicy(client.BrowserLikePolicyForHTTPS):
            def creatorForNetloc(self, hostname, port):
                return ssl.CertificateOptions(verify=False)

        url = f"https://{address}/api/?type=op&cmd=<show><arp><entry+name+=+'all'/></arp></show>&key={key}"
        self._logger.debug("making request: %s", url)

        agent = Agent(reactor, contextFactory=SslPolicy())

        try:
            response = yield agent.request(
                b'GET',
                url.encode('utf-8'),
                Headers(
                    {'User-Agent': [f'NAV/PaloaltoArp; version {buildconf.VERSION}']}
                ),
                None,
            )
        except Exception:  # noqa
            self._logger.exception(
                "Error when talking to PaloAlto API. "
                "Make sure the device is reachable and the API key is correct."
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
    entries = root.find("result").find("entries")
    for entry in entries:
        status = entry.find("status").text
        ip = entry.find("ip").text
        mac = entry.find("mac").text
        if status.strip() != "i":
            if mac != "(incomplete)":
                arps.append(('ifindex', IP(ip), mac))

    return arps

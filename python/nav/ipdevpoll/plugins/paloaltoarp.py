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
from typing import Dict

from IPy import IP
from twisted.internet import defer, reactor, ssl
from twisted.internet.defer import returnValue
from twisted.web import client
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from nav import buildconf
from nav.ipdevpoll.plugins.arp import Arp


class PaloaltoArp(Arp):
    configured_devices: Dict[str, str] = {}

    @classmethod
    def on_plugin_load(cls):
        """Loads the list of PaloAlto access keys from ipdevpoll.conf into the plugin
        class instance, so that `can_handle` will be able to answer which devices
        this plugin can run for.
        """
        from nav.ipdevpoll.config import ipdevpoll_conf

        cls._logger.debug("loading paloaltoarp configuration")
        if 'paloaltoarp' not in ipdevpoll_conf:
            cls._logger.debug("PaloaltoArp config section NOT found")
            return
        cls._logger.debug("PaloaltoArp config section found")
        cls.configured_devices = dict(ipdevpoll_conf['paloaltoarp'])

    @classmethod
    def can_handle(cls, netbox):
        """Return True if this plugin can handle the given netbox."""
        return (
            netbox.sysname in cls.configured_devices
            or str(netbox.ip) in cls.configured_devices
        )

    @defer.inlineCallbacks
    def handle(self):
        """Handle plugin business, return a deferred."""

        api_key = self.configured_devices.get(
            str(self.netbox.ip), self.configured_devices.get(self.netbox.sysname, "")
        )
        self._logger.debug("Collecting IP/MAC mappings for Paloalto device")

        mappings = yield self._get_paloalto_arp_mappings(self.netbox.ip, api_key)
        if mappings is None:
            self._logger.info("No mappings found for Paloalto device")
            returnValue(None)

        yield self._process_data(mappings)

        returnValue(None)

    @defer.inlineCallbacks
    def _get_paloalto_arp_mappings(self, address: str, key: str):
        """Get mappings from Paloalto device"""

        arptable = yield self._do_request(address, key)
        if arptable is None:
            returnValue(None)

        # process arpdata into an array of mappings
        mappings = parse_arp(arptable.decode('utf-8'))
        returnValue(mappings)

    @defer.inlineCallbacks
    def _do_request(self, address: str, key: str):
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
    entries = root[0][4]
    for entry in entries:
        status = entry[0].text
        ip = entry[1].text
        mac = entry[2].text
        if status.strip() != "i":
            if mac != "(incomplete)":
                arps.append(('ifindex', IP(ip), mac))

    return arps

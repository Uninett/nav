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

"""
ipdevpoll plugin for fetching arp mappings from Palo Alto firewalls

Configure a netbox to work with this plugin by assigning it a
HTTP_API management profile with service set to "Palo Alto ARP"
in seedDB.
"""

import xml.etree.ElementTree as ET

from IPy import IP
from twisted.internet import defer, reactor, ssl
from twisted.web import client
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from nav import buildconf
from nav.ipdevpoll import db
from nav.ipdevpoll.plugins.arp import Arp
from nav.models.manage import Netbox, ManagementProfile, NetboxProfile


class PaloaltoArp(Arp):
    @classmethod
    @defer.inlineCallbacks
    def can_handle(cls, netbox):
        """Return True if this plugin can handle the given netbox."""
        has_configurations = yield cls._has_paloalto_configurations(netbox)
        return has_configurations

    @defer.inlineCallbacks
    def handle(self):
        """Handle plugin business, return a deferred."""
        self._check_and_update_prefix_cache()
        self._logger.debug("Collecting IP/MAC mappings for Paloalto device")

        configurations = yield self._get_paloalto_configurations(self.netbox)
        for configuration in configurations:
            mappings = yield self._get_paloalto_arp_mappings(
                self.netbox.ip, configuration["api_key"]
            )
            if mappings:
                yield self._process_data(mappings)
                break

    @staticmethod
    @db.synchronous_db_access
    def _has_paloalto_configurations(netbox: Netbox):
        """
        Make a database request to check if the netbox has any management
        profile that configures access to Palo Alto ARP data via HTTP
        """
        queryset = _paloalto_profile_queryset(netbox)
        return queryset.exists()

    @staticmethod
    @db.synchronous_db_access
    def _get_paloalto_configurations(netbox: Netbox):
        """
        Make a database request that fetches all management profiles of
        the netbox that configures access to Palo Alto ARP data via HTTP
        """
        queryset = _paloalto_profile_queryset(netbox)
        return list(queryset)

    @defer.inlineCallbacks
    def _get_paloalto_arp_mappings(self, address: IP, key: str):
        """
        Make a HTTP request for ARP data from Paloalto device with the given
        ip-address, using the given api-key. Returns a formatted list of ARP
        mappings for use in NAV.
        """
        arptable = yield self._do_request(address, key)
        mappings = _parse_arp(arptable) if arptable else []
        return mappings

    @defer.inlineCallbacks
    def _do_request(self, address: IP, key: str):
        """Make an HTTP request to a Palo Alto device"""

        class SslPolicy(client.BrowserLikePolicyForHTTPS):
            def creatorForNetloc(self, hostname, port):
                return ssl.CertificateOptions(verify=False)

        url = f"https://{address}/api/?type=op&cmd=<show><arp><entry+name+=+'all'/></arp></show>&key={key}"
        self._logger.debug(
            "Making HTTP request to Paloalto API endpoint at %s", address
        )

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
        except Exception:  # noqa: BLE001
            self._logger.exception(
                "Error when making HTTP request to Paloalto API endpoint. "
                "Make sure the device is reachable and the API key is correct."
            )
            return None

        response = yield client.readBody(response)
        return response


def _parse_arp(arpbytes: bytes) -> list[tuple[str, IP, str]]:
    """
    Create mappings from arp table
    xml.etree.ElementTree is considered insecure: https://docs.python.org/3/library/xml.html#xml-vulnerabilities
    However, since we are not parsing untrusted data, this should not be a problem.
    """
    arps = []

    root = ET.fromstring(arpbytes.decode("utf-8"))
    entries = root.find("result").find("entries")
    for entry in entries:
        status = entry.find("status").text
        ip = entry.find("ip").text
        mac = entry.find("mac").text
        if status.strip() != "i":
            if mac != "(incomplete)":
                arps.append(('ifindex', IP(ip), mac))

    return arps


def _paloalto_profile_queryset(netbox: Netbox):
    """
    Creates a Django queryset which when iterated yields JSON dictionaries
    representing configurations for accessing Palo Alto ARP data of the given
    netbox via HTTP. The keys in these dictionaries are the attribute-names of
    the :py:class:`~nav.web.seeddb.page.management_profile.forms.HttpRestForm`
    Django form.
    """
    return NetboxProfile.objects.filter(
        netbox_id=netbox.id,
        profile__protocol=ManagementProfile.PROTOCOL_HTTP_API,
        profile__configuration__contains={"service": "Palo Alto ARP"},
    ).values_list("profile__configuration", flat=True)

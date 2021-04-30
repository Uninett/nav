#
# Copyright (C) 2007-2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Sorts and does calculations on IP addresses/nets."""

import logging

from IPy import IP

_logger = logging.getLogger(__name__)


class UnknownIpVersionError(Exception):
    pass


def sort_nets_by_address(list):
    """Sorts a list of IPy.IP instances on hexlets/octets based on
    IP.version()."""
    return sorted(list, key=lambda x: x.int())


def sort_nets_by_prefixlength(nets):
    """Sorts a list with IPy.IP instances on prefix length."""
    nets.sort(key=lambda x: x.prefixlen())
    return nets


def getLastbitsIpMap(ip_list):
    """Returns a mapping between the last nybble and
    the whole IP address.

    Assumes:
        Unique end nybbles
        Fixed prefix length

    Arguemnts:
        ``ip_list'': list of IPy.IP instances

    Used by the presentation logic for Column-to-IP mapping
    """
    if not ip_list:
        return None

    version = ip_list[0].version()

    if version == 6:
        return _ipv6_getNybblesMap(ip_list)
    elif version == 4:
        return _ipv4_getLastbitsMap(ip_list)
    else:
        raise UnknownIpVersionError(str(version))


def _ipv4_getLastbitsMap(ip_list):
    return dict(
        zip(
            [
                i.net().strNormal()[i.net().strNormal().rfind('.') + 1 :]
                for i in ip_list
            ],
            ip_list,
        )
    )


def _ipv6_getNybblesMap(ip_list):
    """Finds the column where the IPs in the list should be displayed"""
    nybble_index = (ip_list[0].prefixlen() // 4) - 1
    return dict(
        zip(
            [i.net().strFullsize().replace(':', '')[nybble_index] for i in ip_list],
            ip_list,
        )
    )


def andIpMask(ip, mask):
    """Logical AND between ip and mask.

    Arguments:
        ``ip'': IPy.IP
        ``mask'': IPy.IP
    """
    base = IP(ip.net().int() & mask.net().int())
    return IP("{}/{}".format(base, mask.prefixlen()))


def getMask(ip_version, bit_count):
    """Generates a network mask with prefix length = bit_count.
    Returns IPy.IP instance.
    """
    if ip_version == 6:
        return _ipv6_getMask(bit_count)
    elif ip_version == 4:
        return _ipv4_getMask(bit_count)
    else:
        raise UnknownIpVersionError(str(ip_version))


def _ipv6_getMask(bit_count):
    result = IP("::/{}".format(bit_count)).netmask()
    return IP("{}/{}".format(result, bit_count))


def _ipv4_getMask(bit_count):
    result = IP("0.0.0.0/{}".format(bit_count)).netmask()
    return IP("{}/{}".format(result, bit_count))


def getLastSubnet(network, last_network_prefix_len=None):
    """
    Retrieves the last _possible_ subnet of the argument ``network''.
    Does not consider whether the subnet exists or not.

    Arguments:
        ``network'': The network in question

        ``last_network_prefix_len'': An optional specification of the prefix
                                     length of the last network. Defaults to
                                     32 for IPv6 and 128 for IPv6

    """
    if last_network_prefix_len is None:
        last_network_prefix_len = network.netmask().prefixlen()
    return IP(''.join([network.net().strNormal(), "/", str(last_network_prefix_len)]))


def get_next_subnet(net):
    """Returns the next subnet of the same size as net"""
    return IP(net.int() + net.len()).make_net(net.prefixlen())


def create_subnet_range(net, prefixlen):
    """Creates all subnets of the given size inside the net"""
    assert prefixlen >= net.prefixlen(), '{} < than {}'.format(net, prefixlen)
    # Return self as the net cannot be divided further
    if net.prefixlen() == prefixlen:
        return [net]
    subnet = IP("{}/{}".format(net.net().strNormal(), prefixlen))
    subnet_range = []
    while net.overlaps(subnet):
        subnet_range.append(subnet)
        subnet = get_next_subnet(subnet)
    return subnet_range

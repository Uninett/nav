# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Sorts and does calculations on IP addresses/nets."""

from IPy import IP
import math

class UnknownIpVersionError(Exception): pass

def sort_nets_by_address(list):
    """Sorts a list of IPy.IP instances on hexlets/octets based on
    IP.version()."""

    delimiter = None

    def tuplefy(address):
        list = map(lambda x: int(x,16),address.net().strFullsize().split(delimiter)) + [address]
        return tuple(list)

    if len(list) < 1:
        return list

    if list[0].version() == 6:
        delimiter = ':'
    elif list[0].version() == 4:
        delimiter = '.'

    decorate = map(tuplefy,list)
    decorate.sort()
    return [i[-1] for i in decorate]

def sort_nets_by_prefixlength(nets):
    """Sorts a list with IPy.IP instances on prefix length."""
    decorate = [(net.prefixlen(),net) for net in nets]
    decorate.sort()
    result = [i[-1] for i in decorate]
    return result

def netDiff(net1,net2):
    """Lists all the nets between net1 and net2.
    Assumes equal masklength

    Arguments:
        ``net1'': IPy.IP
        ``net2'': IPy.IP
    """
    assert net1.prefixlen()==net2.prefixlen()
    if net1.version() == 4:
        return _ipv4_net_diff(net1,net2)
    else:
        return _ipv6_net_diff(net1,net2)

def _ipv4_net_diff(net1,net2):
    if net1 > net2:
        (net1,net2) = (net2,net1)
    octets_to_the_right = (32-net1.prefixlen())/8
    net_prefix_len = int(float(net1.prefixlen())/8+0.5)*8
    return [IP("/".join([str(net),str(net1.prefixlen())])) for net in range(net1.int(), net2.int(), 256**octets_to_the_right)]

#this may be slow!
def _ipv6_net_diff(net1,net2):
    if net1 > net2:
        (net1,net2) = (net2,net1)
    host_hexlets = (128-net1.prefixlen())/16
    net_prefix_len = int(float(net1.prefixlen())/16+0.5)*16
    return [IP("/".join([str(net),str(net_prefix_len)])) for net in range(net1.int(), net2.int(), int(math.pow(2,16))**host_hexlets)]

def isIntermediateNets(net1,net2):
    if net1.version() != net2.version():
        raise NotEqualVersionError
    if net1.version() == 4:
        raise NotImplementedError
    else:
        return isIntermediateNetsIpv6(net1,net2)

def isIntermediateNetsIpv6(net1,net2):
    """Returns True if there are nets with the same prefixlength between net1
    and net2. This may be faster than using netDiff."""

    if net1.prefixlen() != net2.prefixlen():
        return True

    if net1 > net2:
        (net1,net2) = (net2,net1)

    ip1 = compress_light(net1)
    ip2 = compress_light(net2)

    ip1_array = ip1.split(":")
    ip2_array = ip2.split(":")

    for i in range(0,len(ip1_array)-1):
        if ip1_array[i] != ip2_array[i]:
            return True

    host_quads = (int(float(net1.prefixlen())/16+0.5)*16-net1.prefixlen())/4

    ip1_last_hexlet = ip1[ip1.rfind(':')+1:-host_quads]
    ip2_last_hexlet = ip2[ip2.rfind(':')+1:-host_quads]

    #This occurs when the last hexlet is only one quad long
    if len(ip1_last_hexlet) is 0:
        ip1_last_hexlet = ip1[-1]
    if len(ip2_last_hexlet) is 0:
        ip2_last_hexlet = ip2[-1]

    if int(ip2_last_hexlet,16)-int(ip1_last_hexlet,16) > 1:
        return True
    else:
        return False

def compress_light(ip):
    """Compress the ip address without removing any hexlets."""
    netaddr = None
    hexlets_in_address = int(float(ip.prefixlen())/16+0.5)
    if ip.prefixlen() < 112:
        netaddr = ip.net().strCompressed()[:-2]
    else:
        netaddr = ip.net().strCompressed()

    #in case .strCompressed() compressed it too much
    while netaddr.count(":") < hexlets_in_address-1:
        netaddr = ":".join([netaddr,"0"])

    return netaddr

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

    if ip_list is None or len(ip_list) < 1:
        return None

    version = ip_list[0].version()

    if version == 6:
        return _ipv6_getNybblesMap(ip_list)
    elif version == 4:
        return _ipv4_getLastbitsMap(ip_list)
    else:
        raise UnknownIpVersionError, str(version)

def _ipv4_getLastbitsMap(ip_list):
    return dict(zip([i.net().strNormal()[i.net().strNormal().rfind('.')+1:] for i in ip_list],ip_list))

def _ipv6_getNybblesMap(ip_list):
    start_nybble_index = None

    if ip_list[0].prefixlen() < 112:
        start_nybble_index = -3
    else:
        start_nybble_index = -1

    return dict(zip([i.net().strCompressed()[start_nybble_index:start_nybble_index+1] for i in ip_list],ip_list))

def andIpMask(ip,mask):
    """Logical AND between ip and mask.

    Arguments:
        ``ip'': IPy.IP
        ``mask'': IPy.IP
        """
    if ip.version() == 6:
        return _ipv6_andIpMask(ip,mask)
    elif ip.version() == 4:
        return _ipv4_andIpMask(ip,mask)
    else:
        raise UnknownIpVersionError, str(ip.version())

def _ipv6_andIpMask(ip,mask):
    ip_split = str(ip.net()).split(":")
    mask_split = str(mask.net()).split(":")
    assert len(ip_split) == len(mask_split) == 8
    supernet = ""
    for i in range(0,len(ip_split)):
        andOp = hexAnd(ip_split[i],mask_split[i])
        supernet = ":".join([supernet,andOp])
    return IP("/".join([supernet[1:],str(mask.prefixlen())]))

def _ipv4_andIpMask(ip,mask):
    ip_split = ip.net().strNormal().split(".")
    mask_split = mask.net().strNormal().split(".")
    assert len(ip_split)==len(mask_split)==4
    supernet = ""
    for i in range(0,len(ip_split)):
        andOp = int(ip_split[i]) & int(mask_split[i])
        supernet = ".".join([supernet,str(andOp)])
    return IP("/".join([supernet[1:],str(mask.prefixlen())]))

def hexAnd(hex1, hex2):
    """Logic AND for two hex number.

    ``hex1'', ``hex2'': hexadecimal numbers. Must be strings, function
        accepts both "0xFE" and "FE"."""
    dec1 = int(hex1,16)
    dec2 = int(hex2,16)
    result = dec1 & dec2
    return "%x" % result

def getMask(ip_version,bit_count):
    """Generates a network mask with prefix length = bit_count.
    Returns IPy.IP instance.
    """
    if ip_version == 6:
        return _ipv6_getMask(bit_count)
    elif ip_version == 4:
        return _ipv4_getMask(bit_count)
    else:
        raise UnknownIpVersionError, str(ip_version)

def _ipv6_getMask(bit_count):
    result = None
    mask_array = ['f' for i in range(0,bit_count/4)]
    mask_string = "".join(mask_array)
    last_nybble = bit_count % 4

    if last_nybble:
        last_nybble_dec = sum([2**(4-i) for i in range(1,last_nybble+1)])
        mask_string = "".join([mask_string,"%x" % last_nybble_dec])

    result = [mask_string[4*i:4+4*i] for i in range(0,int(float(bit_count)/16+0.5))]
    if len(result[-1]) < 4:
        for i in range(0,4-len(result[-1])):
            result[-1] = "".join([result[-1],"0"])
    result = ":".join(result)

    if bit_count < 112:
        result = "".join([result,"::"])
    return IP("/".join([result,str(bit_count)]))

def _ipv4_getMask(bit_count):
    ip_builder = ""
    temp = 0 
    for i in range(0,bit_count):
        if i % 8 == 0 and i > 0:
            ip_builder = ".".join([ip_builder,str(temp)])
            temp = 0 
        temp += 2**(7-(i%8))
    ip_builder = ".".join([ip_builder,str(temp)])
    ip_builder = ip_builder[1:]
    for i in range(0,4-len(ip_builder.split("."))):
        ip_builder = ".".join([ip_builder,"0"])
    return IP("/".join([ip_builder,str(bit_count)]))

def getLastSubnet(network, last_network_prefix_len=None):
    """ Retrieves the last _possible_ subnet of the argument ``network''.
        Does not consider whether the subnet exists or not.

        Arguments:
            ``network'': The network in question
            ``last_network_prefix_len'': An optional specification of the prefix length
                                         of the last network. Defaults to 32 for IPv6
                                         and 128 for IPv6
    """
    if last_network_prefix_len is None:
        last_network_prefix_len = network.netmask().prefixlen()
    return IP(''.join([network.net().strNormal(),"/",str(last_network_prefix_len)]))

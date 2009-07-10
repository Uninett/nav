import mibretriever

from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib

class CiscoIetfIpMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_ietf_ip_mib import MIB as mib

    @staticmethod
    def index_to_ip(index):
        """The index of cInetNetToMediaPhysAddress is of undetermined length, but
        the first 3 parts are always ifIndex, ip version and length.

        The remaining parts should either be of length 4 or 16, depending of ip
        version.

        This function checks the ip version and calls ipmib_index_to_ip if it's a
        IPv4 address or ipv6mib_index_to_ip if it's a IPv6 address.
        """
        ifIndex, ip_ver, length = index[0:3]
        ip = index[3:]
        if ip_ver == 1 and len(ip) == 4:
            return IpMib.index_to_ip(ip)
        elif ip_ver == 2 and len(ip) == 16:
            return Ipv6Mib.index_to_ip(ip)
        elif ip_ver == 3 and len(ip) == 5:
            # FIXME IP with zone, what to do?
            return IpMib.index_to_ip(ip[:-1])
        elif ip_ver == 4 and len(ip) == 17:
            # FIXME IPv6 with zone, what to do?
            return Ipv6Mib.index_to_ip(ip[:-1])
        else:
            raise IndexToIpException('Unknown ip version from Cisco MIB.')

import mibretriever

from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib

class CiscoIetfIpMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_ietf_ip_mib import MIB as mib

    @staticmethod
    def index_to_ip(ip_version, ip):
        """Takes ip_version and a tuple of undetermined length and returns a
        IPy.IP object witht the ip.
        """
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

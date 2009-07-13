from IPy import IP

import mibretriever

from nav.mibs.ip_mib import IndexToIpException

class Ipv6Mib(mibretriever.MibRetriever):
    from nav.smidumps.ipv6_mib import MIB as mib

    @staticmethod
    def index_to_ip(ip_set):
        """Takes a 16-tuple and joins it to a IPv6 address.
        Returns a IPy.IP object with the IP.
        """
        if len(ip_set) != 16:
            raise IndexToIpException('Number of tuples in IPv6 address given was less than 16.')
        ip_hex = ["%02x" % part for part in ip_set]
        ip = ':'.join([ip_hex[n] + ip_hex[n+1] for n,v in enumerate(ip_hex) if n % 2 == 0])
        return IP(ip)

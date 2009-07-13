from IPy import IP

import mibretriever

class IpMib(mibretriever.MibRetriever):
    from nav.smidumps.ip_mib import MIB as mib

    @staticmethod
    def index_to_ip(ip_set):
        """Takes a 4-tuple and joins it to a IPv4 address on the form a.b.c.d.
        Returns a IPy.IP object with the IP-address.
        """
        if len(ip_set) != 4:
            raise IndexToIpException('Number of tuples in IPv4 address given was not 4.')
        ip = '.'.join(["%d" % part for part in ip_set])
        return IP(ip)

class IndexToIpException(Exception):
    pass

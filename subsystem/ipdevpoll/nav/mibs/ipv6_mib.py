from IPy import IP

import mibretriever

from nav.mibs.ip_mib import IndexToIpException

class Ipv6Mib(mibretriever.MibRetriever):
    from nav.smidumps.ipv6_mib import MIB as mib

    @staticmethod
    def index_to_ip(index):
        """The index of ipv6NetToMediaPhysAddress is 17 parts (17 bytes in raw SNMP
        represented as a 17-tuple in python).

        The first part is an ifIndex, the remaining 16 is the IPv6 address for the
        MAC address returned.

        This function joins those 16 parts and returns an IP object.
        """
        # Use the last 16 parts
        offset = len(index) - 16
        if offset < 0:
            raise IndexToIpException('Number of tuples in IPv6 address given was less than 16.')

        ip_set = index[offset:]
        ip_hex = ["%02x" % part for part in ip_set]
        ip = ':'.join([ip_hex[n] + ip_hex[n+1] for n,v in enumerate(ip_hex) if n % 2 == 0])
        return IP(ip)

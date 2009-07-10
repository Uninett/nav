from IPy import IP

import mibretriever

class IpMib(mibretriever.MibRetriever):
    from nav.smidumps.ip_mib import MIB as mib

    @staticmethod
    def index_to_ip(index):
        """The index of ipNetToMediaPhysAddress is 5 parts (5 bytes in raw SNMP,
        represented as a 5-tuple in python).

        The first part is an ifIndex, the remaining 4 parts is the IPv4 address for
        the MAC address returned.

        This function joins those four parts and returns an IP object.
        """
        # Use the last 4 parts
        offset = len(index) - 4
        if offset < 0:
            raise IndexToIpException('Number of tuples in IPv4 address given was less than 4.')

        ip_set = index[offset:]
        ip = '.'.join(["%d" % part for part in ip_set])
        return IP(ip)

class IndexToIpException(Exception):
    pass

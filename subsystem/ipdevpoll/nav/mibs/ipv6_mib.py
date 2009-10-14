import mibretriever

from nav.mibs.ip_mib import IndexToIpException

class Ipv6Mib(mibretriever.MibRetriever):
    from nav.smidumps.ipv6_mib import MIB as mib

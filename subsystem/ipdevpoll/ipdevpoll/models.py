"""ipdevpoll internal data models.

To perform its polling duties, the ipdevpoll system must know what
netboxes to poll, what type netboxes are and what vendors they come
from, and finally, what snmpoids we want to poll.

To not interfere with the asynchronous nature of the polling, the data
contained in these models is read from the database and cached in
memory at periodic intervals, possibly by a separate thread.
"""
__author__ = "Morten Brekkevold (morten.brekkevold@uninett.no)"
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

from pysnmp.asn1.oid import OID

from twistedsnmp import snmpprotocol, agentproxy

from nav.db import getConnection
import ipdevpoll

def _load_helper(cls, sql):
    """Runs the sql query and yield instances of cls for each resulting row.

    The supplied SQL query must return a number of columns that can be
    mapped directly as arguments to the cls class constructor.

    """
    conn = getConnection('default')
    cursor = conn.cursor()
    cursor.execute(sql)
    for row in cursor.fetchall():
        yield cls(*row)

def load_models():
    """Loads all models into their respective caches"""
    Netbox.load()
    Type.load()
    SnmpOid.load()
    NetboxSnmpOid.load()

class Netbox(object):

    """A device with an IP address."""

    # Netbox instance store, key=netboxid
    all = {}

    def __init__(self, netboxid, ip, sysname, typeid, community, snmp_version, 
                 uptodate):
        self.netboxid = netboxid
        self.ip = ip
        self.sysname = sysname
        self.typeid = typeid
        self.community = community
        self.snmp_version = snmp_version
        self.uptodate = uptodate

        self.oidkeys = {}
        self.proxy = None
        self.logger = ipdevpoll.get_instance_logger(self,
                                                    "[%s]" % self.sysname)

    def __str__(self):
        return '%s(%s,%s,%s)' % (self.__class__.__name__, 
                                 repr(self.netboxid), repr(self.ip),
                                 repr(self.sysname))

    def __repr__(self):
        return '%s(%s,%s,%s,%s,%s,%s,%s)' % (
            self.__class__.__name__, 
            repr(self.ip),
            repr(self.sysname),
            repr(self.typeid),
            repr(self.community),
            repr(self.snmp_version),
            repr(self.uptodate),
            )

    @classmethod
    def load(cls):
        """Load netbox information from database and populate the Netbox.all
        dictionary with corresponding Netbox instances.
        """
        logger = ipdevpoll.get_class_logger(cls)
        # FIXME: This SQL selects only a subset of netboxes for testing
        sql = """
              SELECT netboxid, ip, sysname, typeid, ro, snmp_version, uptodate
              FROM netbox 
              WHERE ro IS NOT NULL
                AND up='y'
                AND roomid IN ('teknobyen', 'kaupangen')
              ORDER BY netboxid
              """
        # Count entries for debugging purposes
        counter = 0
        for netbox in _load_helper(cls, sql):
            cls.all[netbox.netboxid] = netbox
            counter += 1
        logger.debug('load: Loaded %d netboxes from database', counter)

    def get_proxy(self):
        """Return SNMP agent proxy to communicate with this netbox."""
        if not self.proxy:
            # choose random port in range 25000 to 30000
            port = snmpprotocol.port()
            self.proxy = agentproxy.AgentProxy(
                self.ip, 161,
                community = self.community,
                snmpVersion = 'v%s' % self.snmp_version,
                protocol = port.protocol,
            )
            self.logger.debug("AgentProxy created for %s: %s",
                              self.sysname, self.proxy)
        return self.proxy

    def release_proxy(self):
        """Release the SNMP agent proxy.

        Should be called when the proxy is no longer needed, and the
        corresponding UDP port can be freed.
        """
        del self.proxy
        self.proxy = None

    def get_table(self, oidkey):
        """Retrieve an SNMP table from the given oidkey and return a
        deferred.
        """
        snmpoid = SnmpOid.all[oidkey]
        df = self.get_proxy().getTable(
            [snmpoid.snmpoid], 
            timeout=1, 
            retryCount=5
            )
        return df

    def get(self, oidkey):
        """Retrieve a single SNMP value from the given oidkey, and return a
        deferred.
        """
        snmpoid = SnmpOid.all[oidkey]
        df = self.get_proxy().get(
            [snmpoid.snmpoid], 
            timeout=1, 
            retryCount=5
            )
        return df
            
    def is_supported_oid(self, key):
        """Verify that a given oidkey is supported by this netbox and return a
        boolean value.
        """
        return key in self.oidkeys

    def is_supported_all_oids(self, keys):
        """Verify that all oidkeys in the keys list are supported by this
        netbox and return a boolean value.
        """
        return all(key in self.oidkeys for key in keys)


class Type(object):

    """A device type with a sysObjectID"""

    all = {}
    by_sysobjectid = {}

    def __init__(self, typeid, vendor, name, sysobjectid, community_indexing,
                 interval, description):
        self.typeid = typeid
        self.vendor = vendor
        self.name = name
        self.sysobjectid = sysobjectid
        self.community_indexing = community_indexing
        self.interval = interval
        self.description = description

    def __repr__(self):
        return "%s(%s,%s,%s,%s,%s,%s,%s)" % (
            self.__class__.__name__,
            repr(self.typeid),
            repr(self.vendor),
            repr(self.name),
            repr(self.sysobjectid),
            repr(self.community_indexing),
            repr(self.interval),
            repr(self.description),
            )

    @classmethod
    def load(cls):
        """Load type rows from the database and popule the Type.all dictionary
        with corresponding Type instances.

        """
        logger = ipdevpoll.get_class_logger(cls)
        sql = """
              SELECT typeid, vendorid, typename, sysobjectid, cs_at_vlan, 
                     frequency, descr
              FROM "type"
              """
        # Count entries for debugging purposes
        counter = 0
        for typ in _load_helper(cls, sql):
            cls.all[typ.typeid] = typ
            cls.by_sysobjectid[ OID( typ.sysobjectid ) ] = typ
            counter += 1
        logger.debug('load: Loaded %d types from database', counter)


class Vendor(object):

    """A device vendor"""

    pass


class NetboxSnmpOid(object):

    """A Netbox OID profile entry with interval schedule."""

    # NetboxSnmpOid instance store, key=oidkey
    all = {}

    def __init__(self, netboxid, oidkey, interval):
        self.netboxid = netboxid
        self.oidkey = oidkey
        self.interval = interval

    def __repr__(self):
        return '%s(%s,%s,%s)' % (
            self.__class__.__name__,
            repr(self.netboxid),
            repr(self.oidkey),
            repr(self.interval),
            )

    @classmethod
    def load(cls):
        """Load all netboxsnmpoid rows from the database and populate the
        NetboxSnmpOid.all dictionary with corresponding NetboxSnmpOid
        instances.

        """
        logger = ipdevpoll.get_class_logger(cls)
        sql = """
              SELECT netboxid, oidkey, frequency
              FROM netboxsnmpoid
              JOIN snmpoid USING (snmpoidid)
              """
        # Count entries for debugging purposes
        counter = 0
        for ns in _load_helper(cls, sql):
            # Load into internal instance store
            key = (ns.netboxid, ns.oidkey)
            cls.all[key] = ns

            # Add mapping from Netboxes
            if ns.netboxid in Netbox.all:
                netbox = Netbox.all[ns.netboxid]
                netbox.oidkeys[ns.oidkey] = ns

            # Add mapping from SnmpOids
            if ns.oidkey in SnmpOid.all:
                snmpoid = SnmpOid.all[ns.oidkey]
                snmpoid.netboxes[ns.netboxid] = ns
            counter += 1
        logger.debug('load: Loaded %d netboxsnmpoids from database', counter)

class SnmpOid(object):

    """A pollable SNMP OID"""

    # SnmpOid instance store, key=oidkey
    all = {}

    def __init__(self, snmpoidid, oidkey, snmpoid, getnext, decodehex,
                 match_regex, default_interval, uptodate, mib):
        self.snmpoidid = snmpoidid
        self.oidkey = oidkey
        self.snmpoid = OID(snmpoid)
        self.getnext = getnext
        self.decodehex = decodehex
        self.match_regex = match_regex
        self.default_interval = default_interval
        self.uptodate = uptodate
        self.mib = mib

        self.netboxes = {}

    def __str__(self):
        return '%s(%s,%s,%s)' % (
            self.__class__.__name__,
            repr(self.snmpoidid), repr(self.oidkey), repr(self.snmpoid),
            ) 
    
    def __repr__(self):
        return '%s(%s,%s,%s)' % (
            self.__class__.__name__,
            repr(self.snmpoidid),
            repr(self.oidkey),
            repr(self.snmpoid),
            repr(self.getnext),
            repr(self.decodehex),
            repr(self.match_regex),
            repr(self.default_interval),
            repr(self.uptodate),
            repr(self.mib),
            )

    @classmethod
    def load(cls):
        """Load all SnmpOid rows from the database and populate the
        SnmpOid.all dictionary with corresponding SnmpOid instances.

        """
        logger = ipdevpoll.get_class_logger(cls)
        sql = """
              SELECT snmpoidid, oidkey, snmpoid, getnext, decodehex,
                     match_regex, defaultfreq, uptodate, mib
              FROM snmpoid
              """
        # Count entries for debugging purposes
        counter = 0
        for snmpoid in _load_helper(cls, sql):
            cls.all[snmpoid.oidkey] = snmpoid
            counter += 1
        logger.debug('load: Loaded %d snmpoids from database', counter)

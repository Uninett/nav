# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""ipdevpoll internal data models.

To perform its polling duties, the ipdevpoll system must know what
netboxes to poll, what type netboxes are and what vendors they come
from, and finally, what snmpoids we want to poll.

The model classes use Twisted's adbapi to utilize asynchronous
database queries.  The needed data is read from the database and
cached as instances in dictionaries in each model class.

Periodic reloads are scheduled through the reactor.
"""

import logging

from pysnmp.asn1.oid import OID

from twisted.internet import reactor, defer, task
from twistedsnmp import snmpprotocol, agentproxy

from nav.util import round_robin
from nav import ipdevpoll
from nav.ipdevpoll.db import get_db_pool

ports = round_robin([snmpprotocol.port() for i in range(10)])

def load_models():
    """Load, create and cache all model instances.

    Returns a deferred, whose result is a True value when all models
    have been loaded successfully.

    """
    logger = logging.getLogger(__name__)
    logger.info("load_models: Loading models from database")
    models_to_load = (Netbox, Type, SnmpOid, NetboxSnmpOid)
    receipts = [True]*len(models_to_load)
    deferred = defer.Deferred()

    def callback(result):
        """Callback to pop receipts off the stack."""
        receipts.pop()
        if len(receipts) == 0:
            # Fire callbacks of our own deferred when all load methods
            # have finished
            deferred.callback(True)

    for model in models_to_load:
        model.load().addCallback(callback)

    # Return our own deferred
    return deferred

def loop_load_models():
    """Run load_models in five minute intervals.
    
    The first call to load_models is run immediately, and its deferred
    is returned by this function (useful for initiating first poll
    runs after first model loading is complete).
    """
    deferred = load_models()
    loop = task.LoopingCall(load_models)
    loop.start(5*60.0, now=False)
    return deferred
    

class _MetaModel(type):

    """Model metaclass.

    This metaclass makes sure all model classes are initialized with
    separate "all" dictionary attributes.

    """

    def __init__(cls, name, bases, dict):
        super(_MetaModel, cls).__init__(name, bases, dict)
        cls.all = {}


class _Model(object):
    """Abstract base class for models defined in this module.

    A model class inheriting this class must define two class
    attributes:

      fields        -- a tuple of strings that will be used as
                       instance attributes for the model class.

      refresh_query -- an SQL query that produces rows that are
                       suitable for populating an instance of the
                       model class.  The columns returned by the query
                       must match the ordering as the fields tuple.
    
    All instances created in the class method "load" will be placed in
    a dictionary class attribute called "all".  The key to each
    instance is the first attribute listed in the fields tuple.  If
    you wish to override this behavior, you should override the
    add_to_cache instance method and write your own logic for this.

    """
    __metaclass__ = _MetaModel

    def __init__(self, *args):
        """Initialize an instance.

        Arguments must match the number and order of the class'
        attribute "fields".

        """
        if len(args) != len(self.__class__.fields):
            raise Exception("Hell")

        for name, value in zip(self.__class__.fields, args):
            setattr(self, name, value)

    def __repr__(self):
        values = [repr(getattr(self, name)) for name in self.__class__.fields]
        s = "%s(%s)" % (self.__class__.__name__,
                        ",".join(values))
        return s
        

    def __cmp__(self, other):
        """Compare this instance to other.

        Will compare instances as tuples of instance attributes, as
        defined by the class attribute "fields".

        """
        my_values = [getattr(self, name) for name in self.__class__.fields]
        other_values = [getattr(other, name) for name in self.__class__.fields]
        return cmp(my_values, other_values)

    def add_to_cache(self):
        """Add this instance to the class' cache dictionary "all".

        Uses the first attribute listed in the class' fields tuple as
        the dictionary key.  Override this method if this is not
        suitable, or you need multiple caches using different keys.

        """
        key_field = self.__class__.fields[0]
        key = getattr(self, key_field)
        self.__class__.all[key] = self

    @classmethod
    def load(cls):
        """Run the class' refresh_query against the database.

        Returns a deferred as returned by Twisted's
        ConnectionPool.runQuery method.  The internal classmethod
        _load_result is attached as the first callback, to load the
        results into the class cache.

        """
        deferred = get_db_pool().runQuery(cls.refresh_query)
        deferred.addCallback(cls._load_result)
        return deferred

    @classmethod
    def _load_result(cls, result):
        """Callback method to receive database results and make instances.

        The class cache cls.all is cleared and then an instance is
        created for each result row.  The instance is added to the
        class cache via the instance method add_to_cache.

        """
        logger = ipdevpoll.get_class_logger(cls)
        # Count entries for debugging purposes
        counter = 0
        cls.all.clear()
        for row in result:
            instance = cls(*row)
            instance.add_to_cache()
            counter += 1
        logger.debug('_load_result: Loaded %d %s instances from database', 
                     counter, cls.__name__)
        

class Netbox(_Model):

    """A device with an IP address."""

    fields = (
        'netboxid',
        'ip',
        'sysname',
        'typeid',
        'community',
        'snmp_version',
        'uptodate',
        )
    refresh_query = """
        SELECT netboxid, ip, sysname, typeid, ro, snmp_version, uptodate
        FROM netbox 
        WHERE ro IS NOT NULL AND
              up='y'
          AND roomid IN ('teknobyen', 'kaupangen')
        ORDER BY netboxid
        """

    def __init__(self, *args):
        super(Netbox, self).__init__(*args)
        self.proxy = None
        self.logger = ipdevpoll.get_instance_logger(self,
                                                    "[%s]" % self.sysname)

    def __str__(self):
        return '%s(%s,%s,%s)' % (self.__class__.__name__, 
                                 repr(self.netboxid), repr(self.ip),
                                 repr(self.sysname))

    @classmethod
    def _load_result(cls, result):
        """Callback to receive the results of a Netbox database query and
        update the instance cache.

        """
        logger = ipdevpoll.get_class_logger(cls)
        # Initialize various logging counters
        load_counter = new_counter = changed_counter = 0
        # Load new netboxes, changed netboxes and exsisting unchanged
        # netboxes into temp_dict.
        temp_dict = {}
        for row in result:
            netbox = cls(*row)
            load_counter += 1
            if netbox.netboxid not in cls.all:
                temp_dict[netbox.netboxid] = netbox
                new_counter += 1
            else:
                old_netbox = cls.all[netbox.netboxid]
                if netbox != old_netbox:
                    temp_dict[netbox.netboxid] = netbox
                    changed_counter += 1
                else:
                    temp_dict[netbox.netboxid] = old_netbox
        # Then clear and update Netbox.all with the contents of
        # temp_dict, thus removing instances that no longer exist.
        cls.all.clear()
        cls.all.update(temp_dict)
        # FIXME: We may need to give notice to other parts of the
        # system which netboxes have been removed.  Either that, or
        # other parts should use weak references to netbox objects so
        # that they'll notice that the objects are gone.

        logger.debug('_load_result: Loaded %d netboxes from database, '
                     '%d new, %d changed', 
                     load_counter, new_counter, changed_counter)

    def get_proxy(self):
        """Return SNMP agent proxy to communicate with this netbox."""

        if not self.proxy:
            # choose random port in range 25000 to 30000
            port = ports.next()

            self.proxy = agentproxy.AgentProxy(
                self.ip, 161,
                community = self.community,
                snmpVersion = 'v%s' % self.snmp_version,
                protocol = port.protocol,
            )
            self.logger.debug("AgentProxy created for %s: %s",
                              self.sysname, self.proxy)
        return self.proxy

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
        return (self.netboxid, key) in NetboxSnmpOid.all

    def is_supported_all_oids(self, keys):
        """Verify that all oidkeys in the keys list are supported by this
        netbox and return a boolean value.
        """
        return all((self.netboxid, key) in NetboxSnmpOid.all for key in keys)


class Type(_Model):

    """A device type with a sysObjectID"""

    by_sysobjectid = {}
    fields = (
        'typeid',
        'vendor',
        'name',
        'sysobjectid',
        'community_indexing',
        'interval',
        'description',
        )
    refresh_query = """
        SELECT typeid, vendorid, typename, sysobjectid, cs_at_vlan, 
               frequency, descr
        FROM "type"
        """

    def add_to_cache(self):
        self.__class__.all[self.typeid] = self
        self.__class__.by_sysobjectid[ OID( self.sysobjectid ) ] = self


class Vendor(object):

    """A device vendor"""

    pass


class NetboxSnmpOid(_Model):

    """A Netbox OID profile entry with interval schedule."""

    fields = (
        'netboxid',
        'oidkey',
        'interval',
        )
    refresh_query = """
        SELECT netboxid, oidkey, frequency
        FROM netboxsnmpoid
        JOIN snmpoid USING (snmpoidid)
        """
    def add_to_cache(self):
        key = (self.netboxid, self.oidkey)
        self.__class__.all[key] = self

class SnmpOid(_Model):

    """A pollable SNMP OID"""

    fields = (
        'snmpoidid',
        'oidkey',
        'snmpoid',
        'getnext',
        'decodehex',
        'match_regex',
        'default_interval',
        'uptodate',
        'mib',
        )
    refresh_query = """
        SELECT snmpoidid, oidkey, snmpoid, getnext, decodehex,
               match_regex, defaultfreq, uptodate, mib
        FROM snmpoid
        """

    def __init__(self, *args):
        super(SnmpOid, self).__init__(*args)
        if isinstance(self.snmpoid, basestring):
            self.snmpoid = OID(self.snmpoid)

    def __str__(self):
        return '%s(%s,%s,%s)' % (
            self.__class__.__name__,
            repr(self.snmpoidid), repr(self.oidkey), repr(self.snmpoid),
            ) 

    def add_to_cache(self):
        self.__class__.all[self.oidkey] = self


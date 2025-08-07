# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012, 2014, 2015 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details. You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""APIs to create MIB-aware retriever classes for asynchronous SNMP polling.

libsmi provides a command line tool (smidump) which can parse MIB
definitions and dump them as Python data structures.

To create a new MIB-aware retriever class, inherit from the
MibRetriever class and set the class-variable "mib" to point to a MIB
data structure as dumped by libsmi's smidump command.

The class will be imbued with knowledge of the MIB in question, and
several convenience methods to work with data retrieval.  An instance
of a MibRetriever class is tied to a TwistedSNMP AgentProxy and uses
this to allow asynchronous data retrieval.

"""

import logging

from pynetsnmp.netsnmp import SnmpTimeoutError
from twisted.internet import defer, reactor
from twisted.internet.error import TimeoutError
from twisted.python.failure import Failure

from nav.Snmp import safestring
from nav.ipdevpoll import ContextLogger
from nav.ipdevpoll.utils import fire_eventually
from nav.errors import GeneralException
from nav.oids import OID
from nav.smidumps import get_mib

_logger = logging.getLogger(__name__)
TEXT_TYPES = ("DisplayString", "SnmpAdminString")


class MibRetrieverError(GeneralException):
    """MIB retriever error"""

    pass


class MIBObject(object):
    """Representation of a MIB object.

    Member attributes:

    module
      The name of the MIB module where the object originated.
    name
      The object's textual name.
    oid
      The full object identifier
    enum
      If the object's syntax indicates it is an enumerated value,
      this dictionary will hold mappings between the enumerations textual
      names and integer values.  As a simplifying case,
      SNMPv2-TC::TruthValues will be deciphered as enums of boolean values.

    """

    def __init__(self, mib, name):
        self._mib = mib
        self.raw_mib_data = mib['nodes'][name]
        self.module = mib['moduleName']
        self.name = name
        self.oid = self.raw_mib_data['oid']
        self.enum = {}

        try:
            mib['nodes'][name]['syntax']['type']
        except KeyError:
            pass
        else:
            self._build_type()

    def _build_type(self):
        typ = self._mib['nodes'][self.name]['syntax']['type']
        if 'module' in typ and 'name' in typ:
            # the typedef is separate to the node
            # FIXME: Build typedef'ed enumerations only once for a mib
            typename = typ['name']
            module = get_mib(typ['module'])
            if module and typename in module['typedefs']:
                typ = module['typedefs'][typename]
            elif typ['module'] == 'SNMPv2-TC' and typename == 'TruthValue':
                self.enum = {1: True, 2: False}
                return

        if 'basetype' in typ and typ['basetype'] == 'Enumeration':
            # Build a two-way dictionary mapping enumerated names
            enums = [
                (k, int(val['number']))
                for k, val in typ.items()
                if isinstance(val, dict)
                and 'nodetype' in val
                and val['nodetype'] == 'namednumber'
            ]
            self.enum = dict(enums)
            self.enum.update((y, x) for (x, y) in enums)

    def to_python(self, value):
        """Translate an SNMP value into something python-like.

        If the syntax of this object is an Enumeration, value will be
        translated from and int to a str object.  If it is an
        SNMPv2-TC::TruthValue, it will be translated from int to bool.

        """
        if self.enum and isinstance(value, int) and value in self.enum:
            value = self.enum[value]
        return value

    def __lt__(self, other):
        """Compare to other based on OID."""
        if isinstance(other, self.__class__):
            return self.oid < other.oid
        else:
            return self.oid < other

    def __eq__(self, other):
        """Compare to other based on OID."""
        if isinstance(other, self.__class__):
            return self.oid == other.oid
        else:
            return self.oid == other

    def __repr__(self):
        return '<MibObject %r: %r from %r)' % (self.oid, self.name, self.module)


class MibTableDescriptor(object):
    """Description of a MIB table structure."""

    def __init__(self, table_object, row_object, column_objects):
        self.table = table_object
        self.row = row_object
        self.columns = column_objects

        # column numbers indexed by name
        self.column_index = dict((c.name, c.oid[-1]) for c in self.columns.values())
        # column names indexed by column numbers
        self.reverse_column_index = dict(
            (c.oid[-1], c.name) for c in self.columns.values()
        )

    def __repr__(self):
        return "%s(%r, %r, %r)" % (
            self.__class__.__name__,
            self.table,
            self.row,
            self.columns,
        )

    @classmethod
    def build(cls, mib, table_name):
        """Build and return a MibTableDescriptor for a MIB table.

        mib -- a MibRetriever instance.
        table_name -- the name of the table from the mib.

        """
        if (
            table_name not in mib.nodes
            or mib.nodes[table_name].raw_mib_data['nodetype'] != 'table'
        ):
            raise MibRetrieverError("%s is not a table" % table_name)

        table_object = mib.nodes[table_name]
        for node in mib.nodes.values():
            if (
                table_object.oid.is_a_prefix_of(node.oid)
                and node.raw_mib_data['nodetype'] == 'row'
            ):
                row_object = mib.nodes[node.name]
                # Only one row node type per table
                break

        columns = {}
        for node in mib.nodes.values():
            if (
                row_object.oid.is_a_prefix_of(node.oid)
                and node.raw_mib_data['nodetype'] == 'column'
            ):
                columns[node.name] = mib.nodes[node.name]

        return cls(table_object, row_object, columns)

    @classmethod
    def build_all(cls, mib):
        """Build table descriptors for all tables in a mib.

        mib -- MibRetriever instance"""
        table_descriptors = []
        for node in mib.nodes.values():
            if node.raw_mib_data['nodetype'] == 'table':
                table_descriptors.append(MibTableDescriptor.build(mib, node.name))
        return table_descriptors


class MibTableResultRow(dict):
    """A result row from a MIB table.

    Acts as a dictionary.  The row index is available through the
    integer key 0, or as the member attribute 'index'.
    """

    def __init__(self, index, columns=None):
        """Initialize with the row index of this row.

        :param index: index OID
        :param columns: optional list of column names to pre-allocate with None values.

        """
        if columns is None:
            columns = []
        dict.__init__(self, [(c, None) for c in columns])
        self.index = index
        self[0] = index


class MibRetrieverMaker(type):
    """Metaclass to create new functional MIB retriever classes.

    The MibRetriever base class uses this as its metaclass.  All new
    MIB retrievers should inherit inherit directly from the
    MibRetriever class.

    """

    # TODO: extract enumerations from mib typedefs and add as useful
    #       data structures.

    # MIB module registry.  Maps MIB module names to classes created
    # from this metaclass.
    modules = {}

    def __init__(cls, name, bases, dct):
        try:
            mib = dct['mib']
        except KeyError:
            try:
                mib = bases[0].mib
            except AttributeError:
                raise AttributeError("No mib attribute in class %s" % name)

        super(MibRetrieverMaker, cls).__init__(name, bases, dct)

        if mib is None:
            # This may be the MibRetriever base class or a MixIn of some sort
            return

        MibRetrieverMaker.__make_node_objects(cls)
        cls.tables = dict((t.table.name, t) for t in MibTableDescriptor.build_all(cls))

        MibRetrieverMaker.__make_scalar_getters(cls)
        MibRetrieverMaker.__make_table_getters(cls)
        MibRetrieverMaker.__prepopulate_text_columns(cls)

        MibRetrieverMaker.modules[mib['moduleName']] = cls

    # following is a collection of helper methods to modify the
    # MIB-aware retriever class that is being created.

    @staticmethod
    def __make_scalar_getters(cls):
        """Make a get_* method for every scalar MIB node."""
        for node in cls.nodes.values():
            if node.raw_mib_data['nodetype'] == 'scalar':
                method_name = 'get_%s' % node.name
                # Only create method if a custom one was not present
                if not hasattr(cls, method_name):
                    setattr(
                        cls, method_name, MibRetrieverMaker.__scalar_getter(node.name)
                    )

    @staticmethod
    def __scalar_getter(node_name):
        """Return a single get_* method for a scalar MIB node.

        node_name -- The name of the scalar node, e.g. ifDescr.

        """

        def result_formatter(result, the_oid, self):
            if the_oid in result or str(the_oid) in result:
                self._logger.debug("%s query result: %r", node_name, result)
                return result.get(the_oid, result.get(str(the_oid), None))
            else:
                self._logger.debug("%s was not in the result: %r", node_name, result)
                return None

        def getter(self):
            self._logger.debug("Retrieving scalar value %s", node_name)
            the_oid = self.nodes[node_name].oid
            df = self.agent_proxy.get([str(the_oid)])
            df.addCallback(result_formatter, the_oid, self)
            return df

        getter.__name__ = node_name
        return getter

    @staticmethod
    def __make_table_getters(cls):
        """Make a get_* method for all table MIB node."""
        for node_name in cls.tables.keys():
            setattr(
                cls, 'get_%s' % node_name, MibRetrieverMaker.__table_getter(node_name)
            )

    @staticmethod
    def __table_getter(node_name):
        """Return a single get_* method for a table MIB node.

        node_name -- The name of the table node, e.g. ifTable.

        """

        def getter(self):
            return self.retrieve_table(node_name)

        getter.__name__ = node_name
        return getter

    @staticmethod
    def __make_node_objects(cls):
        cls.nodes = dict(
            (node_name, MIBObject(cls.mib, node_name))
            for node_name in cls.mib['nodes'].keys()
        )

    @staticmethod
    def __prepopulate_text_columns(cls):
        """Prepopulates the new MibRetriever class' text_columns attribute
        with a set of names of contained MIB objects that can be considered as
        text types.

        """
        nodes = {
            node_name
            for node_name in cls.mib['nodes']
            if is_text_object(cls.mib, node_name)
        }
        cls.text_columns = nodes


class MibRetriever(object, metaclass=MibRetrieverMaker):
    """Base class for functioning MIB retriever classes."""

    mib = None
    nodes = None
    _logger = ContextLogger()

    def __init__(self, agent_proxy):
        """Create a new instance tied to an AgentProxy instance."""
        super(MibRetriever, self).__init__()
        self.agent_proxy = agent_proxy
        # touch _logger to initialize logging context right away
        self._logger

    def get_module_name(self):
        """Returns the MIB module"""
        return self.mib.get('moduleName', None)

    @defer.inlineCallbacks
    def get_next(self, object_name, translate_result=False):
        """Gets next sub-object of the named object"""
        oid = self.nodes[object_name].oid
        result = yield self.agent_proxy.walk(str(oid))
        if hasattr(result, 'items'):
            result = result.items()
        for key, value in result:
            if oid.is_a_prefix_of(key):
                if translate_result:
                    value = self.nodes[object_name].to_python(value)
                return value

    def retrieve_column(self, column_name):
        """Retrieve the contents of a single MIB table column.

        Returns a deferred whose result is a dictionary:

          { row_index: column_value }

        """
        node = self.nodes[column_name]
        if node.raw_mib_data['nodetype'] != 'column':
            self._logger.debug("%s is not a table column", column_name)

        def _result_formatter(result):
            formatted_result = {}
            # result keys may be OID objects/tuples or strings, depending on
            # snmp library used
            if node.oid not in result and str(node.oid) not in result:
                self._logger.debug(
                    "%s (%s) seems to be unsupported, result keys were: %r",
                    column_name,
                    node.oid,
                    result.keys(),
                )
                return {}
            varlist = result.get(node.oid, result.get(str(node.oid), None))

            for oid, value in varlist.items():
                # Extract index information from oid
                row_index = OID(oid).strip_prefix(node.oid)
                if column_name in self.text_columns:
                    value = safestring(value)
                formatted_result[row_index] = value

            return formatted_result

        def _snmp_timeout_handler(failure: Failure):
            """Transforms SnmpTimeoutErrors into "regular" TimeoutErrors"""
            failure.trap(SnmpTimeoutError)
            raise TimeoutError(failure.value)

        def _valueerror_handler(failure):
            failure.trap(ValueError)
            self._logger.warning(
                "got a possibly strange response from device "
                "when asking for %s::%s, ignoring: %s",
                self.mib.get('moduleName', ''),
                column_name,
                failure.getErrorMessage(),
            )
            return {}  # alternative is to retry or raise a Timeout exception

        deferred = self.agent_proxy.getTable([str(node.oid)])
        deferred.addErrback(_snmp_timeout_handler)
        deferred.addCallbacks(_result_formatter, _valueerror_handler)
        return deferred

    def retrieve_columns(self, column_names):
        """Retrieve a set of table columns.

        The table columns may come from different tables, as long as
        the table rows are indexed the same way.

        Returns a deferred whose result is a dictionary:

          { row_index: MibTableResultRow instance }

        """

        def _sortkey(col):
            return self.nodes[col].oid

        columns = iter(sorted(column_names, key=_sortkey))

        final_result = {}
        my_deferred = defer.Deferred()

        def _result_aggregate(result, column):
            for row_index, value in result.items():
                if row_index not in final_result:
                    final_result[row_index] = MibTableResultRow(row_index, column_names)
                final_result[row_index][column] = value
            return True

        # schedule the next iteration (i.e. collect next column)
        def _schedule_next(_result=None):
            try:
                column = next(columns)
            except StopIteration:
                my_deferred.callback(final_result)
                return
            deferred = self.retrieve_column(column)
            deferred.addCallback(_result_aggregate, column)
            deferred.addCallback(_schedule_next)
            deferred.addErrback(my_deferred.errback)

        reactor.callLater(0, _schedule_next)
        return my_deferred

    def retrieve_table(self, table_name):
        """Table retriever and formatter.

        Retrieves an entire MIB table.  Returns a deferred whose
        result is a dictionary:

          { row_index: MibTableResultRow instance }

        Each dictionary key is a row index (an oid suffix tuple).  Each
        dictionary value is a MibTableResultRow instance, which can be accessed
        as both a dictionary and a list.

        """
        table = self.tables[table_name]

        def _result_formatter(result):
            formatted_result = {}
            for varlist in result.values():
                # Build a table structure
                for oid in sorted(varlist.keys()):
                    if not table.table.oid.is_a_prefix_of(oid):
                        _msg = "Received wrong response from client, %s is not in %s"
                        raise MibRetrieverError(_msg % (oid, table.table.oid))

                    # Extract table position of value
                    oid_suffix = OID(oid).strip_prefix(table.row.oid)
                    column_no = oid_suffix[0]
                    row_index = oid_suffix[1:]
                    if column_no not in table.reverse_column_index:
                        self._logger.warning(
                            "device response has bad table index %s in %s::%s, "
                            "ignoring",
                            oid_suffix,
                            self.mib['moduleName'],
                            table_name,
                        )
                        continue
                    column_name = table.reverse_column_index[column_no]

                    if row_index not in formatted_result:
                        formatted_result[row_index] = MibTableResultRow(
                            row_index,
                            table.columns.keys(),
                        )

                    value = varlist[oid]
                    if column_name in self.text_columns:
                        value = safestring(value)
                    formatted_result[row_index][column_name] = value

            return formatted_result

        deferred = self.agent_proxy.getTable([str(table.table.oid)])
        deferred.addCallback(_result_formatter)
        return deferred

    @classmethod
    def translate_result(cls, result):
        """Translate result values to pythonic values according to object
        syntax.

        Given a table result from one of this object's retrievers,
        every column object will have it's to_python translation rules
        applied.  This is useful to insert into a callback chain for
        result formatting.

        """
        for row in result.values():
            for column in row.keys():
                if column in cls.nodes:
                    row[column] = cls.nodes[column].to_python(row[column])
        return result

    @defer.inlineCallbacks
    def retrieve_column_by_index(self, column, index):
        """Retrieves the value of a specific column for a given row index"""
        if column not in self.nodes:
            raise ValueError("No such object in %s: %s", self.mib['moduleName'], column)

        node = self.nodes[column]
        oid = node.oid + index
        result = yield self.agent_proxy._get([oid])
        for obj, value in result:
            assert obj == oid
            return node.to_python(value)


class MultiMibMixIn(MibRetriever):
    """Queries and chains the results of multiple MIB instances using
    community indexing.

    Useful for Cisco devices, whose SNMP agents employ multiple BRIDGE-MIB
    instances, one for each active VLAN, each indexable via a modified SNMP
    community.

    Add the mixin to the list of base classes of a MibRetriever descendant
    class, and override any querying method that should work across multiple
    instances.  The overriden method should use a call to self._multiquery().

    """

    def __init__(self, agent_proxy, instances):
        """Initializes a MultiBridgeQuery to perform SNMP requests on multiple
        BRIDGE-MIB instances on the same host/IP.

        :param agent_proxy: The base AgentProxy to use for communication. An
                            AgentProxy for each additional BRIDGE-MIB instance
                            will be created based on the properties of this
                            one.

        :param instances: A sequence of tuples describing the MIB instances to
                          query, like [(description, community), ...], where
                          description is any object that can be used to
                          identify an instance, and community is the alternate
                          MIB instance's SNMP read-community.

        """
        super(MultiMibMixIn, self).__init__(agent_proxy)
        self._base_agent = agent_proxy
        self.instances = instances

    @defer.inlineCallbacks
    def _multiquery(self, method, *args, **kwargs):
        """Runs method once for each known MIB instance.

        The internal AgentProxy will be temporarily replaced with one
        representing the current MIB instance for each iteration.

        :param integrator: A function that can take a list of (description,
                           result) tuples. description is the object
                           associated with an instance, as supplied to the
                           class constructor; result is the actual result
                           value of the call to method.

                           If omitted, the default integrator function is
                           self._dictintegrator().

        :returns: A deferred whose result is the return value of the
                  integrator.

        """
        agents = self._make_agents()
        if 'integrator' in kwargs:
            integrator = kwargs['integrator']
            del kwargs['integrator']
        else:
            integrator = self._dictintegrator
        results = []

        for agent, descr in agents:
            self._logger.debug("now querying %r", descr)
            if agent is not self._base_agent:
                agent.open()
            self.agent_proxy = agent
            try:
                one_result = yield method(*args, **kwargs).addErrback(
                    self.__timeout_handler, descr
                )
            finally:
                if agent is not self._base_agent:
                    agent.close()
                self.agent_proxy = self._base_agent
            results.append((descr, one_result))
            yield lambda thing: fire_eventually(thing)
        return integrator(results)

    def __timeout_handler(self, failure, descr):
        """Handles timeouts while processing alternate MIB instances.

        Under the premise that we may have an incorrect community string for a
        MIB instance, we don't want to derail the entire process of collecting
        from all instances, so we ignore timeouts for anything but the primary
        (base) instance.

        """
        if self.agent_proxy is not self._base_agent:
            failure.trap(TimeoutError, defer.TimeoutError)
            self._logger.debug("ignoring timeout from %r", descr)
            return None
        return failure

    @staticmethod
    def _dictintegrator(results):
        """Merges dictionary results from a _multiquery() call.

        If a key appears in multiple result dictionaries, the value from the
        last procesed dictionary will overwrite the value from any previous
        result dictionaries with the same key.  If this is not desirable you
        need to write a custom result integrator.

        """
        merged_dict = {}
        for _instance, result in results:
            if result is not None:
                merged_dict.update(result)
        return merged_dict

    def _make_agents(self):
        "Generates a series of alternate AgentProxy instances"
        instances = list(self._prune_instances())
        if not instances:
            # The un-indexed BRIDGE-MIB instance represents the default
            # VLAN. We only check this un-indexed instance if no alternate
            # instances were found, otherwise some results will be duplicated.
            yield (self._base_agent, None)
        for descr, community in instances:
            agent = self._get_alternate_agent(community)
            yield (agent, descr)

    def _prune_instances(self):
        """ "Prunes instances with duplicate community strings from the
        instance list, as these cannot possibly represent individual MIB
        instances in the queried devices.

        """
        seen_communities = set(self._base_agent.community)

        for descr, community in self.instances:
            if community not in seen_communities:
                seen_communities.add(community)
                yield (descr, community)

    def _get_alternate_agent(self, community):
        """Create an alternate AgentProxy using a different community.

        :returns: An instance of the same class as the AgentProxy object given
                  to __init__().  Every main attribute will be copied from the
                  original AgentProxy, except for the community string, which
                  will be taken from the MIB instance list..

        """
        agent = self._base_agent
        alt_agent = agent.__class__(
            agent.ip,
            agent.port,
            community=community,
            snmpVersion=agent.snmpVersion,
            snmp_parameters=agent.snmp_parameters,
        )
        if hasattr(agent, 'protocol'):
            alt_agent.protocol = agent.protocol

        return alt_agent


def is_text_object(mib_dict, obj_name):
    """Verifies whether a given MIB object has a syntax that can be considered
    a text type.
    """
    if not mib_dict or "nodes" not in mib_dict:
        return False
    syntax_type = mib_dict["nodes"][obj_name].get("syntax", {}).get("type", {})
    type_name = syntax_type.get("name", "")
    parent_type_name = syntax_type.get("parent module", {}).get("type", "")

    return type_name in TEXT_TYPES or parent_type_name in TEXT_TYPES

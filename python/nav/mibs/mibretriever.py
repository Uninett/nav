# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
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
import operator
from twisted.internet import defer, reactor

from nav.ipdevpoll import get_context_logger, get_class_logger
from nav.errors import GeneralException
from nav.oids import OID

logger = logging.getLogger(__name__)

class MibRetrieverError(GeneralException):
    """MIB retriever error"""
    pass

class MIBObject(object):
    """Representation of a MIB object.

    Member attributes:

    module -- The name of the MIB module where the object originated.
    name -- The object's textual name.
    oid -- The full object identifier
    enum -- If the object's syntax indicates it is an enumerated
            value, this dictionary will hold mappings between the
            enumerations textual names and integer values.  As a
            simplifying case, SNMPv2-TC::TruthValues will be
            deciphered as enums of boolean values.

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
            # FIXME: Support type defs from external mibs?
            # FIXME: Build typedef'ed enumerations only once for a mib
            typename = typ['name']
            if typ['module'] == self.module and \
                    typename in self._mib['typedefs']:
                typ = self._mib['typedefs'][typename]
            elif typ['module'] == 'SNMPv2-TC' and typename == 'TruthValue':
                # no True:1 translate because of wacky Python.
                # True is resolved as 1 anyway.
                self.enum = {1: True, 2: False, False: 2}
                return

        if 'basetype' in typ and typ['basetype'] == 'Enumeration':
            # Build a two-way dictionary mapping enumerated names
            enums = [(k, int(val['number']))
                     for k,val in typ.items()
                     if type(val) is dict and 'nodetype' in val and
                     val['nodetype'] == 'namednumber'
                     ]
            self.enum = dict(enums)
            self.enum.update((y, x) for (x, y) in enums)

    def to_python(self, value):
        """Translate an SNMP value into something python-like.

        If the syntax of this object is an Enumeration, value will be
        translated from and int to a str object.  If it is an
        SNMPv2-TC::TruthValue, it will be translated from int to bool.

        """
        if self.enum and isinstance(value, (int, long)) and value in self.enum:
            value = self.enum[value]
        return value

    def __cmp__(self, other):
        """Compare to others based on OID."""
        if isinstance(other, self.__class__):
            return cmp(self.oid, other.oid)
        else:
            return cmp(self.oid, other)

    def __repr__(self):
        return '<MibObject %r: %r from %r)' % \
            (self.oid, self.name, self.module)


class MibTableDescriptor(object):
    """Description of a MIB table structure."""

    def __init__(self, table_object, row_object, column_objects):
        self.table = table_object
        self.row = row_object
        self.columns = column_objects

        # column numbers indexed by name
        self.column_index = dict((c.name, c.oid[-1])
                                 for c in self.columns.values())
        # column names indexed by column numbers
        self.reverse_column_index = \
            dict((c.oid[-1], c.name) for c in self.columns.values())

    def __repr__(self):
        return "%s(%r, %r, %r)" % (self.__class__.__name__,
                                   self.table,
                                   self.row,
                                   self.columns)

    @classmethod
    def build(cls, mib, table_name):
        """Build and return a MibTableDescriptor for a MIB table.

        mib -- a MibRetriever instance.
        table_name -- the name of the table from the mib.

        """
        if table_name not in mib.nodes or \
               mib.nodes[table_name].raw_mib_data['nodetype'] != 'table':
            raise MibRetrieverError("%s is not a table" % table_name)

        table_object = mib.nodes[table_name]
        for node in mib.nodes.values():
            if table_object.oid.is_a_prefix_of(node.oid) and \
                    node.raw_mib_data['nodetype'] == 'row':
                row_object = mib.nodes[node.name]
                # Only one row node type per table
                break

        columns = {}
        for node in mib.nodes.values():
            if row_object.oid.is_a_prefix_of(node.oid) and \
                    node.raw_mib_data['nodetype'] == 'column':
                columns[node.name] = mib.nodes[node.name]

        return cls(table_object, row_object, columns)

    @classmethod
    def build_all(cls, mib):
        """Build table descriptors for all tables in a mib.

        mib -- MibRetriever instance"""
        table_descriptors = []
        for node in mib.nodes.values():
            if node.raw_mib_data['nodetype'] == 'table':
                table_descriptors.append(
                    MibTableDescriptor.build(mib, node.name))
        return table_descriptors

class MibTableResultRow(dict):
    """A result row from a MIB table.

    Acts as a dictionary.  The row index is available through the
    integer key 0, or as the member attribute 'index'.

    """
    def __init__(self, index, columns=None):
        """Initialize with the row index of this row.

        index -- index OID
        columns -- optional list of column names to pre-allocate with
                   None values.

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
        except KeyError, error:
            raise AttributeError("No mib attribute in class %s" % name)

        super(MibRetrieverMaker, cls).__init__(name, bases, dct)

        if name == 'MibRetriever' and mib is None:
            # This is the base retriever class, which is meant to be abstract
            return

        # modify mib data to slightly optimize later OID manipulation
        convert_oids(mib)

        MibRetrieverMaker.__make_node_objects(cls)
        cls.tables = dict((t.table.name, t)
                          for t in MibTableDescriptor.build_all(cls))

        MibRetrieverMaker.__make_scalar_getters(cls)
        MibRetrieverMaker.__make_table_getters(cls)

        MibRetrieverMaker.modules[ mib['moduleName'] ] = cls

        cls.logger = get_class_logger(cls)

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
                    setattr(cls, method_name,
                            MibRetrieverMaker.__scalar_getter(node.name))

    @staticmethod
    def __scalar_getter(node_name):
        """Return a single get_* method for a scalar MIB node.

        node_name -- The name of the scalar node, e.g. ifDescr.

        """
        def result_formatter(result, the_oid, self):
            if the_oid in result:
                self._logger.debug("%s query result: %r",
                                   node_name, result)
                return result[the_oid]
            else:
                self._logger.debug("%s was not in the result: %r",
                                   node_name, result)
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
            setattr(cls, 'get_%s' % node_name,
                    MibRetrieverMaker.__table_getter(node_name))

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
        cls.nodes = dict((node_name, MIBObject(cls.mib, node_name))
                         for node_name in cls.mib['nodes'].keys())

class MibRetriever(object):
    """Base class for functioning MIB retriever classes."""
    mib = None
    __metaclass__ = MibRetrieverMaker

    def __init__(self, agent_proxy):
        """Create a new instance tied to an AgentProxy instance."""
        super(MibRetriever, self).__init__()
        self.agent_proxy = agent_proxy
        self._logger = get_context_logger(self, sysname=agent_proxy.ip)

    def retrieve_column(self, column_name):
        """Retrieve the contents of a single MIB table column.

        Returns a deferred whose result is a dictionary:

          { row_index: column_value }

        """
        node = self.nodes[column_name]
        if node.raw_mib_data['nodetype'] != 'column':
            self._logger.debug("%s is not a table column", column_name)

        def resultFormatter(result):
            formatted_result = {}
            if str(node.oid) not in result:
                self._logger.debug("%s (%s) seems to be unsupported, result "
                                   "keys were: %r",
                                   column_name, node.oid, result.keys())
                return {}
            varlist = result[str(node.oid)]

            for oid, value in varlist.items():
                # Extract index information from oid
                row_index = OID(oid).strip_prefix(node.oid)
                formatted_result[row_index] = value

            return formatted_result

        deferred = self.agent_proxy.getTable([ str(node.oid) ], maxRepetitions=50)
        deferred.addCallback(resultFormatter)
        return deferred

    def retrieve_columns(self, column_names):
        """Retrieve a set of table columns.

        The table columns may come from different tables, as long as
        the table rows are indexed the same way.

        Returns a deferred whose result is a dictionary:

          { row_index: MibTableResultRow instance }

        """
        def sortkey(col):
            return self.nodes[col].oid
        columns = iter(sorted(column_names, key=sortkey))

        final_result = {}
        my_deferred = defer.Deferred()

        def result_aggregate(result, column):
            for row_index, value in result.items():
                if row_index not in final_result:
                    final_result[row_index] = \
                        MibTableResultRow(row_index, column_names)
                final_result[row_index][column] = value
            return True

        # schedule the next iteration (i.e. collect next column)
        def schedule_next(result=None):
            try:
                column = columns.next()
            except StopIteration:
                my_deferred.callback(final_result)
                return
            deferred = self.retrieve_column(column)
            deferred.addCallback(result_aggregate, column)
            deferred.addCallback(schedule_next)
            deferred.addErrback(my_deferred.errback)

        reactor.callLater(0, schedule_next)
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

        def resultFormatter(result):
            formatted_result = {}
            for varlist in result.values():
                # Build a table structure
                for oid in sorted(varlist.keys()):
                    if not table.table.oid.is_a_prefix_of(oid):
                        raise MibRetrieverError(
                            "Received wrong response from client,"
                            "%s is not in %s" % (oid, table.table.oid))

                    # Extract table position of value
                    oid_suffix = OID(oid).strip_prefix(table.row.oid)
                    column_no = oid_suffix[0]
                    row_index = oid_suffix[1:]
                    column_name = table.reverse_column_index[column_no]

                    if row_index not in formatted_result:
                        formatted_result[row_index] = \
                            MibTableResultRow(row_index, table.columns.keys())
                    formatted_result[row_index][column_name] = varlist[oid]

            return formatted_result


        deferred = self.agent_proxy.getTable([str(table.table.oid)],
                                             maxRepetitions=50)
        deferred.addCallback(resultFormatter)
        return deferred

    def translate_result(self, result):
        """Translate result values to pythonic values according to object
        syntax.

        Given a table result from one of this object's retrievers,
        every column object will have it's to_python translation rules
        applied.  This is useful to insert into a callback chain for
        result formatting.

        """
        for row in result.values():
            for column in row.keys():
                if column in self.nodes:
                    row[column] = self.nodes[column].to_python(row[column])
        return result

def convert_oids(mib):
    """Convert a mib data structure's oid strings to OID objects.

    mib is expected to be a data structure as dumped by the smidump utility
    (using the -python option).

    """
    for node_name in mib['nodes']:
        node = mib['nodes'][node_name]
        if isinstance(node['oid'], basestring):
            #oid_tuple = tuple(int(i) for i in node['oid'].split('.'))
            node['oid'] = OID(node['oid'])

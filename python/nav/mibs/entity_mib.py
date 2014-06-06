#
# Copyright (C) 2009-2011, 2014 UNINETT AS
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
"""Implements a MibRetriever for the ENTITY-MIB, as well as helper classes."""
from collections import defaultdict
from itertools import chain
from operator import itemgetter

from twisted.internet import defer

from nav.oids import OID
from nav.mibs import mibretriever

class EntityMib(mibretriever.MibRetriever):
    from nav.smidumps.entity_mib import MIB as mib

    def retrieve_alternate_bridge_mibs(self):
        """Retrieves a list of alternate bridge mib instances.

        This is accomplished by looking at entLogicalTable.  Returns a
        deferred whose result value is a list of tuples:: 

          (entity_description, community)

        :NOTE: Some devices will return entities with the same community.
               These should effectively be filtered out for polling purposes.
               A Cisco WS-C3560CG-8PC-S running IOS 15.0(2)SE has also been
               shown to return communities with null bytes,
               which are unusable and will be filtered.

        """
        # Define this locally to avoid external overhead
        bridge_mib_oid = OID('.1.3.6.1.2.1.17')
        def bridge_mib_filter(result):
            def _is_bridge_mib_instance_with_valid_community(row):
                return (row['entLogicalType']
                        and OID(row['entLogicalType']) == bridge_mib_oid
                        and '\x00' not in row['entLogicalCommunity'])

            new_result = [(r['entLogicalDescr'], r['entLogicalCommunity'])
                          for r in result.values()
                          if _is_bridge_mib_instance_with_valid_community(r)]
            return new_result

        df = self.retrieve_columns([
                'entLogicalDescr',
                'entLogicalType',
                'entLogicalCommunity'
                ])
        df.addCallback(bridge_mib_filter)
        return df

    def get_last_change_time(self):
        """Retrieves the sysUpTime value of the last time any of the
        ENTITY-MIB tables changed.

        """
        return self.get_next('entLastChangeTime')

    @defer.inlineCallbacks
    def _get_named_table(self, table_name):
        df = self.retrieve_table(table_name)
        df.addCallback(self.translate_result)
        ret_table = yield df
        named_table = EntityTable(ret_table)
        defer.returnValue(named_table)

    @defer.inlineCallbacks
    def get_entity_physical_table(self):
        phy_sensor_table = yield self._get_named_table('entPhysicalTable')
        defer.returnValue(phy_sensor_table)

    @defer.inlineCallbacks
    def get_useful_physical_table_columns(self):
        """Retrieves the most useful columns of the entPhysicalTable"""
        columns = yield self.retrieve_columns([
            'entPhysicalDescr',
            'entPhysicalContainedIn',
            'entPhysicalClass',
            'entPhysicalParentRelPos',
            'entPhysicalName',
            'entPhysicalHardwareRev',
            'entPhysicalFirmwareRev',
            'entPhysicalSoftwareRev',
            'entPhysicalSerialNum',
            'entPhysicalModelName',
            'entPhysicalIsFRU',
        ])
        defer.returnValue(self.translate_result(columns))


class EntityTable(dict):
    """Represent the contents of the entPhysicalTable as a dictionary"""
    def __init__(self, mibresult):
        # want single integers, not oid tuples as keys/indexes
        super(EntityTable, self).__init__()
        for row in mibresult.values():
            index = row[0][0]
            row[0] = index
            self[index] = row

        self.clean()

    def is_module(self, e):
        return e['entPhysicalClass'] == 'module' and \
            e['entPhysicalIsFRU'] and \
            e['entPhysicalSerialNum']

    def is_port(self, e):
        return e['entPhysicalClass'] == 'port'

    def is_chassis(self, e):
        return e['entPhysicalClass'] == 'chassis'

    def get_modules(self):
        """Return the subset of entities that are modules.

        A module is defined as an entity with class=module, being a
        field replaceable unit and having a non-empty serial number.

        Return value is a list of table rows.

        """

        modules = [entity for entity in self.values()
                   if self.is_module(entity)]
        return modules

    def get_ports(self):
        """Return the subset of entities that are physical ports.

        A port is defined as en entity class=port.

        Return value is a list of table rows.

        """
        ports = [entity for entity in self.values()
                 if self.is_port(entity)]
        return ports

    def get_chassis(self):
        """Return the subset of entities that are chassis.
        
        There will normally be only one chassis in a system, unless
        there is some sort of stcking involved.

        Return value is a list of table rows.

        """
        chassis = [entity for entity in self.values()
                   if self.is_chassis(entity)]
        return chassis

    def get_nearest_module_parent(self, entity):
        """Traverse the entity hierarchy to find a suitable parent module.

        Returns a module row if a parent is found, else None is returned.

        """
        parent_index = entity['entPhysicalContainedIn']
        if parent_index in self:
            parent = self[parent_index]
            if self.is_module(parent):
                return parent
            else:
                return self.get_nearest_module_parent(parent)

    def get_chassis_of(self, entity):
        """Returns the nearest parent chassis of an entity.

        Normally, all entities will resolve to the same chassis. In a stack,
        however, there may be multiple chassis.
        """
        while entity and not self.is_chassis(entity):
            parent_idx = entity['entPhysicalContainedIn']
            entity = self.get(parent_idx, None)
        return entity if entity and self.is_chassis(entity) else None

    def clean(self):
        """Cleans the table data"""
        self._strip_whitespace()
        self._fix_broken_chassis_relative_positions()
        self._rename_stack_duplicates()

    def _strip_whitespace(self):
        """Strips leading/trailing whitespace from all string data within"""
        for entity in self.values():
            for key, value in entity.items():
                if hasattr(value, 'strip'):
                    entity[key] = value.strip()

    def _fix_broken_chassis_relative_positions(self):
        """
        Some devices claim all chassis in a stack occupy the same relative
        position. If this is so, renumber their relative positions according to
        their position in the entPhysicalTable.
        """
        chassis = self.get_chassis()
        distinct_pos = set(c['entPhysicalParentRelPos'] for c in chassis)
        if len(distinct_pos) == len(chassis):
            return

        chassis.sort(key=itemgetter(0))
        for relpos, ent in enumerate(chassis, start=1):
            ent['_entPhysicalParentRelPos'] = ent['entPhysicalParentRelPos']
            ent['entPhysicalParentRelPos'] = relpos

    def _rename_stack_duplicates(self):
        """
        Renames entities with duplicate names by inserting the stack-relative
        positions of their owning chassis into their entPhysicalNames
        """
        if len(self.get_chassis()) < 2:
            return

        dupes = self._get_non_chassis_duplicates()
        for ent in chain(*dupes.values()):
            chassis = self.get_chassis_of(ent)
            name = ent.get('_entPhysicalName', ent.get('entPhysicalName'))
            ent['_entPhysicalName'] = name
            if chassis:
                relpos = chassis['entPhysicalParentRelPos']
                ent['entPhysicalName'] = "{0} [chassis {1}]".format(name,
                                                                    relpos)

    def _get_non_chassis_duplicates(self):
        """
        Returns a dict of all entities that have non-unique names.

        :returns: dict(name=[list of at least 2 entities with this name], ...)

        """
        dupes = defaultdict(list)
        for ent in self.values():
            if not self.is_chassis(ent):
                dupes[ent['entPhysicalName']].append(ent)
        dupes = dict((key, value) for key, value in dupes.iteritems()
                     if len(value) > 1)
        return dupes

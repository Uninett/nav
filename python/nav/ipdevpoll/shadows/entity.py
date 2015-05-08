#
# Copyright (C) 2015 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import
from datetime import datetime
from nav.toposort import build_graph, topological_sort

from nav.ipdevpoll.storage import Shadow, DefaultManager
from nav.models import manage
from nav.models.event import EventQueue as Event
from .netbox import Netbox

import networkx as nx
from networkx.algorithms.traversal.depth_first_search import dfs_tree as subtree


class EntityManager(DefaultManager):
    def __init__(self, *args, **kwargs):
        super(EntityManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)
        self.matched = set()
        self.missing = set()
        self.existing = set()

    def prepare(self):
        self.existing = set(manage.NetboxEntity.objects.filter(
            netbox__id=self.netbox.id).select_related('device'))
        by_id = {entitykey(e): e for e in self.existing}

        def _match(ent):
            # Matching by name isn't reliable, since names may not be unique,
            # or even present. Matching if entityPhysicalIndex is "ok",
            # but may have bad side effects if and when entities are
            # re-indexed by a device (e.g. by a reboot)
            return by_id.get(entitykey(ent))

        matches = ((ent, _match(ent)) for ent in self.get_managed())

        for collected, model in matches:
            if model:
                collected.set_existing_model(model)
                self.matched.add(model)

        self.missing = self.existing.difference(self.matched)

    def cleanup(self):
        if self.missing:
            w_serial = sum(int(m.device is not None) for m in self.missing)
            self._logger.info("%d entities have disappeared, %d of which have "
                              "known serial numbers",
                              len(self.missing), w_serial)

            to_purge = self.get_purge_list()
            to_set_missing = self.missing.difference(to_purge)
            self._logger.info("marking %d entities as missing, purging %d",
                              len(to_set_missing), len(to_purge))

            manage.NetboxEntity.objects.filter(
                id__in=[e.id for e in to_purge]).delete()
            manage.NetboxEntity.objects.filter(
                id__in=[e.id for e in to_set_missing],
                gone_since__isnull=True,
            ).update(gone_since=datetime.now())

    def get_purge_list(self):
        graph = self._build_dependency_graph()
        to_purge = set(self.missing)
        missing = (miss for miss in self.missing
                   if miss.device is not None)
        for miss in missing:
            if miss not in to_purge:
                continue
            sub = subtree(graph, miss)
            to_purge.difference_update(sub.nodes())
        return to_purge

    def _build_dependency_graph(self):
        self._logger.debug("building dependency graph")
        by_id = {entity.id: entity for entity in self.existing}
        graph = nx.DiGraph()

        for entity in self.existing:
            if entity.contained_in_id in by_id:
                parent = by_id[entity.contained_in_id]
                graph.add_edge(parent, entity)

        return graph

    def get_managed(self):
        """
        Returns managed containers in topological sort order; the point being
        that containers can be inserted into the database in the returned
        order without raising integrity errors.
        """
        managed = super(EntityManager, self).get_managed()
        graph = build_graph(
            managed,
            lambda ent: [ent.contained_in] if ent.contained_in else [])
        return topological_sort(graph)


def entitykey(ent):
    return '%s:%s' % (ent.source, ent.index)


def parententitykey(ent):
    if ent.contained_in:
        return '%s:%s' % (ent.source, ent.contained_in)


class NetboxEntity(Shadow):
    __shadowclass__ = manage.NetboxEntity
    manager = EntityManager

    def __init__(self, *args, **kwargs):
        super(NetboxEntity, self).__init__(*args, **kwargs)
        if 'gone_since' not in kwargs:
            # make sure to reset the gone_since timestamp on created records
            self.gone_since = None

    def __setattr__(self, key, value):
        if key == 'index' and value is not None:
            value = unicode(value)
        if key == 'contained_in' and value == 0:
            value = None
        super(NetboxEntity, self).__setattr__(key, value)

    @classmethod
    def get_chassis_entities(cls, containers):
        """Returns a list of chassis entities in containers

        :type containers: nav.ipdevpoll.storage.ContainerRepository
        """
        if cls in containers:
            entities = containers[cls].itervalues()
            return [e for e in entities
                    if e.physical_class == manage.NetboxEntity.CLASS_CHASSIS]
        else:
            return []


##
## Event dispatch functions
##


def _dispatch_down_event(django_entity):
    event = _make_chassisstate_event(django_entity)
    event.state = event.STATE_START
    event.varmap = {'alerttype': 'chassisDown'}
    event.save()


def _dispatch_up_event(django_entity):
    event = _make_chassisstate_event(django_entity)
    event.state = event.STATE_END
    event.varmap = {'alerttype': 'chassisUp'}
    event.save()


def _make_chassisstate_event(django_entity):
    event = Event()
    event.source_id = 'ipdevpoll'
    event.target_id = 'eventEngine'
    event.device = django_entity.device
    event.netbox = django_entity.netbox
    event.subid = unicode(django_entity.id)
    event.event_type_id = 'chassisState'
    return event


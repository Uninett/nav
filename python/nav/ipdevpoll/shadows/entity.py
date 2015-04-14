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
from nav.toposort import build_graph, topological_sort

from nav.ipdevpoll.storage import Shadow, DefaultManager
from nav.models import manage
from .netbox import Netbox


class EntityManager(DefaultManager):
    def __init__(self, *args, **kwargs):
        super(EntityManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)
        self.matched = set()
        self.missing = set()

    def prepare(self):
        existing = set(manage.NetboxEntity.objects.filter(
            netbox__id=self.netbox.id).select_related('device'))
        by_id = {entitykey(e): e for e in existing}

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

        self.missing = existing.difference(self.matched)

    def cleanup(self):
        if self.missing:
            self._logger.info("want to delete %d disappeared entities",
                              len(self.missing))

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

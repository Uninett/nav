#
# Copyright (C) 2012 Uninett AS
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
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""adjacency candidate storage and handling.

About sources
-------------

Each record has a source; typical sources are 'lldp', 'cam' and 'cdp'.

Record expiry
-------------

A database record that is not in the ContainerRepository will have its
miss_count incremented.  Any record whose miss_count >= MAX_MISS_COUNT will be
deleted from the database.

The AdjacencyManager will make note of which sources placed records in the
ContainerRepository.  If only the lldp collector plugin ran, records that came
from other sources will _NOT_ be targets of the expiration algorithm.

A collector plugin that found no records should place a sentinel record in the
ContainerRepository, to ensure that pre-existing database records from the
same source are expired properly.

Sentinels
---------

A sentinel record is an AdjacencyCandidate or UnrecognizedNeighbor instance whose
interface attribute is None, and whose source attribute is a non-empty string.

"""

from nav.models import manage
from nav.ipdevpoll.storage import Shadow, DefaultManager
from nav.ipdevpoll.utils import is_invalid_database_string
from .netbox import Netbox

MAX_MISS_COUNT = 3


class AdjacencyManager(DefaultManager):
    "Manages AdjacencyCandidate records"

    _existing = None
    _missing = None
    _sources = None

    def __init__(self, *args, **kwargs):
        super(AdjacencyManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)

    def prepare(self):
        self._load_existing()
        self._map_existing()

    def _load_existing(self):
        candidates = manage.AdjacencyCandidate.objects.filter(netbox__id=self.netbox.id)
        self._existing = dict((candidate_key(c), c) for c in candidates)

    def _map_existing(self):
        found = dict((candidate_key(c), c) for c in self.get_managed())
        self._sources = set()
        for key, cand in found.items():
            if key in self._existing:
                cand.set_existing_model(self._existing[key])
                # always reset miss_count of found records
                cand.miss_count = 0
            if cand.source:
                self._sources.add(cand.source)

        missing = set(self._existing.keys()).difference(found)
        self._missing = [
            self._existing[key]
            for key in missing
            if self._existing[key].source in self._sources
        ]

        self._logger.debug("existing: %r", self._existing)
        self._logger.debug("missing: %r", self._missing)
        self._logger.debug("sources: %r", self._sources)

    def cleanup(self):
        self._handle_missing()
        self._delete_expired()

    def _handle_missing(self):
        """Increments the miss_count of each missing adjacency candidate.

        Will only increment the counter for candidates that came from a source
        that found any records at all during this collection run.  I.e. if the
        cam collector ran, but not the lldp collector, we shouldn't consider
        lldp candidates to be missing.

        """
        missing = (c for c in self._missing if c.source in self._sources)
        for cand in missing:
            db_cand = manage.AdjacencyCandidate.objects.filter(id=cand.id)
            db_cand.update(miss_count=cand.miss_count + 1)

    def _delete_expired(self):
        expired = manage.AdjacencyCandidate.objects.filter(
            netbox__id=self.netbox.id, miss_count__gte=MAX_MISS_COUNT
        )
        expired.delete()


class AdjacencyCandidate(Shadow):
    __shadowclass__ = manage.AdjacencyCandidate
    manager = AdjacencyManager

    def get_existing_model(self, containers=None):
        "Returns only a cached object, if available"
        return getattr(self, '_cached_existing_model', None)

    def save(self, containers=None):
        "Does nothing if this is a sentinel object"
        if self.interface:
            return super(AdjacencyCandidate, self).save(containers)

    @classmethod
    def sentinel(cls, containers, source):
        """Creates or returns existing sentinel for source in containers.

        :param containers: A ContainerRepository.
        :param source: A source identifier string, e.g. 'lldp', 'cam', 'cdp',
                       etc.

        """
        candidate = containers.factory(source, cls)
        candidate.source = source
        return candidate


def candidate_key(cand):
    "return a (hopefully) unique dict key for a candidate object"
    # all this getattr yaking is trying to reduce the number of db fetches
    return (
        (getattr(cand, 'interface_id', None) or (cand.interface and cand.interface.id)),
        (getattr(cand, 'to_netbox_id', None) or (cand.to_netbox and cand.to_netbox.id)),
        (
            getattr(cand, 'to_interface_id', None)
            or (cand.to_interface and cand.to_interface.id)
        ),
        cand.source,
    )


class UnrecognizedNeighborManager(DefaultManager):
    """Manager for UnrecognizedNeighbor entries"""

    existing = None
    found = None
    sources = None

    def __init__(self, *args, **kwargs):
        super(UnrecognizedNeighborManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)

    def prepare(self):
        for record in self.get_managed():
            record.prepare()

        self._find_candidate_sources()
        self._load_and_map_existing()

    def _find_candidate_sources(self):
        if AdjacencyCandidate not in self.containers:
            return
        candidates = self.containers[AdjacencyCandidate].values()
        self.sources = set(c.source for c in candidates if c.source)

    def _load_and_map_existing(self):
        existing = manage.UnrecognizedNeighbor.objects.filter(
            netbox__id=self.netbox.id
        ).select_related('interface')
        self.existing = dict((self.make_key(e), e) for e in existing)
        self.found = dict((self.make_key(m), m) for m in self.get_managed())

        matched = set(self.found).intersection(self.existing)
        for key in matched:
            self.found[key].set_existing_model(self.existing[key])

    @staticmethod
    def make_key(obj):
        return obj.interface.id if obj.interface else None, obj.remote_id, obj.source

    def cleanup(self):
        missing = set(self.existing).difference(self.found)
        missing = (self.existing[key] for key in missing)
        deleteable = [m for m in missing if m.source in self.sources]
        if deleteable:
            self._logger.debug(
                "deleting %d missing records: %r", len(deleteable), deleteable
            )
            manage.UnrecognizedNeighbor.objects.filter(
                id__in=[d.id for d in deleteable]
            ).delete()


class UnrecognizedNeighbor(Shadow):
    __shadowclass__ = manage.UnrecognizedNeighbor
    __lookups__ = [('netbox', 'interface', 'remote_id')]
    manager = UnrecognizedNeighborManager

    def prepare(self, _=None):
        for attr in ('remote_id', 'remote_name'):
            if getattr(self, attr) and is_invalid_database_string(getattr(self, attr)):
                self._logger.debug(
                    "converting invalid %s: %r", attr, getattr(self, attr)
                )
                setattr(self, attr, repr(getattr(self, attr)))
            elif not getattr(self, attr):
                setattr(self, attr, '')
            elif not isinstance(getattr(self, attr), str):
                value = getattr(self, attr)
                setattr(self, attr, value.decode('utf-8'))

    def save(self, containers=None):
        """Does nothing if this is a sentinel object"""
        if self.interface:
            return super(UnrecognizedNeighbor, self).save(containers)

    @classmethod
    def sentinel(cls, containers, source):
        """Creates or returns existing sentinel for source in containers.

        :param containers: A ContainerRepository.
        :param source: A source identifier string, e.g. 'lldp', 'cam', 'cdp',
                       etc.

        """
        sentinel = containers.factory(source, cls)
        sentinel.source = source
        return sentinel

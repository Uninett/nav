#
# Copyright (C) 2009-2011 UNINETT AS
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
"""interface related shadow classes"""
import datetime
import operator
from itertools import groupby

from nav.models import manage
from nav.models.event import EventQueue as Event, EventQueueVar as EventVar

from nav.ipdevpoll.storage import Shadow, DefaultManager
from nav.ipdevpoll import db

from .netbox import Netbox

# pylint: disable=C0111

class InterfaceManager(DefaultManager):
    def __init__(self, *args, **kwargs):
        super(InterfaceManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)
        self.found_existing_map = {}

    def prepare(self):
        self._load_existing_objects()
        self._map_found_to_existing()
        for ifc in self.get_managed():
            ifc.prepare(self.containers)
        self._resolve_changed_ifindexes()

    def _load_existing_objects(self):
        db_ifcs = manage.Interface.objects.filter(netbox__id=self.netbox.id)

        self.db_ifcs = db_ifcs
        self.by_ifname = mapby(db_ifcs, 'ifname')
        self.by_ifnamedescr = mapby(db_ifcs, 'ifname', 'ifdescr')
        self.by_ifindex = mapby(db_ifcs, 'ifindex')

    def _map_found_to_existing(self):
        self.found_existing_map = dict(
            (snmp_ifc, self._find_existing_for(snmp_ifc))
            for snmp_ifc in self.get_managed())
        for found, existing in self.found_existing_map.items():
            if existing:
                found.set_existing_model(existing)

    def _find_existing_for(self, snmp_ifc):
        result = None
        if snmp_ifc.ifname:
            result = self.by_ifname.get(snmp_ifc.ifname, None)
        if not result and snmp_ifc.ifdescr:
            # this is only likely on a db recently migrated from NAV 3.5
            result = self.by_ifnamedescr.get(
                (snmp_ifc.ifdescr, snmp_ifc.ifdescr), None)
        if result and len(result) > 1:
            # Multiple ports with same name? damn...
            # also filter for ifindex, maybe we get lucky
            result = [i for i in result if i.ifindex == snmp_ifc.ifindex]

        # If none of this voodoo helped, try matching ifindex only
        if not result:
            result = self.by_ifindex.get(snmp_ifc.ifindex, None)

        if result and len(result) > 1:
            self._logger.debug(
                "_find_existing_for: multiple matching interfaces "
                "found for %r: %r", snmp_ifc, result)
            raise manage.Interface.MultipleObjectsReturned(
                "_find_existing_for: "
                "Found multiple matching interfaces for %r" % snmp_ifc)
        elif result:
            return result[0]

    def _resolve_changed_ifindexes(self):
        """Resolves conflicts that arise from changed ifindexes.

        The db model will not allow duplicate ifindex, so any ifindex
        that appears to have changed on the device must be nulled out
        in the database before we start updating Interfaces.

        """
        changed_ifindexes = [(new.ifindex, old.ifindex)
                             for new, old in self.found_existing_map.items()
                             if old and new.ifindex != old.ifindex]
        if not changed_ifindexes:
            return

        self._logger.debug("%s changed ifindex mappings (new/old): %r",
                           self.netbox.sysname, changed_ifindexes)

        changed_interfaces = self.db_ifcs.filter(
            ifindex__in=[new for new, old in changed_ifindexes])
        changed_interfaces.update(ifindex=None)


class Interface(Shadow):
    __shadowclass__ = manage.Interface
    manager = InterfaceManager

    @classmethod
    def cleanup_after_save(cls, containers):
        """Cleans up Interface data."""
        cls._mark_missing_interfaces(containers)
        cls._delete_missing_interfaces(containers)
        cls._generate_linkstate_events(containers)
        super(Interface, cls).cleanup_after_save(containers)

    @classmethod
    @db.commit_on_success
    def _mark_missing_interfaces(cls, containers):
        """Marks interfaces in db as gone if they haven't been collected in
        this round.

        This is designed to run in the cleanup_after_save phase, as it needs
        primary keys of the containers to have been found.

        """
        netbox = containers.get(None, Netbox)
        found_interfaces = containers[cls].values()
        timestamp = datetime.datetime.now()

        # start by finding the existing interface's primary keys
        pks = [i.id for i in found_interfaces if i.id]

        # the rest of the interfaces that haven't already been marked as gone,
        # should be marked as such
        missing_interfaces = manage.Interface.objects.filter(
            netbox=netbox.id, gone_since__isnull=True
            ).exclude(pk__in=pks)

        count = missing_interfaces.count()
        if count > 0:
            cls._logger.debug("_mark_missing_interfaces(%s): "
                              "marking %d interfaces as gone",
                              netbox.sysname, count)
        missing_interfaces.update(gone_since=timestamp)

    @classmethod
    @db.commit_on_success
    def _delete_missing_interfaces(cls, containers):
        """Deletes missing interfaces from the database."""
        netbox = containers.get(None, Netbox)
        ifcs = manage.Interface.objects.filter(netbox__id=netbox.id)
        missing_ifcs = ifcs.exclude(gone_since__isnull=True)

        deleteable = set(cls._get_indexless_ifcs_pk(missing_ifcs))
        deleteable.update(cls._get_dead_ifcs_pk(ifcs))

        if deleteable:
            cls._logger.info("(%s) Deleting %d missing interfaces",
                             netbox.sysname, len(deleteable))
            manage.Interface.objects.filter(pk__in=deleteable).delete()

    @staticmethod
    def _get_indexless_ifcs_pk(interfaces):
        indexless = interfaces.filter(ifindex__isnull=True).values('pk')
        return [row['pk'] for row in indexless]

    @staticmethod
    def _get_dead_ifcs_pk(interfaces,
                          grace_period = datetime.timedelta(days=1)):
        """Returns a list of primary keys of dead interfaces.

        An interface is considered dead if has a gone_since timestamp older
        than the grace period and is either not associated with a module or
        associated with a module known to still be up.

        """
        deadline = datetime.datetime.now() - grace_period
        ancient_ifcs = interfaces.filter(gone_since__lt = deadline)
        down_modules = manage.Module.objects.exclude(up='y')
        dead_ifcs = ancient_ifcs.exclude(module__in = down_modules)
        return [row['pk'] for row in dead_ifcs.values('pk')]

    @classmethod
    @db.commit_on_success
    def _generate_linkstate_events(cls, containers):
        changed_ifcs = [ifc for ifc in containers[cls].values()
                        if ifc.is_linkstate_changed()]
        if not changed_ifcs:
            return

        netbox = containers.factory(None, Netbox)
        cls._logger.debug("(%s) link state changed for: %s",
                          netbox.sysname,
                          ', '.join(ifc.ifname for ifc in changed_ifcs))

        linkstate_filter = cls.get_linkstate_filter()
        eventful_ifcs = [ifc for ifc in changed_ifcs
                         if ifc.matches_filter(linkstate_filter)]
        if eventful_ifcs:
            cls._logger.debug("(%s) posting linkState events for %r: %s",
                              netbox.sysname, linkstate_filter,
                              ', '.join(ifc.ifname for ifc in eventful_ifcs))

        for ifc in eventful_ifcs:
            ifc.post_linkstate_event()

    def is_linkstate_changed(self):
        return (hasattr(self, 'ifoperstatus_change')
                and bool(self.ifoperstatus_change))

    @classmethod
    def get_linkstate_filter(cls):
        from nav.ipdevpoll.config import ipdevpoll_conf as conf
        default = 'topology'
        link_filter = (conf.get('linkstate', 'filter')
                       if conf.has_option('linkstate', 'filter')
                       else default)

        if link_filter not in ('any', 'topology'):
            cls._logger.warning("configured linkstate filter is invalid: %r"
                                " (using %r as default)", link_filter, default)
            return default
        else:
            return link_filter

    def matches_filter(self, linkstate_filter):
        django_ifc = self._cached_converted_model
        if linkstate_filter == 'topology' and django_ifc.to_netbox:
            return True
        elif linkstate_filter == 'any':
            return True
        else:
            return False

    def post_linkstate_event(self):
        if not self.is_linkstate_changed():
            return

        oldstate, newstate = self.ifoperstatus_change
        if newstate == manage.Interface.OPER_DOWN:
            self._make_linkstate_event(True)
        elif newstate == manage.Interface.OPER_UP:
            self._make_linkstate_event(False)

    def _make_linkstate_event(self, start=True):
        django_ifc = self._cached_converted_model
        event = Event()
        event.source_id = 'ipdevpoll'
        event.target_id = 'eventEngine'
        event.netbox_id = self.netbox.id
        event.device = django_ifc.netbox.device
        event.subid = self.id
        event.event_type_id = 'linkState'
        event.state = event.STATE_START if start else event.STATE_END
        event.save()

        EventVar(event_queue=event, variable='alerttype',
                 value='linkDown' if start else 'linkUp').save()
        EventVar(event_queue=event, variable='interface',
                 value=self.ifname).save()
        EventVar(event_queue=event, variable='ifalias',
                 value=django_ifc.ifalias or '').save()

    def get_existing_model(self, containers=None):
        """Returns the set existing Django model instance, without attempting
        to lookup ourselves in the db.

        """
        return self._cached_existing_model

    def set_existing_model(self, django_object):
        super(Interface, self).set_existing_model(django_object)
        self._verify_operstatus_change(django_object)

    def _verify_operstatus_change(self, stored):
        if self.ifoperstatus != stored.ifoperstatus:
            self.ifoperstatus_change = (stored.ifoperstatus, self.ifoperstatus)
        else:
            self.ifoperstatus_change = None

    def prepare(self, containers):
        self._set_netbox_if_unset(containers)
        self._set_ifindex_if_unset(containers)

    def _set_netbox_if_unset(self, containers):
        """Sets this Interface's netbox reference if unset by plugins."""
        if self.netbox is None:
            self.netbox = containers.get(None, Netbox)

    def _set_ifindex_if_unset(self, containers):
        """Sets this Interface's ifindex value if unset by plugins."""
        if self.ifindex is None:
            interfaces = dict((v, k) for k, v in containers[Interface].items())
            if self in interfaces:
                self.ifindex = interfaces[self]


def mapby(items, *attrs):
    """Maps items by attributes"""
    keyfunc = operator.attrgetter(*attrs)
    groupgen = groupby(items, keyfunc)
    return dict((k, list(v)) for k, v in groupgen)

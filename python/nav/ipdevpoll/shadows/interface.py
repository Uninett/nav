#
# Copyright (C) 2009-2012 Uninett AS
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
"""interface related shadow classes"""

import datetime
import operator
from itertools import groupby

from django.db.models import Q
from django.db import transaction

from nav.models import manage
from nav.models.event import EventQueue as Event, EventQueueVar as EventVar
from nav.models.event import AlertHistory
from nav import natsort

from nav.ipdevpoll.storage import Shadow, DefaultManager

from .netbox import Netbox

MISSING_THRESHOLD = datetime.timedelta(days=1)
INFINITY = datetime.datetime.max


class InterfaceManager(DefaultManager):
    _found_existing_map = {}
    _db_ifcs = []
    _by_ifname = {}
    _by_ifnamedescr = {}
    _by_ifindex = {}
    _missing_ifcs = {}

    def __init__(self, *args, **kwargs):
        super(InterfaceManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)
        self.handle_missing = False

    def prepare(self):
        if self.sentinel in self.containers[Interface]:
            self.handle_missing = True
            self._logger.debug(
                "full interface table collected; "
                "will handle missing ones during cleanup"
            )
            del self.containers[Interface][self.sentinel]
            self._reset_baseport_numbers()

        for ifc in self.get_managed():
            ifc.prepare(self.containers)
        self._load_existing_objects()
        self._resolve_changed_ifindexes()
        self._resolve_linkstate_alerts()

    def _reset_baseport_numbers(self):
        """Explicitly sets baseport to None for interfaces where it wasn't
        touched.

        This is qto ensure that switch ports that have been deconfigured as such
        won't keep their switch port status in NAV.

        """
        for ifc in self.get_managed():
            if not ifc.baseport:
                ifc.baseport = None

    def _load_existing_objects(self):
        db_ifcs = manage.Interface.objects.filter(
            netbox__id=self.netbox.id
        ).select_related('module')
        self._make_maps(db_ifcs)

    def _make_maps(self, db_ifcs):
        self._db_ifcs = db_ifcs
        self._by_ifname = mapby(db_ifcs, 'ifname')
        self._by_ifnamedescr = mapby(db_ifcs, 'ifname', 'ifdescr')
        self._by_ifindex = mapby(db_ifcs, 'ifindex')

        self._found_existing_map = dict(
            (snmp_ifc, self._find_existing_for(snmp_ifc))
            for snmp_ifc in self.get_managed()
        )
        for found, existing in self._found_existing_map.items():
            if existing:
                found.set_existing_model(existing)

        self._missing_ifcs = dict(
            (ifc.id, ifc)
            for ifc in self._db_ifcs
            if (ifc not in self._found_existing_map.values() and not ifc.gone_since)
        )

    def _find_existing_for(self, snmp_ifc):
        result = None
        if snmp_ifc.ifname:
            result = self._by_ifname.get(snmp_ifc.ifname, None)
        if not result and snmp_ifc.ifdescr:
            # this is only likely on a db recently migrated from NAV 3.5
            result = self._by_ifnamedescr.get(
                (snmp_ifc.ifdescr, snmp_ifc.ifdescr), None
            )
        if result and len(result) > 1:
            # Multiple ports with same name? damn...
            # also filter for ifindex, maybe we get lucky
            result = [i for i in result if i.ifindex == snmp_ifc.ifindex]

        # If none of this voodoo helped, try matching ifindex only
        if not result:
            result = self._by_ifindex.get(snmp_ifc.ifindex, None)

        if result and len(result) > 1:
            self._logger.debug(
                "_find_existing_for: multiple matching interfaces found for %r: %r",
                snmp_ifc,
                result,
            )
            raise manage.Interface.MultipleObjectsReturned(
                "_find_existing_for: "
                "Found multiple matching interfaces for %r" % snmp_ifc
            )
        elif result:
            return result[0]

    def _resolve_changed_ifindexes(self):
        """Resolves conflicts that arise from changed ifindexes.

        The db model will not allow duplicate ifindex, so any ifindex
        that appears to have changed on the device must be nulled out
        in the database before we start updating Interfaces.

        """
        changed_ifindexes = [
            (new.ifindex, old.ifindex)
            for new, old in self._found_existing_map.items()
            if old and new.ifindex != old.ifindex
        ]
        if not changed_ifindexes:
            return

        self._logger.debug(
            "%s changed ifindex mappings (new/old): %r",
            self.netbox.sysname,
            changed_ifindexes,
        )

        changed_interfaces = self._db_ifcs.filter(
            ifindex__in=[new for new, old in changed_ifindexes]
        )
        changed_interfaces.update(ifindex=None)

    def _resolve_linkstate_alerts(self):
        alerts = self._get_unresolved_linkstate_alerts()
        need_to_resolve = set(
            ifc
            for ifc in self.get_managed()
            if not ifc.is_linkstate_changed()
            and ifc.id in alerts
            and ifc.ifoperstatus == manage.Interface.OPER_UP
        )
        self._logger.debug(
            "resolving link state alerts for these ifcs: %r",
            [ifc.ifname or ifc.ifdescr for ifc in need_to_resolve],
        )
        for ifc in need_to_resolve:
            ifc.ifoperstatus_change = (
                manage.Interface.OPER_DOWN,
                manage.Interface.OPER_UP,
            )
        self._ifcs_with_unresolved_alerts = need_to_resolve

    def _get_unresolved_linkstate_alerts(self):
        unresolved = AlertHistory.objects.filter(
            netbox=self.netbox.id, event_type__id='linkState', end_time__gte=INFINITY
        )
        interface_ids = [v['subid'] for v in unresolved.values('subid')]
        return [int(ifc_id) for ifc_id in interface_ids if ifc_id.isdigit()]

    def cleanup(self):
        """Cleans up Interface data."""
        if self.handle_missing:
            self._mark_missing_interfaces()
            self._delete_missing_interfaces()
        self._generate_linkstate_events()

    @transaction.atomic()
    def _mark_missing_interfaces(self):
        """Marks interfaces in db as gone if they haven't been collected in
        this round.

        """
        if self._missing_ifcs:
            self._logger.debug(
                "marking %d interface(s) as gone: %r",
                len(self._missing_ifcs),
                ifnames(self._missing_ifcs.values()),
            )

            missing = manage.Interface.objects.filter(id__in=self._missing_ifcs.keys())
            missing.update(gone_since=datetime.datetime.now())

    @transaction.atomic()
    def _delete_missing_interfaces(self):
        """Deletes missing interfaces from the database."""
        indexless = self._get_indexless_ifcs()
        dead = self._get_dead_ifcs()

        deleteable = set(indexless + dead)
        if deleteable:
            self._logger.info(
                "deleting %d missing interfaces: %s",
                len(deleteable),
                ifnames(deleteable),
            )
            pks = [ifc.id for ifc in deleteable]
            manage.Interface.objects.filter(pk__in=pks).delete()

    def _get_indexless_ifcs(self):
        return [ifc for ifc in self._db_ifcs if not ifc.ifindex]

    def _get_dead_ifcs(self):
        """Returns a list of dead interfaces.

        An interface is considered dead if has a gone_since timestamp older
        than the MISSING_THRESHOLD and is either not associated with a module or
        is associated with a module known to still be up.
        """
        deadline = datetime.datetime.now() - MISSING_THRESHOLD

        def is_dead(ifc):
            return (
                ifc.gone_since
                and ifc.gone_since < deadline
                and (not ifc.module or ifc.module.up == 'y')
            )

        return [ifc for ifc in self._db_ifcs if is_dead(ifc)]

    @transaction.atomic()
    def _generate_linkstate_events(self):
        changed_ifcs = [ifc for ifc in self.get_managed() if ifc.is_linkstate_changed()]
        if not changed_ifcs:
            return

        self._logger.debug("link state changed for: %s", ifnames(changed_ifcs))

        linkstate_filter = self.get_linkstate_filter()
        eventful_ifcs = [
            ifc
            for ifc in changed_ifcs
            if ifc.matches_filter(linkstate_filter)
            or ifc in self._ifcs_with_unresolved_alerts
        ]
        if eventful_ifcs:
            self._logger.debug(
                "posting linkState events for %r: %s",
                linkstate_filter,
                ifnames(eventful_ifcs),
            )

        for ifc in eventful_ifcs:
            ifc.post_linkstate_event()

    def get_linkstate_filter(self):
        from nav.ipdevpoll.config import ipdevpoll_conf as conf

        default = 'topology'
        link_filter = (
            conf.get('linkstate', 'filter')
            if conf.has_option('linkstate', 'filter')
            else default
        )

        if link_filter not in ('any', 'topology'):
            self._logger.warning(
                "configured linkstate filter is invalid: %r (using %r as default)",
                link_filter,
                default,
            )
            return default
        else:
            return link_filter


class Interface(Shadow):
    __shadowclass__ = manage.Interface
    manager = InterfaceManager
    ifoperstatus_change = None

    def is_linkstate_changed(self):
        return bool(self.ifoperstatus_change)

    def matches_filter(self, linkstate_filter):
        django_ifc = self.get_existing_model()
        if linkstate_filter == 'topology' and django_ifc.to_netbox:
            return True
        elif linkstate_filter == 'any':
            return True
        else:
            return False

    def post_linkstate_event(self):
        """
        Posts a linkState event, but only if the interface is
        administratively up and the link status has changed.
        """
        if not self.is_admin_up():
            self._logger.debug(
                "withholding linkState event, interface %s is not admUp",
                self.ifname or self.ifindex,
            )
            return

        if not self.is_linkstate_changed():
            return

        oldstate, newstate = self.ifoperstatus_change
        if newstate == manage.Interface.OPER_DOWN:
            self._make_linkstate_event(True)
        elif newstate == manage.Interface.OPER_UP:
            self._make_linkstate_event(False)

    def is_admin_up(self):
        """Returns True if interface is administratively up"""
        return self.ifadminstatus == manage.Interface.ADM_UP

    def _make_linkstate_event(self, start=True):
        django_ifc = self.get_existing_model()
        event = Event()
        event.source_id = 'ipdevpoll'
        event.target_id = 'eventEngine'
        event.netbox_id = self.netbox.id
        event.device = django_ifc.netbox.device
        event.subid = self.id
        event.event_type_id = 'linkState'
        event.state = event.STATE_START if start else event.STATE_END
        event.save()

        EventVar(
            event_queue=event,
            variable='alerttype',
            value='linkDown' if start else 'linkUp',
        ).save()
        EventVar(event_queue=event, variable='interface', value=self.ifname).save()
        EventVar(
            event_queue=event, variable='ifalias', value=django_ifc.ifalias or ''
        ).save()

    def get_existing_model(self, containers=None):
        """Returns the existing Django ORM object represented by this object.

        Will return the cached existing model if set.  If not, will use the
        primary key, if set, for database lookup.

        """
        if self._cached_existing_model:
            return self._cached_existing_model
        elif self.id:
            try:
                ifc = manage.Interface.objects.get(id=self.id)
            except manage.Interface.DoesNotExist:
                return None
            else:
                self._cached_existing_model = ifc
                return ifc

    def set_existing_model(self, django_object):
        super(Interface, self).set_existing_model(django_object)
        self._verify_operstatus_change(django_object)

    def _verify_operstatus_change(self, stored):
        if self.ifoperstatus and self.ifoperstatus != stored.ifoperstatus:
            self.ifoperstatus_change = (stored.ifoperstatus, self.ifoperstatus)
        else:
            self.ifoperstatus_change = None

    def prepare(self, containers):
        self._strip_null_bytes(containers)
        self._set_netbox_if_unset(containers)
        self._set_ifindex_if_unset(containers)
        self.gone_since = None

    def _strip_null_bytes(self, containers):
        """Strips null bytes from several string fields.

        As it turns out, some devices like to return these as part of interface names
        or descriptions, but we cannot insert those into the database.
        """
        for field in 'ifname', 'ifdescr', 'ifalias':
            value = getattr(self, field, None)
            if isinstance(value, str) and "\x00" in value:
                value = value.replace("\x00", "")
                setattr(self, field, value)

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

    @classmethod
    def add_sentinel(cls, containers):
        """Adds an Interface sentinel to a ContainerRepository, signifying
        that a full interface collection has taken place and that handling of
        missing interfaces can be safely performed by the manager.

        """
        containers.setdefault(cls, {})[cls.sentinel] = cls.sentinel


InterfaceManager.sentinel = Interface.sentinel = Interface()


class InterfaceStack(Shadow):
    __shadowclass__ = manage.InterfaceStack
    __lookups__ = [('higher', 'lower')]

    @classmethod
    def cleanup_after_save(cls, containers):
        """Delete from database the higher/lower combinations from this device
        that weren't found in the collected set.

        """
        collected_stackings = containers[cls].values()
        stacking_primary_keys = set(s.id for s in collected_stackings)
        collected_ifc_ids = set(
            ifc.id for ifc in containers[Interface].values() if ifc.id
        )

        existing = Q(higher__in=collected_ifc_ids) | Q(lower__in=collected_ifc_ids)
        obsolete = existing & ~Q(id__in=stacking_primary_keys)

        deleteable = manage.InterfaceStack.objects.filter(obsolete)
        deleteable.delete()


class InterfaceAggregate(Shadow):
    __shadowclass__ = manage.InterfaceAggregate
    __lookups__ = [('aggregator', 'interface')]

    @classmethod
    def cleanup_after_save(cls, containers):
        """Delete from database the aggregator/interface combinations from this
        device that weren't found in the collected set.

        """
        collected_aggregates = containers[cls].values()
        aggregate_primary_keys = set(s.id for s in collected_aggregates)
        collected_ifc_ids = set(
            ifc.id for ifc in containers[Interface].values() if ifc.id
        )

        existing = Q(aggregator__in=collected_ifc_ids) | Q(
            interface__in=collected_ifc_ids
        )
        obsolete = existing & ~Q(id__in=aggregate_primary_keys)

        deleteable = manage.InterfaceAggregate.objects.filter(obsolete)
        deleteable.delete()


def mapby(items, *attrs):
    """Maps items by attributes"""
    keyfunc = operator.attrgetter(*attrs)
    groupgen = groupby(items, keyfunc)
    return dict((k, list(v)) for k, v in groupgen)


def ifnames(ifcs):
    """Returns a loggable string of interface names from a list of Interface
    objects.

    """
    return ', '.join(sorted((ifc.ifname or 'None' for ifc in ifcs), key=natsort.split))

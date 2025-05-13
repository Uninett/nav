#
# Copyright (C) 2008-2012, 2016 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A shadow implementation of the nav.manage.Prefix model, and its manager"""

from nav.models import manage
from nav.ipdevpoll.storage import Shadow, DefaultManager
from .netbox import Netbox


PREFIX_AUTHORITATIVE_CATEGORIES = ('GW', 'GSW')


class PrefixManager(DefaultManager):
    """ "Manager of Prefix containers"""

    def cleanup(self):
        """Cleans up missing static prefixes"""
        if STATIC_ROUTES_SENTINEL not in self.get_managed():
            return  # no static route cleanup necessary

        missing = self._get_missing_static_prefixes()
        if missing:
            self._logger.info(
                "deleting missing static routes: %s",
                ",".join(p.net_address for p in missing),
            )
            missing.delete()

    def _get_missing_static_prefixes(self):
        netbox = self.containers.get(None, Netbox)
        sysname = netbox.sysname.split('.')[0]

        statics = (
            p
            for p in self.get_managed()
            if p.vlan and p.vlan.net_type and p.vlan.net_type.id == 'static'
        )
        collected_addrs = [str(p.net_address) for p in statics if p.net_address]
        missing_statics = manage.Prefix.objects.filter(
            vlan__net_type__id='static',
            vlan__net_ident__startswith=sysname,
        ).exclude(net_address__in=collected_addrs)
        return missing_statics


class Prefix(Shadow):
    """A shadow container for nav.model.Prefix data"""

    manager = PrefixManager
    __shadowclass__ = manage.Prefix
    __lookups__ = [('net_address', 'vlan'), 'net_address']

    def save(self, containers):
        if (
            self is STATIC_ROUTES_SENTINEL
            or self._is_not_authorized_to_modify_prefix(containers)
            or self._is_modification_of_existing_prefix_to_static()
        ):
            return
        else:
            return super(Prefix, self).save(containers)

    def _is_not_authorized_to_modify_prefix(self, containers):
        if self.get_existing_model():
            netbox = containers.get(None, Netbox).get_existing_model()
            if netbox.category_id not in PREFIX_AUTHORITATIVE_CATEGORIES:
                self._logger.debug(
                    "not updating existing prefix %s for box of category %s",
                    self.net_address,
                    netbox.category_id,
                )
                return True

    def _is_modification_of_existing_prefix_to_static(self):
        existing = self.get_existing_model()
        if existing:
            try:
                if (
                    self.vlan.net_type.id == 'static'
                    and existing.vlan.net_type.id != 'static'
                ):
                    self._logger.info(
                        "not changing existing prefix %s into static route",
                        self.net_address,
                    )
                    return True
            except AttributeError:
                return False  # maybe the proper attrs weren't set, ignore

    @classmethod
    def add_static_routes_sentinel(cls, containers):
        """
        Adds a sentinel to the container repository to signify the completed
        collection of static routes, meaning missing static routes can be
        safely pruned from the db.

        """
        containers.setdefault(cls, {})['static'] = STATIC_ROUTES_SENTINEL


STATIC_ROUTES_SENTINEL = Prefix()

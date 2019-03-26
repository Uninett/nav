#
# Copyright (C) 2009-2012, 2015 Uninett AS
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
"""netbox related shadow classes"""
from nav.models import manage
from django.db.models import Q
from django.db import transaction

from nav.ipdevpoll.storage import Shadow


# pylint: disable=C0111
class Netbox(Shadow):
    __shadowclass__ = manage.Netbox
    __lookups__ = ['sysname', 'ip']

    def __init__(self, *args, **kwargs):
        super(Netbox, self).__init__(*args, **kwargs)
        if args:
            obj = args[0]
            self.snmp_up = getattr(obj, 'snmp_up', not obj.is_snmp_down())
            self.last_updated = getattr(obj, 'last_updated',
                                        self._translate_last_jobs(obj))
            self.read_only = getattr(obj, 'read_only')
            self.snmp_version = getattr(obj, 'snmp_version')

    @staticmethod
    def _translate_last_jobs(netbox):
        """Compatibility method for translating a set of last run jobs for a
        Netbox into the structure expected by users of this class. This was
        made necessary because the Netbox objects initialized by the
        dataloder classes is no longer passed through to the JobHandler
        instances, just a netbox primary key, used to load a new Netbox
        instance from the database.

        :type netbox: nav.models.manage.Netbox

        :returns: A dict structured like the return value of
                  nav.ipdevpoll.dataloader.load_last_updated_times()

        """
        return {job.job_name: job.end_time
                for job in netbox.get_last_jobs()}

    def is_up(self):
        return self.up == manage.Netbox.UP_UP

    def copy(self, other):
        super(Netbox, self).copy(other)
        for attr in ('snmp_up', 'last_updated'):
            if hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))

    def prepare(self, containers):
        self._handle_sysname_conflicts(containers)

    def _handle_sysname_conflicts(self, containers):
        if self.id and self.sysname:
            other = manage.Netbox.objects.filter(~Q(id=self.id),
                                                 Q(sysname=self.sysname))
            if not other:
                return
            else:
                other = other[0]

            liveself = self.get_existing_model(containers)
            self._logger.warning(
                "%s and %s both appear to resolve to the same DNS name (%s)."
                "Are they the same device? Setting sysname = IP Address to "
                "avoid conflicts", liveself.ip, other.ip, self.sysname)
            self.sysname = liveself.ip

    @classmethod
    @transaction.atomic()
    def cleanup_replaced_netbox(cls, netbox_id, new_type):
        """Removes basic inventory knowledge for a netbox.

        When a netbox has changed type (sysObjectID), this can be called to set
        its new type, delete its modules and interfaces, and reset its
        up_to_date status.

        Arguments:

            netbox_id -- Netbox primary key integer.
            new_type -- A NetboxType shadow container representing the new
                        type.

        """
        type_ = new_type.convert_to_model() if new_type else None
        if type_:
            type_.save()

        netbox = manage.Netbox.objects.get(id=netbox_id)
        cls._logger.warning("Removing stored inventory info for %s",
                            netbox.sysname)
        netbox.type = type_
        netbox.up_to_date = False

        netbox.save()

        # Delete interfaces and stored hardware information
        netbox.module_set.all().delete()
        netbox.interface_set.all().delete()
        netbox.entity_set.all().delete()
        netbox.sensor_set.all().delete()
        netbox.powersupplyorfan_set.all().delete()
        netbox.info_set.filter(key='poll_times').delete()

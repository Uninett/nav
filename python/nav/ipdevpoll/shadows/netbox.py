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
"""netbox related shadow classes"""
from nav.models import manage

from nav.ipdevpoll.storage import Shadow
from nav.ipdevpoll import db

class Netbox(Shadow):
    __shadowclass__ = manage.Netbox
    __lookups__ = ['sysname', 'ip']

    def prepare(self, containers):
        """Attempts to solve serial number conflicts before savetime.

        Specifically, if another Netbox in the database is registered with the
        same serial number as this one, we empty this one's serial number to
        avoid db integrity conflicts.

        """
        if self.device and self.device.serial:
            try:
                other = manage.Netbox.objects.get(
                    device__serial=self.device.serial)
            except manage.Netbox.DoesNotExist:
                pass
            else:
                if other.id != self.id:
                    self._logger.warning(
                        "Serial number conflict, attempting peaceful "
                        "resolution (%s): "
                        "%s [%s] (id: %s) <-> %s [%s] (id: %s)",
                        self.device.serial, 
                        self.sysname, self.ip, self.id,
                        other.sysname, other.ip, other.id)
                    self.device.serial = None

    @classmethod
    @db.commit_on_success
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
        type_ = new_type.convert_to_model()
        if type_:
            type_.save()

        netbox = manage.Netbox.objects.get(id=netbox_id)
        cls._logger.warn("Removing stored inventory info for %s",
                         netbox.sysname)
        netbox.type = type_
        netbox.up_to_date = False

        new_device = manage.Device()
        new_device.save()
        netbox.device = new_device

        netbox.save()

        netbox.module_set.all().delete()
        netbox.interface_set.all().delete()



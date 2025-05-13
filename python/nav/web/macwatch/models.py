#
# Copyright (C) 2011 Uninett AS
# Copyright (C) 2022 Sikt
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
"""macwatch Django models"""

from django.db import models

from nav.macaddress import MacPrefix
from nav.models.fields import VarcharField
from nav.models.manage import Cam
from nav.models.profiles import Account


class MacWatch(models.Model):
    """Data-model for mac-address that should get watched
    by bin/macwatch"""

    MAC_ADDR_DELIM_CHAR = ':'

    id = models.AutoField(db_column='id', primary_key=True)
    # TODO: Create MACAddressField in Django
    mac = models.CharField(db_column='mac', max_length=17, unique=True)
    userid = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        db_column='userid',
        null=False,
        related_name="mac_watches",
    )
    description = VarcharField(db_column='description', null=True)
    created = models.DateTimeField(db_column='created', auto_now_add=True)
    # Used only when a mac-address prefix is given.  This is value of
    # the number for hex-digits (or so-called nybbles).
    prefix_length = models.IntegerField(db_column='prefix_length', null=True)

    class Meta(object):
        db_table = 'macwatch'
        ordering = ('created',)

    def __str__(self):
        return str(self.mac)

    def _filtered_mac_addr(self):
        """Returns the MAC address value with delimiters stripped"""
        return self.mac.replace(':', '').replace('-', '')

    def get_mac_addr(self):
        """Returns a string representation of the watched MAC address, whether
        it is a full or a partial (prefix) address
        """
        return str(self.get_mac_prefix())

    def get_mac_prefix(self):
        """Returns the watched MAC address as a MacPrefix object

        :rtype: nav.macaddress.MacPrefix
        """
        filtered_mac = self._filtered_mac_addr()
        prefix_mac = filtered_mac[0 : self.prefix_length]
        return MacPrefix(prefix_mac)


class MacWatchMatch(models.Model):
    """Extra model (helper-model) for mac-watch when macwatch
    only has a mac-adress prefix"""

    id = models.AutoField(db_column='id', primary_key=True)
    macwatch = models.ForeignKey(
        MacWatch,
        on_delete=models.CASCADE,
        db_column='macwatch',
        null=False,
        related_name="mac_watch_matches",
    )
    cam = models.ForeignKey(
        Cam,
        on_delete=models.CASCADE,
        db_column='cam',
        null=False,
        related_name="mac_watch_matches",
    )
    posted = models.DateTimeField(db_column='posted', auto_now_add=True)

    class Meta(object):
        db_table = 'macwatch_match'

    def __str__(self):
        return 'id=%s; macwatch = %s; cam = %s; posted = %s' % (
            self.id,
            self.macwatch,
            self.cam,
            self.posted,
        )

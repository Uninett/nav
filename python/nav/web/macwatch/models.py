#
# Copyright (C) 2011 UNINETT AS
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
"""macwatch Django models"""

import re

from django.db import models
from nav.models.fields import VarcharField
from nav.models.manage import Cam
from nav.models.profiles import Account


class MacWatch(models.Model):
    """Data-model for mac-address that should get watched
    by bin/macwatch.py"""
    MAC_ADDR_DELIM_CHAR = ':'

    id = models.AutoField(db_column='id', primary_key=True)
    # TODO: Create MACAddressField in Django
    mac = models.CharField(db_column='mac', max_length=17, unique=True)
    userid = models.ForeignKey(Account, db_column='userid', null=False)
    description = VarcharField(db_column='description', null=True)
    created = models.DateTimeField(db_column='created', auto_now_add=True)
    # Used only when a mac-address prefix is given.  This is value of
    # the number for hex-digits (or so-called nybbles).
    prefix_length = models.IntegerField(db_column='prefix_length', null=True)

    class Meta:
        db_table = u'macwatch'
        ordering = ('created',)

    def __unicode__(self):
        return u'%s' % self.mac

    def _filtered_mac_addr(self):
        """Filter delimiters from the mac-address."""
        return re.sub('-', '', re.sub(':', '', self.mac))

    def _add_separators(self, mac_addr):
        """Add delimiters between the hex-numbers. Check
        MAC_ADDR_DELIM_CHAR for delimiter-character."""
        # Extract every second chars at odd index
        mac_odds = mac_addr[::2]
        # Extract every second chars at even index
        mac_evens = mac_addr[1::2]
        # Add together one character from odd and one from even list,
        # and make lists with the strings.
        # Join the lists of strings with delimiter-character to form
        # a mac-address string.
        ret_addr = self.MAC_ADDR_DELIM_CHAR.join(odd_char + even_char
            for odd_char,even_char in zip(mac_odds, mac_evens))
        # Sweep up the left-over if length is even,
        # since zip will only merge a pair.
        if self.prefix_length % 2:
            ret_addr += self.MAC_ADDR_DELIM_CHAR + mac_addr[-1]
        return ret_addr


    def get_mac_addr(self):
        """Get the current mac-address.  If the stored
        mac-address is a prefix (i.e. only a partial mac-address)
        only the prefix will get returned."""
        if self.prefix_length and self.prefix_length > 0:
            filtered_mac = self._filtered_mac_addr()
            prefix_mac = filtered_mac[0:self.prefix_length]
            return self._add_separators(prefix_mac)
        else:
            return self.mac


class MacWatchMatch(models.Model):
    """Extra model (helper-model) for mac-watch when macwatch
    only has a mac-adress prefix"""
    id = models.AutoField(db_column='id', primary_key=True)
    macwatch = models.ForeignKey(MacWatch, db_column='macwatch', null=False)
    cam = models.ForeignKey(Cam, db_column='cam', null=False)
    posted = models.DateTimeField(db_column='posted', auto_now_add=True)

    class Meta:
        db_table = u'macwatch_match'

    def __unicode__(self):
        return (u'id=%d; macwatch = %d; cam = %d; posted = %s' %
                (self.id, self.macwatch, self.cam, str(self.posted)))

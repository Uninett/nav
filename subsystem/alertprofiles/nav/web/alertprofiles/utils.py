# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

"""Utility methods for Alert Profiles"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

from nav.models.profiles import Filter, FilterGroup, Account

# Admingroup is identified by having id/primary key 1.
ADMINGROUP = 1

def account_owns_filter(account, filter):
    """Checks if account have access to edit filter."""
    try:
        # Try to find owner, will raise DoesNotExist if there is no owner
        owner = filter.owner
    except Account.DoesNotExist:
        # There is no owner set, and that means the filter is public
        # Only admins are allowed to edit public filters, so check if account is
        # admin.
        groups = account.accountgroup_set.filter(pk=ADMINGROUP).count()
        if groups > 0:
            return True
        else:
            return False
    else:
        # Owner is set, check if account is the owner
        if owner == account:
            return True
        else:
            return False

def account_owns_filter_group(account, filter_group):
    """Checks if account have access to edit filter_group."""
    try:
        # Try to find owner, will raise DoesNotExist if there is no owner
        owner = filter_group.owner
    except Account.DoesNotExist:
        # There is no owner set, and that means the filtergroup is public
        # Only admins are allowed to edit public filtergroups, so check if account is
        # admin.
        groups = account.accountgroup_set.filter(pk=ADMINGROUP).count()
        if groups > 0:
            return True
        else:
            return False
    else:
        # Owner is set, check if account is the owner
        if owner == account:
            return True
        else:
            return False

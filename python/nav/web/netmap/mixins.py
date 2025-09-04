#
# Copyright (C) 2014 Uninett AS
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
"""Mixin classes for netmap"""

from django.core.exceptions import PermissionDenied

from nav.web.auth.utils import get_account
from nav.models.profiles import NetmapViewDefaultView, Account


class DefaultNetmapViewMixin(object):
    """
    Mixin for returning either a global or user specific
    default view
    """

    def get_context_data(self, user, **_kwargs):
        netmap_views = NetmapViewDefaultView.objects.select_related(
            'view',
        )
        try:
            view = netmap_views.get(owner=user).view
        except NetmapViewDefaultView.DoesNotExist:
            try:
                view = netmap_views.get(owner=Account.DEFAULT_ACCOUNT).view
            except NetmapViewDefaultView.DoesNotExist:
                view = None
        return {'default_view': view.viewid if view else None}


class AdminRequiredMixin(object):
    """Mixin for limiting view access to an admin user"""

    def dispatch(self, request, *args, **kwargs):
        if not get_account(request).is_admin():
            raise PermissionDenied
        return super(AdminRequiredMixin, self).dispatch(request, *args, **kwargs)

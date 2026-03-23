#
# Copyright (C) 2026 Sikt
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
"""Views for the allauth social account integration."""

from allauth.socialaccount.views import ConnectionsView


class NAVConnectionsView(ConnectionsView):
    """Custom connections view that adds connected provider IDs to the context.

    This allows the template to disable providers that the user has already
    connected, preventing duplicate connections.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["connected_providers"] = set(
            form.accounts.values_list("provider", flat=True)
        )
        return context

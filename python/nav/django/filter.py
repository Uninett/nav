#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Custom exception reporter filter that masks password fields unconditionally.

Django's default SafeExceptionReporterFilter only masks POST parameters when
the view has been decorated with @sensitive_post_parameters. If a crash occurs
in middleware before the view runs, the decorator never executes and cleartext
passwords end up in error emails.

This filter adds a defence-in-depth layer: any POST key whose name contains
"password" (case-insensitive) is always replaced with '********************',
regardless of whether the request has a sensitive_post_parameters attribute.
"""

import re

from django.views.debug import SafeExceptionReporterFilter

_PASSWORD_RE = re.compile(r"password", re.IGNORECASE)


class NAVExceptionReporterFilter(SafeExceptionReporterFilter):
    """Masks password-like POST parameters unconditionally."""

    def get_post_parameters(self, request):
        post_data = super().get_post_parameters(request)
        if isinstance(post_data, dict):
            post_data = {
                key: self.cleansed_substitute if _PASSWORD_RE.search(key) else value
                for key, value in post_data.items()
            }
        return post_data

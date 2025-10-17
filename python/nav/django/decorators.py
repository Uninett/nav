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
"""Custom django related decorators"""

from functools import wraps
from django.http import HttpResponse

from nav.web.auth.utils import get_account


def require_admin(func):
    """Decorator for requiring admin on a request"""

    @wraps(func)
    def _wrapper(request, *args, **kwargs):
        account = get_account(request)
        if account.is_admin():
            return func(request, *args, **kwargs)
        else:
            return HttpResponse(status=403)

    return _wrapper

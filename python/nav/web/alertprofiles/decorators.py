#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Alert Profiles helper decorators."""

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.functional import wraps

from nav.web.message import new_message, Messages

_ = lambda a: a


def requires_post(redirect='alertprofiles-overview', required_args=None):
    """Decorates a view function to require a POST request.

    If the view function was not reached via a POST request, a session
    error message is generated, and the client is redirected to the
    specified redirect view.

    """

    def _required_args_are_present(request):
        if required_args is not None:
            for arg in required_args:
                if not request.POST.get(arg):
                    return False
        return True

    def _decorator(func):
        def _handler(request, *args, **kwargs):
            error = None
            if request.method == 'POST':
                if _required_args_are_present(request):
                    return func(request, *args, **kwargs)
                else:
                    error = _('Required post-data were not supplied')
            else:
                error = _('There was no post-data')

            new_message(request, error, Messages.ERROR)
            return HttpResponseRedirect(reverse(redirect))

        return wraps(func)(_handler)

    return _decorator

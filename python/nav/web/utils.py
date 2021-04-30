#
# Copyright (C) 2012 (SD -311000) Uninett AS
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
"""Utils for views"""

from django.http import HttpResponse


from django.views.generic.list import ListView


def get_navpath_root():
    """Returns the default navpath root

    To be used in the navpath argument to the base template
    navpath = [get_navpath_root(), ('Tool', )]
    """
    return 'Home', '/'


def create_title(navpath):
    """Create title from navpath (or any other array of tuples)"""
    return " - ".join([x[0] for x in navpath])


class SubListView(ListView):
    """Subclass of the generic list ListView to allow extra context"""

    extra_context = {}

    def get_context_data(self, *args, **kwargs):
        context = super(SubListView, self).get_context_data(*args, **kwargs)
        context.update(self.extra_context)
        return context


def require_param(parameter):
    """A decorator for requiring parameters

    Will check both GET and POST querydict for the parameter.
    """
    # pylint: disable=missing-docstring
    def wrap(func):
        def wrapper(request, *args, **kwargs):
            if parameter in request.GET or parameter in request.POST:
                return func(request, *args, **kwargs)
            else:
                return HttpResponse(
                    "Missing parameter {}".format(parameter), status=400
                )

        return wrapper

    return wrap

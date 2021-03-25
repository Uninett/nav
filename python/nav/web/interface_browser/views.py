# Copyright (C) 2018 Uninett AS
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
"""Controllers and views for PortList tool"""

from django.shortcuts import render

from nav.web import utils


def default_context():
    navpath = (('Home', '/'), ('Interface browser',))
    return {'navpath': navpath, 'title': utils.create_title(navpath)}


def index(request):
    context = default_context()
    return render(request, 'interface_browser/base.html', context)


def by_netboxid(request, netboxid):
    context = default_context()
    context.update({'netboxid': netboxid})
    return render(request, 'interface_browser/base.html', context)

#
# Copyright (C) 2012 (SD -311000) UNINETT AS
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
"""Views for Arnold"""

from django.shortcuts import render_to_response
from django.template import RequestContext
from nav.web.utils import create_title

NAVPATH = [('Home', '/'), ('Arnold', '/arnold')]

def index(request):
    """Main controller for Arnold"""
    return render_to_response(
        'arnold/base.html',
        {
            'navpath': NAVPATH,
            'title': create_title(NAVPATH)
        },
        context_instance = RequestContext(request)
    )


def render_history(request):
    """Controller for rendering arnold history"""
    return render_to_response(
        'arnold/history.html',
        {},
        context_instance = RequestContext(request)
    )


def render_detained_ports(request):
    """Controller for rendering detained ports"""
    return render_to_response(
        'arnold/detainedports.html',
        {},
        context_instance = RequestContext(request)
    )


def render_search(request):
    """Controller for rendering search"""
    pass


def render_detention_reason(request):
    """Controller for rendering detention reasons"""
    pass


def render_manual_detention(request):
    """Controller for rendering manual detention"""
    pass


def render_predefined_detentions(request):
    """Controller for rendering predefined detentions"""
    pass


def render_quarantine_vlans(request):
    """Controller for rendering quarantine vlans"""
    pass

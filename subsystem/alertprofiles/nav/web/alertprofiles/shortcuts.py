# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Shortcuts for Alert Profiles"""

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.template import RequestContext

from nav.web.message import new_message, Messages
from django.shortcuts import render_to_response

def _alertprofiles_response(request, status_code=200):
    # Get a normal response object
    response = render_to_response(
        'alertprofiles/base.html',
        None,
        context_instance=RequestContext(
            request,
        ),
    )

    # Change the status_code
    response.status_code = status_code

    return response

def alertprofiles_response_forbidden(request, message):
    new_message(request, '403 Forbidden', Messages.ERROR)
    new_message(request, message, Messages.ERROR)

    return _alertprofiles_response(request, 403)

def alertprofiles_response_not_found(request, message):
    new_message(request, '404 Not Found', Messages.ERROR)
    new_message(request, message, Messages.ERROR)

    return _alertprofiles_response(request, 404)

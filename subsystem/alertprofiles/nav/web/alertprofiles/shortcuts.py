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

"""Shortcuts for Alert Profiles"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.template import RequestContext

from nav.web.message import new_message, Messages
from nav.django.shortcuts import render_to_response, object_list
from nav.web.templates.AlertProfilesTemplate import AlertProfilesTemplate

def _alertprofiles_response(request, status_code=200):
    # Get a normal response object
    response = render_to_response(
        AlertProfilesTemplate,
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

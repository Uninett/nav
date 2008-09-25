# -*- coding: utf-8 -*-
#
# Copyright 2007 UNINETT AS
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
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

"""Shortcuts for using Django with NAV and Cheetah"""
"""Utility methods for django"""

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

from django.http import HttpResponseForbidden

from nav.models.profiles import Account

def get_account(request):
    """Extracts users login from sessionvariables and looks up the
    corresponding account in the database
    """

    return Account.objects.get(login=request._req.session['user'].login)

def permission_required(function):
    """Decorator to check if user have access"""
    def _check_permission(request, *args, **kwargs):
        account = get_account(request)
        if account.has_perm('web_access', request.path):
            return function(request, *args, **kwargs)
        else:
            # FIXME better 403 handling
            return HttpResponseForbidden('<h1>403 Forbidden</h1><p>You do not have access to this page</p>')
    return _check_permission

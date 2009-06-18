# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Views for status tool"""

from nav.web.templates.StatusTemplate import StatusTemplate
from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account

from nav.web.status.sections import get_user_sections

def status(request):
    '''Main status view.'''
    pass

def preferences(request):
    '''Allows user customization of the status page.'''
    account = get_account(request)
    sections = get_user_sections(account)
    return render_to_response(
        StatusTemplate,
        'templates/preferences.html',
        {
            'sections': sections,
        },
        RequestContext(request)
    )

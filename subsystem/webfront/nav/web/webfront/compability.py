# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.template.loader import render_to_string

from nav.models.profiles import Account
from nav.buildconf import VERSION

def header(user, title, navpath):
    account = Account.objects.get(id=user['id'])
    return render_to_string(
        'header.html',
        {
            'title': title,
            'navpath': navpath,
            'account': account,
            'navbar': user['preferences']['navbar'],
            'qlink1': user['preferences']['qlink1'],
            'qlink2': user['preferences']['qlink2'],
        }
    )

def footer(user):
    account = Account.objects.get(id=user['id'])
    return render_to_string(
        'footer.html',
        {
            'account': account,
            'version': VERSION,
        }
    )

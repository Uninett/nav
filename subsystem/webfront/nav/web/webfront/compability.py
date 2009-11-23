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

class Cheetah(object):
    """Provides a compability layer between cheetah and django.
    """
    additional_meta = None
    additional_css = None
    additional_javascript = None
    additional_head = None

    def __init__(self, user, title, navpath):
        self.user = Account.objects.get(id=user['id'])
        self.title = title
        self.navpath = navpath
        
        preferences = user.get('preferences', {})
        self.navbar = preferences.get('navbar', [])
        self.qlink1 = preferences.get('qlink1', [])
        self.qlink2 = preferences.get('qlink2', [])

    def header(self):
        """Prints the django header template as a string.
        """
        return render_to_string(
            'compability/header.html',
            {
                'title': self.title,
                'navpath': self.navpath,
                'account': self.user,
                'navbar': self.navbar,
                'qlink1': self.qlink1,
                'qlink2': self.qlink2,
                'additional': {
                    'meta': self.additional_meta,
                    'css': self.additional_css,
                    'javascript': self.additional_javascript,
                    'head': self.additional_head,
                }
            }
        )

    def footer(self):
        """Prints the django footer template as a string.
        """
        return render_to_string(
            'compability/footer.html',
            {
                'account': self.user,
                'version': VERSION,
            }
        )

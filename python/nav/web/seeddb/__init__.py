# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 UNINETT AS
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

TITLE_DEFAULT = 'NAV - Seed Database'
NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

class SeeddbInfo(object):
    active = {'index': True}
    caption = 'Seed Database'
    tab_template = None

    _title = ''
    _navpath = []

    @property
    def title(self):
        sub_title = ''
        if self._title:
            sub_title = ' - %s' % self._title
        return TITLE_DEFAULT + sub_title

    @property
    def navpath(self):
        return NAVPATH_DEFAULT + self._navpath

    @property
    def template_context(self):
        return {
            'active': self.active,
            'title': self.title,
            'caption': self.caption,
            'navpath': self.navpath,
            'tab_template': self.tab_template,
        }

# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#


from nav.web.seeddb.constants import TITLE_DEFAULT, NAVPATH_DEFAULT


class SeeddbInfo(object):
    active = {'index': True}
    active_page = ''
    caption = 'Seed Database'
    verbose_name = ''
    tab_template = None

    _title = ''
    _navpath = []

    hide_move = False
    hide_delete = False
    hide_qr_code = True
    copy_url_name = None
    delete_url = None
    delete_url_name = None
    back_url = None
    add_url = None
    bulk_url = None
    documentation_url = None

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
            'active_page': self.active_page,
            'documentation_url': self.documentation_url,
            'title': self.title,
            'verbose_name': self.verbose_name,
            'caption': self.caption,
            'navpath': self.navpath,
            'tab_template': self.tab_template,
            'hide_move': self.hide_move,
            'hide_delete': self.hide_delete,
            'hide_qr_code': self.hide_qr_code,
            'delete_url': self.delete_url,
            'delete_url_name': self.delete_url_name,
            'back_url': self.back_url,
            'add_url': self.add_url,
            'bulk_url': self.bulk_url,
            'copy_url_name': self.copy_url_name,
        }

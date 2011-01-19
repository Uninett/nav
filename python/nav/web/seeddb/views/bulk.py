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

from nav.bulkimport import NetboxImporter
from nav.bulkparse import NetboxBulkParser

from nav.web.seeddb.utils.bulk import render_bulkimport

TITLE_DEFAULT = 'NAV - Seed Database'
NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def netbox_bulk(request):
    extra = {
        'active': {'netbox': True},
        'title': TITLE_DEFAULT + ' - IP Devices',
        'navpath': NAVPATH_DEFAULT + [('IP Devices', None)],
        'tab_template': 'seeddb/tabs_netbox.html',
    }
    return render_bulkimport(
            request, NetboxBulkParser, NetboxImporter,
            'seeddb-netbox',
            extra_context=extra)

def room_bulk(request):
    pass

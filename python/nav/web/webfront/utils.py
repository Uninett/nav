#
# Copyright (C) 2009, 2012 UNINETT AS
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

import os
from datetime import datetime

from django.db.models import Q

from nav.web import webfrontConfig
from nav.config import readConfig
from nav.models.msgmaint import Message
from nav.models.event import AlertHistory
from nav.models.manage import Netbox

def quick_read(filename):
    """Read and return the contents of a file, or None if something went wrong.
    """
    try:
        return file(filename).read().strip()
    except IOError:
        return None

def current_messages():
    """Finds current messages"""
    return Message.objects.filter(
        publish_start__lt=datetime.today().isoformat(' '),
        publish_end__gt=datetime.today().isoformat(' '),
        replaced_by__isnull=True
    )

def boxes_down():
    """Finds boxes that are down and not currently on maintenance"""
    infinity = datetime.max
    on_maintenance = Netbox.objects.filter(
        alerthistory__event_type='maintenanceState',
        alerthistory__end_time__gte=infinity,
    )
    boxes_down = AlertHistory.objects.select_related(
        'netbox'
    ).filter(
        Q(netbox__up=Netbox.UP_DOWN) | Q(netbox__up=Netbox.UP_SHADOW),
        end_time__gte=infinity,
        event_type='boxState'
    ).exclude(netbox__in=on_maintenance).order_by('-start_time')
    return boxes_down

def tool_list(account):
    def load_tool(filename):
        if filename[0] != os.sep:
            filename = os.path.join(os.getcwd(), filename)
        tool = readConfig(filename)
        if tool.has_key('priority'):
            tool['priority'] = int(tool['priority'])
        else:
            tool['priority'] = 0
        return tool

    def compare_tools(x, y):
        # Do a standard comparison of priority values (to accomplish an
        # ascendingg sort, we negate the priorities)
        ret = cmp(-x['priority'], -y['priority'])
        # If priorities were equal, sort by name instead
        if not ret:
            ret = cmp(x['name'].upper(), y['name'].upper())
        return ret

    paths = {}
    if webfrontConfig.has_option('toolbox', 'path'):
        paths = webfrontConfig.get('toolbox', 'path').split(os.pathsep)
    else:
        return None
    
    list = []
    for path in paths:
        if os.access(path, os.F_OK):
            filelist = os.listdir(path)
            for filename in filelist:
                if filename[-5:] == '.tool':
                    fullpath = os.path.join(path, filename)
                    tool = load_tool(fullpath)
                    if account.has_perm('web_access', tool['uri']):
                        list.append(tool)
    list.sort(compare_tools)
    return list

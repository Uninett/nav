"""Utility functions for various parts of the frontpage, navbar etc."""

#
# Copyright (C) 2009, 2012 Uninett AS
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
import io
import os
from datetime import datetime
import logging

from django.db.models import Q

from nav.config import get_config_locations
from nav.web import webfrontConfig
from nav.models.msgmaint import Message
from nav.models.event import AlertHistory
from nav.models.manage import Netbox
from nav.models.profiles import AccountTool

_logger = logging.getLogger('nav.web.tools.utils')


class Tool(object):
    """Class representing a tool"""

    def __init__(
        self, name, uri, icon, description, priority=0, display=True, doclink=None
    ):
        self.name = name
        self.uri = uri
        self.icon = icon
        self.description = description
        self.priority = int(priority)
        self.display = display
        self.doclink = doclink

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.priority < other.priority

    def __repr__(self):
        return "Tool('%s')" % self.name


def quick_read(filename):
    """Read and return the contents of a file, or None if something went wrong."""
    try:
        return open(filename).read().strip()
    except IOError:
        return None


def current_messages():
    """Finds current messages"""
    return Message.objects.filter(
        publish_start__lt=datetime.today().isoformat(' '),
        publish_end__gt=datetime.today().isoformat(' '),
        replaced_by__isnull=True,
    )


def boxes_down():
    """Finds boxes that are down and not currently on maintenance"""
    infinity = datetime.max
    on_maintenance = Netbox.objects.filter(
        alerthistory__event_type='maintenanceState',
        alerthistory__end_time__gte=infinity,
    )
    _boxes_down = (
        AlertHistory.objects.select_related('netbox')
        .filter(
            Q(netbox__up=Netbox.UP_DOWN) | Q(netbox__up=Netbox.UP_SHADOW),
            end_time__gte=infinity,
            event_type='boxState',
        )
        .exclude(netbox__in=on_maintenance)
        .order_by('-start_time')
    )
    return _boxes_down


def tool_list(account):
    """Get the list of tools existing in the tool directories"""

    def parse_tool(tool_file):
        """Parse the tool file and return a Tool object"""
        attrs = (
            line.split('=', 1)
            for line in io.open(tool_file, encoding='utf-8')
            if line.strip()
        )
        attrs = {key.strip(): value.strip() for key, value in attrs}
        return Tool(**attrs)

    paths = [str(path / 'toolbox') for path in get_config_locations()]
    if webfrontConfig.has_option('toolbox', 'path'):
        paths = webfrontConfig.get('toolbox', 'path').split(os.pathsep)

    _tool_list = []
    for path in paths:
        if os.access(path, os.F_OK):
            filelist = os.listdir(path)
            for filename in filelist:
                if filename[-5:] == '.tool':
                    fullpath = os.path.join(path, filename)
                    try:
                        tool = parse_tool(fullpath)
                    except Exception as error:  # noqa: BLE001
                        _logger.error('Error parsing tool in %s: %s', filename, error)
                        continue

                    if account.has_perm('web_access', tool.uri):
                        _tool_list.append(tool)
    _tool_list.sort()
    return _tool_list


def get_account_tools(account, all_tools):
    """Get tools for this account"""
    account_tools = account.account_tools.all()
    tools = []
    for tool in all_tools:
        try:
            account_tool = account_tools.get(toolname=tool.name)
        except AccountTool.DoesNotExist:
            tools.append(tool)
        else:
            tool.priority = account_tool.priority
            tool.display = account_tool.display
            tools.append(tool)
    return tools


def split_tools(tools, parts=3):
    """Split tools into even parts for megadropdown"""
    columns = []
    tools_in_column = len(tools) // parts
    remainder = len(tools) % parts
    first_index = 0
    for _column in range(parts):
        tools_in_this_column = tools_in_column
        if remainder:
            tools_in_this_column += 1
            remainder -= 1
        last_index = first_index + tools_in_this_column
        columns.append(tools[first_index:last_index])
        first_index += tools_in_this_column
    return columns

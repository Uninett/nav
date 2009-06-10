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

from datetime import datetime

from django.db.models import Q

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
    """Find boxes that are down and not on maintenance"""
    # FIXME We should ask for end_time='infinity', as infinity has a special
    # meaning in postgres. However, end_time__gt=datetime.max works as well
    # (for now).
    on_maintenance = AlertHistory.objects.filter(
        end_time__gt=datetime.max,
        event_type='maintenanceState',
    ).values('id').query
    boxes_down = AlertHistory.objects.select_related(
        'netbox'
    ).filter(
        ~Q(id__in=on_maintenance),
        Q(netbox__up=Netbox.UP_DOWN) | Q(netbox__up=Netbox.UP_SHADOW),
        end_time__gt=datetime.max,
        event_type='boxState'
    ).order_by('-start_time')
    return boxes_down

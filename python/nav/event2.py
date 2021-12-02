#
# Copyright (C) 2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Next generation event factory functionality for NAV, based on the Django ORM
models from nav.models.event.
"""
from __future__ import absolute_import

import six

from nav.models.event import EventQueue


class EventFactory(object):
    """A factory for NAV event dispatching"""

    def __init__(self, source, target, event_type, start_type=None, end_type=None):
        """
        Initialize a template for event generation.

        :param source: An event source string (e.g. 'ipdevpoll')
        :param target: An event target string (e.g. 'eventEngine')
        :param event_type: An event type name.
        :param start_type: An optional start alert type hint for eventengine
        :param end_type: An optional end alert type hint for eventengine
        """
        self.source = source
        self.target = target
        self.event_type = event_type
        self.start_type = start_type
        self.end_type = end_type

    def base(self, device=None, netbox=None, subid='', varmap=None, alert_type=None):
        """Creates and returns an event base template

        :param device: A nav.models.manage.Device object or primary key.
        :param netbox: A nav.models.manage.Netbox object or primary key.
        :param subid: A subid string, if applicable.
        :param varmap: A dictionary of arbitrary event variables to attach.
        :param alert_type: An option alert type hint for eventEngine; useful
                           for cases where eventEngine has no specific plugin.
        :return:
        """
        event = EventQueue()
        event.source_id = self.source
        event.target_id = self.target
        event.event_type_id = self.event_type

        if isinstance(device, int):
            event.device_id = device
        else:
            event.device = device

        if isinstance(netbox, int):
            event.netbox_id = netbox
        else:
            event.netbox = netbox

        event.subid = six.text_type(subid)

        var = dict(varmap or {})
        if alert_type:
            var['alerttype'] = alert_type
        event.varmap = var

        return event

    def start(self, device=None, netbox=None, subid='', varmap=None, alert_type=None):
        """Creates and returns a start event"""
        event = self.base(device, netbox, subid, varmap, alert_type or self.start_type)
        event.state = event.STATE_START
        return event

    def end(self, device=None, netbox=None, subid='', varmap=None, alert_type=None):
        """Creates and returns an end event"""
        event = self.base(device, netbox, subid, varmap, alert_type or self.end_type)
        event.state = event.STATE_END
        return event

    def notify(self, device=None, netbox=None, subid='', varmap=None, alert_type=None):
        """Creates and returns a stateless event"""
        event = self.base(device, netbox, subid, varmap, alert_type or self.start_type)
        event.event_type = event.STATE_STATELESS
        return event

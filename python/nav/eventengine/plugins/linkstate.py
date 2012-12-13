#
# Copyright (C) 2012 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
""""linkState event plugin"""

# TODO: FIX LP#1062136

from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins import delayedstate
from nav.models.manage import Interface

class LinkStateHandler(delayedstate.DelayedStateHandler):
    """Accepts linkState events"""
    HAS_WARNING_ALERT = False
    handled_types = ('linkState',)

    __waiting_for_resolve = {}
    _target = None

    def get_target(self):
        if not self._target:
            self._target = Interface.objects.get(id=self.event.subid)
            assert self._target.netbox_id == self.event.netbox.id
        return self._target

    def _make_up_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = "linkUp"
        return alert

    def _get_down_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = "linkDown"
        return alert

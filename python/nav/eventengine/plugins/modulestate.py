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
""""moduleState event plugin"""

from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins import delayedstate
from nav.models.manage import Module


class ModuleStateHandler(delayedstate.DelayedStateHandler):
    """Accepts moduleState events"""
    HAS_WARNING_ALERT = True
    handled_types = ('moduleState',)

    __waiting_for_resolve = {}
    _target = None

    def get_target(self):
        if not self._target:
            self._target = Module.objects.get(id=self.event.subid)
            assert self._target.netbox_id == self.event.netbox.id
        return self._target

    def _get_up_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = "moduleUp"

        module = self.get_target()
        module.up = module.UP_UP
        module.save()

        return alert

    def _register_internal_down_state(self):
        module = self.get_target()
        module.up = module.UP_DOWN
        module.save()

    def _get_down_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = "moduleDown"
        return alert

    def _post_down_warning(self):
        """Posts the actual warning alert"""
        alert = AlertGenerator(self.event)
        alert.alert_type = "moduleDownWarning"
        alert.state = self.event.STATE_STATELESS
        self._logger.info("%s: Posting %s alert",
                          self.get_target(), alert.alert_type)
        alert.post()

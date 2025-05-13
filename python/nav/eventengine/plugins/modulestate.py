#
# Copyright (C) 2012, 2014 Uninett AS
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
""" "moduleState event plugin"""

import datetime

from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins import delayedstate
from nav.models.manage import Module


class ModuleStateHandler(delayedstate.DelayedStateHandler):
    """Accepts moduleState events"""

    HAS_WARNING_ALERT = True
    WARNING_WAIT_TIME = 'moduleDown.warning'
    ALERT_WAIT_TIME = 'moduleDown.alert'
    handled_types = ('moduleState',)

    _target = None

    def get_target(self):
        if not self._target:
            self._target = Module.objects.get(id=self.event.subid)
            assert self._target.netbox_id == self.event.netbox.id
        return self._target

    def _is_internally_down(self):
        module = self.get_target()
        return module.up != module.UP_UP

    def _get_up_alert(self):
        alert = self._get_alert()
        alert.alert_type = "moduleUp"
        return alert

    def _set_internal_state_down(self):
        module = self.get_target()
        module.up = module.UP_DOWN
        module.down_since = datetime.datetime.now()
        module.save()

    def _set_internal_state_up(self):
        module = self.get_target()
        module.up = module.UP_UP
        module.down_since = None
        module.save()

    def _get_down_alert(self):
        if self._is_chassis_down():
            self._logger.info(
                "%s: Containing chassis is down, not posting moduleDown",
                self.get_target(),
            )
            return

        alert = self._get_alert()
        alert.alert_type = "moduleDown"
        return alert

    def _get_alert(self):
        alert = AlertGenerator(self.event)
        target = self.get_target()
        if target:
            alert['module'] = target
        return alert

    def _post_down_warning(self):
        """Posts the actual warning alert"""
        if self._is_chassis_down():
            self._logger.info(
                "%s: Containing chassis is down, not posting moduleDownWarning",
                self.get_target(),
            )
            return

        alert = self._get_alert()
        alert.alert_type = "moduleDownWarning"
        alert.state = self.event.STATE_STATELESS
        self._logger.info("%s: Posting %s alert", self.get_target(), alert.alert_type)
        alert.post()

    def _is_chassis_down(self):
        chassis = self.get_target().get_chassis()
        return chassis and chassis.gone_since

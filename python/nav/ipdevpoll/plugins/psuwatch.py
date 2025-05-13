#
# Copyright (C) 2019 Uninett AS
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
"""ipdevpoll plugin to monitor the state of known field-replaceable power supply and
fan units.

"""

import datetime

from twisted.internet import defer

from django.db import transaction

from nav.event2 import EventFactory
from nav.ipdevpoll import Plugin, db
from nav.models.manage import PowerSupplyOrFan

from .psu import get_mibretrievers_from_vendor_id


CALL_MAP = {"powerSupply": "get_power_supply_status", "fan": "get_fan_status"}
PSU_EVENT = EventFactory("ipdevpoll", "eventEngine", "psuState", "psuNotOK", "psuOK")
FAN_EVENT = EventFactory("ipdevpoll", "eventEngine", "fanState", "fanNotOK", "fanOK")
EVENT_MAP = {"powerSupply": PSU_EVENT, "fan": FAN_EVENT}

# Shorthand for database states
STATE_UNKNOWN = PowerSupplyOrFan.STATE_UNKNOWN
STATE_UP = PowerSupplyOrFan.STATE_UP
STATE_DOWN = PowerSupplyOrFan.STATE_DOWN
STATE_WARNING = PowerSupplyOrFan.STATE_WARNING


class PowerSupplyOrFanStateWatcher(Plugin):
    """Collects PSU and FAN statues from netboxes"""

    def __init__(self, *args, **kwargs):
        super(PowerSupplyOrFanStateWatcher, self).__init__(*args, **kwargs)
        self.vendor_id = (
            self.netbox.type.get_enterprise_id() if self.netbox.type else None
        )
        self.miblist = get_mibretrievers_from_vendor_id(self.vendor_id, self.agent)

    @defer.inlineCallbacks
    def handle(self):
        units = yield db.run_in_thread(self._get_database_unit_list)

        state_map = {}
        for unit in units:
            old_state = unit.up
            new_state = yield self._retrieve_current_unit_state(unit)
            state_map[unit] = new_state
            if old_state != new_state:
                yield self._handle_state_change(unit, new_state)

        return True

    @defer.inlineCallbacks
    def _retrieve_current_unit_state(self, unit):
        """
        :type unit: nav.models.manage.PowerSupplyOrFan
        """
        method_name = CALL_MAP.get(unit.physical_class)
        assert method_name is not None

        if unit.internal_id is not None:
            for mib in self.miblist:
                method = getattr(mib, method_name, None)
                if method:
                    state = yield method(unit.internal_id)
                    return state or STATE_UNKNOWN
        else:
            self._logger.debug("unit has no internal id: %r", unit)

        return STATE_UNKNOWN

    @defer.inlineCallbacks
    def _handle_state_change(self, unit, new_state):
        self._logger.info(
            "%s state changed from %s to %s", unit.name, unit.up, new_state
        )
        yield db.run_in_thread(self._update_internal_state, unit, new_state)
        yield db.run_in_thread(self._post_event, unit, new_state)

    #
    # Synchronous database access methods
    #

    def _get_database_unit_list(self):
        return list(PowerSupplyOrFan.objects.filter(netbox_id=self.netbox.id))

    @staticmethod
    def _update_internal_state(unit, new_state):
        old_state = unit.up

        if old_state in (STATE_UP, STATE_UNKNOWN) and new_state in (
            STATE_WARNING,
            STATE_DOWN,
        ):
            unit.downsince = datetime.datetime.now()
        elif old_state in (STATE_DOWN, STATE_WARNING) and new_state == STATE_UP:
            unit.downsince = None

        PowerSupplyOrFan.objects.filter(id=unit.id).update(
            up=new_state, downsince=unit.downsince
        )

    def _post_event(self, unit, new_state):
        factory = EVENT_MAP.get(unit.physical_class)
        assert factory is not None

        if new_state in (STATE_DOWN, STATE_WARNING):
            construct = factory.start
        else:
            construct = factory.end

        varmap = {
            "sysname": unit.netbox.sysname,
            "unitname": unit.name,
            "state": new_state,
        }
        event = construct(
            netbox=unit.netbox,
            device=unit.device if unit.device_id else None,
            subid=unit.id,
            varmap=varmap,
        )
        self._logger.debug("posting state change event for %s: %r", unit, event)
        with transaction.atomic():
            event.save()

#
# Copyright (C) 2023 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Juniper chassis/system alarms"""

from twisted.internet import defer

from nav.enterprise.ids import VENDOR_ID_JUNIPER_NETWORKS_INC
from nav.event2 import EventFactory
from nav.ipdevpoll import Plugin, db
from nav.mibs.juniper_alarm_mib import JuniperAlarmMib
from nav.models.manage import NetboxInfo

YELLOW_EVENT = EventFactory(
    source='ipdevpoll',
    target='eventEngine',
    event_type='juniperYellowAlarmState',
    start_type='juniperYellowAlarmOn',
    end_type='juniperYellowAlarmOff',
)
RED_EVENT = EventFactory(
    source='ipdevpoll',
    target='eventEngine',
    event_type='juniperRedAlarmState',
    start_type='juniperRedAlarmOn',
    end_type='juniperRedAlarmOff',
)

INFO_KEY_NAME = "juniperalarm"


class JuniperChassisAlarm(Plugin):
    """Retrieves the number of red and yellow alarms in a chassis

    This is done by attempting to retrieve the gauges in JUNIPER-ALARM-MIB:

    * jnxYellowAlarmCount
    * jnxRedAlarmCount

    If the count is not zero, a start event for that color is sent. When the
    count goes back to zero, an end-event is sent.

    """

    RESTRICT_TO_VENDORS = [VENDOR_ID_JUNIPER_NETWORKS_INC]

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("Collecting any juniper led alarms")

        mib = JuniperAlarmMib(self.agent)

        last_yellow_count = yield db.run_in_thread(self._get_last_count, "yellow_count")
        last_red_count = yield db.run_in_thread(self._get_last_count, "red_count")

        current_yellow_count = yield mib.get_yellow_alarm_count()
        current_red_count = yield mib.get_red_alarm_count()

        if last_yellow_count != current_yellow_count:
            if current_yellow_count:
                yield db.run_in_thread(
                    self._post_yellow_alarm_count_non_zero, current_yellow_count
                )
            else:
                yield db.run_in_thread(self._post_yellow_alarm_count_zero)

            yield db.run_in_thread(
                self._create_or_update_new_alarm_count,
                current_yellow_count,
                "yellow_count",
            )

        if last_red_count != current_red_count:
            if current_red_count:
                yield db.run_in_thread(
                    self._post_red_alarm_count_non_zero, current_red_count
                )
            else:
                yield db.run_in_thread(self._post_red_alarm_count_zero)

            yield db.run_in_thread(
                self._create_or_update_new_alarm_count,
                current_red_count,
                "red_count",
            )

    def _get_last_count(self, variable: str):
        count = getattr(
            NetboxInfo.objects.filter(netbox__id=self.netbox.id)
            .filter(key=INFO_KEY_NAME)
            .filter(variable=variable)
            .first(),
            "value",
            None,
        )
        if count != None and count.isdigit():
            return int(count)

    def _post_yellow_alarm_count_non_zero(self, count: int):
        YELLOW_EVENT.start(netbox=self.netbox.id, varmap={"count": count}).save()

    def _post_yellow_alarm_count_zero(self):
        YELLOW_EVENT.end(netbox=self.netbox.id).save()

    def _post_red_alarm_count_non_zero(self, count: int):
        RED_EVENT.start(netbox=self.netbox.id, varmap={"count": count}).save()

    def _post_red_alarm_count_zero(self):
        RED_EVENT.end(netbox=self.netbox.id).save()

    def _create_or_update_new_alarm_count(self, count: int, variable: str):
        object, _ = NetboxInfo.objects.get_or_create(
            netbox_id=self.netbox.id,
            key=INFO_KEY_NAME,
            variable=variable,
        )
        object.value = count
        object.save()

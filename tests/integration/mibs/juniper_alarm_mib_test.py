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
import pytest
import pytest_twisted

from nav.mibs.juniper_alarm_mib import JuniperAlarmMib


class TestJuniperAlarmMib:
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_get_alarm_count_should_get_the_correct_red_and_yellow_alarm_counts(
        self, snmp_agent_proxy
    ):
        snmp_agent_proxy.community = 'juniper-alarm'
        snmp_agent_proxy.open()
        mib = JuniperAlarmMib(snmp_agent_proxy)

        yellow_alarm_count = yield mib.get_yellow_alarm_count()
        red_alarm_count = yield mib.get_red_alarm_count()

        assert yellow_alarm_count == 0
        assert red_alarm_count == 2

    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_get_alarm_count_should_get_the_correct_red_and_yellow_alarm_counts_for_result_None(  # noqa: E501
        self, snmp_agent_proxy
    ):
        snmp_agent_proxy.community = 'juniper-alarm-none'
        snmp_agent_proxy.open()
        mib = JuniperAlarmMib(snmp_agent_proxy)

        yellow_alarm_count = yield mib.get_yellow_alarm_count()
        red_alarm_count = yield mib.get_red_alarm_count()

        assert yellow_alarm_count == 0
        assert red_alarm_count == 0

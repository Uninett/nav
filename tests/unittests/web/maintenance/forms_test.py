#
# Copyright (C) 2022 Sikt
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
from datetime import date

import pytest

from nav.web.maintenance.forms import MaintenanceCalendarForm


class TestMaintenanceCalendarForm:
    def test_cleaned_year_returns_integer(self, valid_form):
        assert valid_form.cleaned_year == 2022

    def test_cleaned_month_returns_integer(self, valid_form):
        assert valid_form.cleaned_month == 7

    def test_this_month_start_returns_the_first_day_of_the_month(self, valid_form):
        assert valid_form.this_month_start == date(2022, 7, 1)

    def test_next_month_start_returns_the_first_day_of_the_next_month(self, valid_form):
        assert valid_form.next_month_start == date(2022, 8, 1)

    def test_previous_month_start_returns_the_first_day_of_the_previous_month(
        self, valid_form
    ):
        assert valid_form.previous_month_start == date(2022, 6, 1)

    def test_when_month_is_december_next_month_start_returns_january(
        self, december_form
    ):
        assert december_form.next_month_start == date(2023, 1, 1)

    def test_when_month_is_january_previous_month_start_returns_december(
        self, january_form
    ):
        assert january_form.previous_month_start == date(2021, 12, 1)


@pytest.fixture
def valid_form() -> MaintenanceCalendarForm:
    return MaintenanceCalendarForm(data={'year': '2022', 'month': '7'})


@pytest.fixture
def december_form() -> MaintenanceCalendarForm:
    return MaintenanceCalendarForm(data={'year': '2022', 'month': '12'})


@pytest.fixture
def january_form() -> MaintenanceCalendarForm:
    return MaintenanceCalendarForm(data={'year': '2022', 'month': '1'})

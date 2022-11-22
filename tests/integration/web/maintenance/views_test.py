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


class TestMaintenanceCalendarView:
    def test_calendar_renders_when_no_arguments_given(self, client):
        response = client.get('/maintenance/', follow=True)
        assert response.status_code == 200

    def test_calendar_still_renders_when_invalid_arguments_given(self, client):
        response = client.get('/maintenance/?year=invalid&month=invalid', follow=True)
        assert response.status_code == 200

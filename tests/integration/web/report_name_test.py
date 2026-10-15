#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Tests for how the report views handle untrusted report names"""

import pytest
from django.urls import reverse


@pytest.mark.parametrize("view_name", ["report-by-name", "widget-report-by-name"])
def test_when_report_name_has_invalid_regex_syntax_then_report_view_should_return_404(
    client, view_name
):
    response = client.get(reverse(view_name, kwargs={"report_name": "("}))

    assert response.status_code == 404

#
# Copyright (C) 2025 Sikt
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
from django.core.management import call_command
from django.test import override_settings


def test_collectstatic_should_succeed(tmp_path):
    """Verify collectstatic works with NAV's staticfiles configuration."""
    with override_settings(STATIC_ROOT=str(tmp_path)):
        call_command('collectstatic', '--noinput', verbosity=0)
    collected = list(tmp_path.rglob('*'))
    assert any(f.is_file() for f in collected), "No files were collected"

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
"""Unit tests for the access session shadow helpers"""

import re

from django.test import override_settings

from nav.ipdevpoll.shadows.access_session import make_session_key

SESSION_ID = b"\x0a\x0b\x0c\x0d\x00\x00\x00\x12\x34\x56\xab\xcd"


class TestMakeSessionKey:
    def test_when_called_twice_with_same_id_then_it_should_return_same_key(self):
        assert make_session_key(SESSION_ID) == make_session_key(SESSION_ID)

    def test_when_ids_differ_then_it_should_return_different_keys(self):
        assert make_session_key(SESSION_ID) != make_session_key(SESSION_ID + b"0")

    def test_when_secret_key_differs_then_it_should_return_different_key(self):
        with override_settings(SECRET_KEY="one secret"):
            first = make_session_key(SESSION_ID)
        with override_settings(SECRET_KEY="another secret"):
            second = make_session_key(SESSION_ID)

        assert first != second

    def test_when_called_then_it_should_return_a_sha256_hexdigest(self):
        assert re.fullmatch("[0-9a-f]{64}", make_session_key(SESSION_ID))

    def test_when_called_then_it_should_not_contain_the_raw_id_in_hex(self):
        assert SESSION_ID.hex() not in make_session_key(SESSION_ID)

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
"""Unit tests for the CISCO-AUTH-FRAMEWORK-MIB retriever"""

from unittest.mock import Mock

import pytest
from twisted.internet import defer

from nav.mibs.cisco_auth_framework_mib import (
    IDENTITY_COLUMNS,
    CiscoAuthFrameworkMib,
)
from nav.mibs.mibretriever import MibTableResultRow
from nav.oids import OID

SESSION_ID = b"\x0a\x00\x00\x01\xab"
IFINDEX = 10101


class TestGetSessions:
    @pytest.mark.twisted
    async def test_when_index_has_implied_session_id_then_it_should_decode_it(self):
        mib = _mib_returning_columns({"cafSessionStatus": 6})

        sessions = await mib.get_sessions()

        assert list(sessions) == [(IFINDEX, SESSION_ID)]

    @pytest.mark.twisted
    async def test_when_values_are_enumerated_then_it_should_translate_them(self):
        mib = _mib_returning_columns(
            {"cafSessionStatus": 6, "cafSessionDomain": 3, "cafSessionAuthVlan": 330}
        )

        sessions = await mib.get_sessions()

        assert sessions[(IFINDEX, SESSION_ID)] == {
            "cafSessionStatus": "authorizationSuccess",
            "cafSessionDomain": "voice",
            "cafSessionAuthVlan": 330,
        }

    @pytest.mark.twisted
    async def test_when_identity_is_not_included_then_it_should_not_request_it(self):
        mib = _mib_returning_columns({"cafSessionStatus": 6})

        await mib.get_sessions()

        requested = mib.retrieve_columns.call_args.args[0]
        assert not set(IDENTITY_COLUMNS) & set(requested)

    @pytest.mark.twisted
    async def test_when_identity_is_included_then_it_should_request_it(self):
        mib = _mib_returning_columns({"cafSessionStatus": 6})

        await mib.get_sessions(include_identity=True)

        requested = mib.retrieve_columns.call_args.args[0]
        assert set(IDENTITY_COLUMNS) <= set(requested)

    @pytest.mark.twisted
    @pytest.mark.parametrize("bad_index", [(IFINDEX,), (IFINDEX, 300, 1)])
    async def test_when_an_index_is_malformed_then_it_should_skip_only_that_row(
        self, bad_index
    ):
        mib = _mib_returning_columns(
            {"cafSessionStatus": 6}, extra_indexes=[OID(bad_index)]
        )

        sessions = await mib.get_sessions()

        assert list(sessions) == [(IFINDEX, SESSION_ID)]


class TestGetSessionMethods:
    @pytest.mark.twisted
    async def test_when_index_has_length_prefixed_session_id_then_it_should_decode_it(
        self,
    ):
        mib = _mib_returning_method_states({2: 5, 3: 4})

        methods = await mib.get_session_methods()

        assert methods == {
            (IFINDEX, SESSION_ID): {
                "dot1x": "authcFailed",
                "macAuthBypass": "authcSuccess",
            }
        }

    @pytest.mark.twisted
    @pytest.mark.parametrize(
        "bad_index",
        [(IFINDEX, 9, 1, 2), (IFINDEX, 1, 300, 2), (IFINDEX,)],
    )
    async def test_when_an_index_is_malformed_then_it_should_skip_only_that_row(
        self, bad_index
    ):
        mib = _mib_returning_method_states({2: 4}, extra_indexes=[OID(bad_index)])

        methods = await mib.get_session_methods()

        assert methods == {(IFINDEX, SESSION_ID): {"dot1x": "authcSuccess"}}


def _mib_returning_columns(values, extra_indexes=()):
    mib = CiscoAuthFrameworkMib(Mock())
    result = {}
    for index in [OID((IFINDEX, *SESSION_ID)), *extra_indexes]:
        result[index] = MibTableResultRow(index)
        result[index].update(values)
    mib.retrieve_columns = Mock(return_value=defer.succeed(result))
    return mib


def _mib_returning_method_states(states_by_method, extra_indexes=()):
    mib = CiscoAuthFrameworkMib(Mock())
    prefix = (IFINDEX, len(SESSION_ID), *SESSION_ID)
    result = {
        OID(prefix + (method,)): state for method, state in states_by_method.items()
    }
    result.update((index, 4) for index in extra_indexes)
    mib.retrieve_column = Mock(return_value=defer.succeed(result))
    return mib

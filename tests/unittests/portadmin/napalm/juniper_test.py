#
# Copyright (C) 2022 Sikt AS
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

from jnpr.junos.exception import RpcError

from nav.portadmin.handlers import ProtocolError
from nav.portadmin.napalm.juniper import wrap_unhandled_rpc_errors


class TestWrapUnhandledRpcErrors:
    def test_rpcerrors_should_become_protocolerrors(self):
        @wrap_unhandled_rpc_errors
        def wrapped_function():
            raise RpcError("bogus")

        with pytest.raises(ProtocolError):
            wrapped_function()

    def test_non_rpcerrors_should_pass_through(self):
        @wrap_unhandled_rpc_errors
        def wrapped_function():
            raise TypeError("bogus")

        with pytest.raises(TypeError):
            wrapped_function()

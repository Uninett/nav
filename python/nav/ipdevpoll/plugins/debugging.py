#
# Copyright (C) 2017 Uninett AS
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
"""ipdevpoll plugins to test error handling and scheduling in ipdevpoll

Example config:
[plugins]
crash=nav.ipdevpoll.plugins.debugging.Crash
error=nav.ipdevpoll.plugins.debugging.Error
fail=nav.ipdevpoll.plugins.debugging.Fail
sleep=nav.ipdevpoll.plugins.debugging.Sleep
noop=nav.ipdevpoll.plugins.debugging.Noop

[job_debug]
interval: 30
description: Testing testing
plugins: sleep

[job_stress]
interval: 1
description: Stress the scheduler
plugins: noop

[job_stress2]
interval: 2
description: Stress the scheduler
plugins: noop

[job_stress5]
interval: 5
description: Stress the scheduler
plugins: noop
"""

from twisted.internet import defer, reactor

from nav.ipdevpoll import Plugin


class Crash(Plugin):
    "This plugin crashes when invoked"

    def handle(self):
        raise RuntimeError("crash")


class Error(Plugin):
    "This plugin allways triggers it's deferred's errback"

    def handle(self):
        deferred = defer.Deferred()
        reactor.callLater(0, self.error, deferred)
        return deferred

    def error(self, deferred):
        try:
            raise RuntimeError()
        except Exception:  # noqa: BLE001
            deferred.errback()


class Fail(Plugin):
    "This plugin allways returns a failed state"

    def handle(self):
        deferred = defer.Deferred()
        reactor.callLater(0, deferred.callback, False)
        return deferred


class Sleep(Plugin):
    "This plugin succeeds, but very slowly"

    def handle(self):
        deferred = defer.Deferred()
        reactor.callLater(300, deferred.callback, True)
        return deferred


class Noop(Plugin):
    "This plugin allways returns a failed state"

    def handle(self):
        deferred = defer.Deferred()
        reactor.callLater(0, deferred.callback, True)
        return deferred

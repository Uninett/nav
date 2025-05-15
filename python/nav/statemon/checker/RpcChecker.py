#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""RPC portmapper service checker"""

import os
import subprocess
from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event
from nav.util import which


class RpcChecker(AbstractChecker):
    """RPC portmapper"""

    DESCRIPTION = "RPC portmapper"
    OPTARGS = (
        (
            'required',
            'A comma separated list of require services. Example: nfs,nlockmgr',
        ),
    )

    def __init__(self, service, **kwargs):
        """This handler doesn't obey the port argument"""
        AbstractChecker.__init__(self, service, port=111, **kwargs)

    def execute(self):
        # map service to t=tcp or u=udp
        mapper = {
            'nfs': 't',
            'status': 't',
            'nlockmgr': 'u',
            'mountd': 't',
            'ypserv': 'u',
            'ypbind': 'u',
        }
        default = ['nfs', 'nlockmgr', 'mountd', 'status']
        required = self.args.get('required', '')
        if not required:
            required = default
        else:
            required = required.split(',')

        cmd = 'rpcinfo'
        cmdpath = which(cmd)
        if not cmdpath:
            return (
                Event.DOWN,
                'Command %s not found in %s' % (cmd, os.environ['PATH']),
            )

        ip, _port = self.get_address()
        for service in required:
            protocol = mapper.get(service, '')
            if not protocol:
                return (
                    Event.DOWN,
                    "Unknown argument: [%s], can only check "
                    "%s" % (service, str(mapper.keys())),
                )

            try:
                proc = subprocess.Popen(
                    [cmdpath, '-' + protocol, ip, service],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                proc.wait()
            except OSError as msg:
                return Event.DOWN, 'could not run rpcinfo: %s' % msg

            output = proc.stdout.read()
            if 'ready' in output:
                continue
            if 'not available' in output:
                return Event.DOWN, '%s not available' % service
            if not output:
                return Event.DOWN, 'rpcinfo timed out'

        return Event.UP, "Ok"

# -*- coding: utf-8 -*-
#
# Copyright (C) 2003,2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import os
import re
import subprocess
from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
from nav.util import which

pattern = re.compile(r'domain=\[[^\]]+\] os=\[([^\]]+)\] server=\[([^\]]+)\]',
                     re.I)


class SmbChecker(AbstractChecker):
    """
    args:
            'hostname'
        'username'
        'password'
        'port'
    """
    TYPENAME = "smb"
    IPV6_SUPPORT = True
    DESCRIPTION = "Windows file sharing"
    OPTARGS = (
        ('hostname', ''),
        ('username', ''),
        ('password', ''),
        ('workgroup', ''),
        ('port', ''),
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=139, **kwargs)

    def execute(self):
        ip, port = self.getAddress()
        args = self.getArgs()
        host = args.get('hostname', ip)
        username = args.get('username','')
        password = args.get('password','')
        workgroup = args.get('workgroup', '')

        cmd = 'smbclient'
        cmdpath = which(cmd)
        if not cmdpath:
            return Event.DOWN, 'Command %s not found in %s' % (cmd, os.environ['PATH'])

        args = [cmdpath,
                '-L', host,
                '-p', str(port)]

        if password and username:
            args += ['-U', username+'%'+password]
            if workgroup:
                args += ['-W', workgroup]
        else:
            args += ['-N']

        try:
            p = subprocess.Popen(args,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            p.wait()
        except IOError, msg:
            return Event.DOWN, 'could not run smbclient: %s' % msg

        output = p.stdout.read()
        errput = p.stderr.read()

        match = pattern.search(output) or pattern.search(errput)
        if match:
            version = ' '.join(match.groups())
            self.setVersion(version)
            return Event.UP, 'OK'
        else:
            return Event.DOWN, 'error %s' % output.strip().split('\n')[-1]

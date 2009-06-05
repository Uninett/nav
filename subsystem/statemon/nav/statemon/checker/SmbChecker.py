# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# $Id$
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

import re
import subprocess
from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event

pattern = re.compile(r'domain=\[[^\]]+\] os=\[([^\]]+)\] server=\[([^\]]+)\]',re.I) #tihihi


class SmbChecker(AbstractChecker):
    """
    args:
            'hostname'
        'username'
        'password'
        'port'
    """
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "smb", service, port=139, **kwargs)
    def execute(self):
        ip,port = self.getAddress()
        args = self.getArgs()
        host = args.get('hostname',ip)
        username = args.get('username','')
        password = args.get('password','')
        workgroup = args.get('workgroup', '')

        args = ['smbclient',
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
        except IOEerror, msg:
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

def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = []
    return requiredArgs


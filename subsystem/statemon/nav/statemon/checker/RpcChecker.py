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
import subprocess
from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
class RpcChecker(AbstractChecker):
    """
    args:
    requried
    ex: nfs,nlockmgr
    """
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "rpc", service,port=111, **kwargs)
        # This handler doesn't obey port argument
    def execute(self):
        args = self.getArgs()
        # map service to t=tcp or u=udp
        mapper = {'nfs':'t',
              'status':'t',
              'nlockmgr':'u',
              'mountd':'t',
              'ypserv':'u',
              'nfs':'u',
              'ypbind':'u'
              }
        default = ['nfs', 'nlockmgr', 'mountd', 'status']
        required = args.get('required','')
        if not required:
            required = default
        else:
            required = required.split(',')

        ip, port = self.getAddress()
        for service in required:
            protocol = mapper.get(service, '')
            if not protocol:
                return Event.DOWN, "Unknown argument: [%s], can only check %s" % (service, str(mapper.keys()))

            try:
                p = subprocess.Popen(['rpcinfo',
                                      '-'+protocol,
                                      ip,
                                      service],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                p.wait()
            except OSError, msg:
                return Event.DOWN, 'cound not run rpcinfo: %s' % msg

            output = p.stdout.read()
            if 'ready' in output:
                continue
            if 'not available' in output:
                return Event.DOWN, '%s not available' % service
            if not output:
                return Event.DOWN, 'rpcinfo timed out'

        return Event.UP, "Ok"

def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = ['required']
    return requiredArgs


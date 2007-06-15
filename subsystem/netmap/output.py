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


def returnSimpleXML(data = None):
    ret = ""
    for box in data.values():
        ret += """
<netpoint>
    <netboxid>%s</netboxid>
    <sysname>%s</sysname>
    <ip>%s</ip>
    <category>%s</category>
    <cpuload>%d</cpuload>
    <room>%s</room>
    <location>%s</location>
    <up>%s</up>
    <uptime>%s</uptime>
    <connected_to>
        """ % (box.netboxid, box.sysname, box.ip, box.catid, -1.0, box.roomid,"Unknown", box.up, box.uptime)
        for module in box.modules.values():
            for port in module.gwports.values():
                if port.connected_to:
                    ret += """
        <link>
            <netboxid>%s</netboxid>
            <capacity>-1</capacity>
            <traffic>
                <in>-1</in>
                <out>-1</out>
            </traffic>
            <type>unknown</type>
        </link>
                    """ % port.connected_to
        ret += """
    </connected_to>
</netpoint>
        """
    return ret

#!/usr/bin/env python
# -*- coding: ISO8859-1 -*-
# Copyright 2004 Norwegian University of Science and Technology
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
# Authors: Kristian Eide <kreide@online.no>
#
"""
Fetch RRD data (used by vPServer)
"""

import rrdtool
from sys import stdin
import os.path

cr = stdin.readline().strip()
time = stdin.readline().strip().split(",")
for line in stdin:
    if len(line.strip()) == 0: continue
    t = line.split()
    if os.path.isfile(t[0]):
        if (len(t) == 2):
            r = rrdtool.graph('-','-s '+time[0]+':'+time[1],'DEF:value='+t[0]+':'+t[1]+':AVERAGE','PRINT:value:'+cr+':%6.2lf')
            print r[2][0].strip()
        elif (len(t) == 3):
            r = rrdtool.graph('-','-s '+time[0]+':'+time[1],'DEF:value1='+t[0]+':'+t[1]+':AVERAGE','DEF:value2='+t[0]+':'+t[2]+':AVERAGE','PRINT:value1:'+cr+':%6.2lf','PRINT:value2:'+cr+':%6.2lf')
            print r[2][0].strip() + ' ' + r[2][1].strip()
    else:
        print 'fnf'

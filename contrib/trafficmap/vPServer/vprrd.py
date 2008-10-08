#!/usr/bin/env python
# -*- coding: ISO8859-1 -*-
# Copyright 2004 Norwegian University of Science and Technology
# Copyright 2006 UNINETT AS
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
#          Morten Brekkevold <morten.brekkevold@uninett.no>
#
"""Helper program to allow vPServer to fetch RRD data.

vPServer establishes communication with this program through a pipe.
"""

import rrdtool
from sys import stdin
import os.path
import shlex

doWarp = True # Should we perform timewarping?
timewarp = 60 # Seconds

def rrdvalues(start, stop, rrdfile, datasources, consolidation):
    """Extract values from RRD files and return as a list."""
    defs = [ 'DEF:value' + str(ds[0]) + '=' + rrdfile + ':' + ds[1] +
             ':AVERAGE'
             for ds in enumerate(datasources) ]
    prints = [ 'PRINT:value' + str(ds[0]) + ':' + consolidation + ':%6.2lf'
               for ds in enumerate(datasources) ]

    result = rrdtool.graph('-', '-s ' + str(start) + ':' + str(stop),
                           *(defs+prints))
    return [v.strip() for v in result[2]]

consolidation = stdin.readline().strip()
time = stdin.readline().strip().split(",")
start = long(time[0])
stop = long(time[1])

for line in stdin:
    if len(line.strip()) == 0: continue
    t = shlex.split(line)
    rrdfile = t[0]
    dss = t[1:]
    
    if os.path.isfile(rrdfile):
        values = rrdvalues(start, stop, rrdfile, dss, consolidation)
        if doWarp and stop == 0:
            if "nan" in [v.lower() for v in values]:
                # The RRD file's last data point might not have been inserted
                # yet, so we look `timewarp` seconds further back in time in a
                # desperate attempt to avoid so-called "black load" on the
                # traffic map.
                values = rrdvalues(start-timewarp, stop-timewarp, rrdfile,
                                   dss, consolidation)
        print " ".join(values)
    else:
        print 'fnf'

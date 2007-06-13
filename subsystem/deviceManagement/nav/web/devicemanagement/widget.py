# -*- coding: UTF-8 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2007 UNINETT AS
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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#
"""
Widget class of Device Management
"""

### Imports

import mx.DateTime

### Classes

class Widget:
    MONTHS = ['January','February','March','April','May','June','July',
              'August','September','October','November','December']

    # Widget 'struct' for the template
    def __init__(self,controlname,type,name=None,value=None,options=None,
                 required=False):
        self.controlname = controlname
        self.type = type
        self.name = name
        if options is None: options = {}
        self.options = options
        self.required = required
        self.value = value

        if type == 'date':
            # date widget
            self.valueY = self.value[0]
            self.valueM = self.value[1]
            self.valueD = self.value[2]
            now = mx.DateTime.now()
            if options.has_key('startyear'):
                startYear = options['startyear']
            else:
                startYear = now.year - 1
            if options.has_key('endyear'):
                endYear = options['endyear']
            else:
                endYear = now.year
            if options.has_key('setdate'):
                setdate = options['setdate']
            else:
                setdate = mx.DateTime.now()

            monthOptions = []
            for i, month in enumerate(self.MONTHS):
                i += 1
                thisMonth = False
                if self.valueM:
                    if self.valueM == str(i):
                        thisMonth = True
                else:
                   if setdate.month == i:
                       thisMonth = True
                monthOptions.append((str(i),month,thisMonth))

            dayOptions = []
            for d in range(1,32):
                thisDay = False
                if self.valueD:
                    if self.valueD == str(d):
                        thisDay = True
                else:
                    if d == setdate.day:
                        thisDay = True
                dayOptions.append((str(d),str(d),thisDay))

            yearOptions = []
            for y in range(startYear,endYear+1):
                thisYear = False
                if self.valueY:
                    if self.valueY == str(y):
                        thisYear = True
                else:
                    if y == setdate.year:
                        thisYear = True
                yearOptions.append((str(y),str(y),thisYear))

            self.options['months'] = monthOptions
            self.options['days'] = dayOptions
            self.options['years'] = yearOptions

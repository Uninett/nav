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
FormattedList class for Device Management
"""

### Imports

import mx.DateTime
import re

from nav.web.devicemanagement.common import *

### Classes

class FormattedList:
    def __init__(self,name,title,headings,colformat,sql,limit=None,offset=None):
        self.title = title
        self.headings = headings
        self.rows = []

        result = executeSQL(sql,fetch=True)
        # Regexp matching $1i$,$2$,...
        regexp = re.compile("\$(\d+)\$")

        for resultrow in result:
            testDate = mx.DateTime.now()
            tmprow = list(resultrow)
            resultrow = []
            for data in tmprow:
                ## UGLY!
                if type(data) == type(testDate):
                    data = data.strftime(DATEFORMAT)
                elif not type(data) is str:
                    data = str(data)
                elif not data:
                    data = ''
                resultrow.append(data)
            row = []
            for formatstring in colformat:
                column = []
                for part in formatstring:
                    if type(part) is list:
                        # This part of the formatstring is on the format
                        # [string:type,string:data] where string:type can
                        # be 'url','image','widget'
                        partType = part[0]
                        tempcol = []
                        tempcol.append(partType)
                        if partType == 'widget':
                            # Format the value of the widget
                            # Make a copy of the general widget
                            widget = newWidget(part[1])
                            col = widget.value
                            while regexp.search(col):
                                match = regexp.search(col).groups()[0]
                                col = col.replace('$' + match + '$',
                                                  resultrow[int(match)])
                            widget.value = col
                            tempcol.append(widget)
                            column.append(tempcol)
                        else:
                            for i in range(1,len(part)):
                                col = part[i]
                                while regexp.search(col):
                                    match = regexp.search(col).groups()[0]
                                    col = col.replace('$' + match + '$',
                                                      resultrow[int(match)])
                                tempcol.append(col)
                            column.append(tempcol)
                    elif type(part) is str:
                        col = part
                        while regexp.search(col):
                            match = regexp.search(col).groups()[0]
                            col = col.replace('$' + match + '$',
                                              resultrow[int(match)])
                        column.append(col)
                row.append(column)
            self.rows.append(row)

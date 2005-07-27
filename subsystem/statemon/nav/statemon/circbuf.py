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
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Stian Soiland   <stain@itea.ntnu.no>
#

"""Circular buffer. 
The buffer holds n items. When the the buffer is full and a new item is
added, the first item is removed.
"""

class CircBuf:
  def __init__(self, size=10, *args, **kwargs):
      self._size = size
      self._data = [None]*self._size

  def push(self, value):
      self._data.pop()
      self._data.insert(0,value)

  def __len__(self):
      return self._size
  def __getslice__(self, i, j):
      return self._data[i:j]

  def __getitem__(self, i):
      return self._data[i]
          
          
          
    

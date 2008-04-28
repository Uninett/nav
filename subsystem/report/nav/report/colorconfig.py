# -*- coding: utf-8 -*-
# $Id:$
#
# Copyright 2007-2008 UNINETT AS
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
# Authors: Jostein Gogstad <jostein.gogstad@idi.ntnu.no>
#          Jørgen Abrahamsen <jorgen.abrahamsen@uninett.no>
#

# FIXME: Comment on what this class does and perhaps why.


from re import search

class ColorConfig:

	def __init__(self,path):
		config = file(path).readlines()
		limits = {}
		extras = {}
		for line in config:
			limitmatch = search("^\s*\>\=?\s*(\d+)\s*:\s*(\S+)",line)
			if limitmatch:
				limits[limitmatch.group(1)] = limitmatch.group(2)
			else:
				wordmatch = search("^\s*(\w+)\s*:\s*(\S+)",line)
				if wordmatch:
					extras[wordmatch.group(1)] = wordmatch.group(2)

		self.extras = extras
		self.limits = limits

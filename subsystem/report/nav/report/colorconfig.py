# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Sets options according to configuration file."""

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

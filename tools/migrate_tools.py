#!/usr/bin/env python
#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Tool for migrating tools from files to database"""

import sys
from os import listdir
from os.path import isfile, join
from nav.models.profiles import Tool


def main(path):
    """Main controller"""
    files = [f for f in listdir(path)
             if isfile(join(path, f)) and f.endswith('.tool')]
    for toolfile in files:
        parse(open(join(path, toolfile)))


def parse(toolfile):
    """Parse toolfile and insert into database"""
    kwargs = dict(line.strip().split('=') for line in toolfile.readlines()
                  if line.count('='))
    if Tool.objects.filter(name=kwargs['name']).exists():
        print "%s seems to exist - skipping" % kwargs['name']
        return
    Tool(**kwargs).save()

if __name__ == '__main__':
    _toolpath = "/usr/local/nav/etc/toolbox"
    if len(sys.argv) > 1:
        _toolpath = sys.argv[1]
    main(_toolpath)

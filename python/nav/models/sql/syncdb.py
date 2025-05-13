#!/usr/bin/env python
"""
This helper script is here for backwards compatibility; it lets the the
current development schema be installed from anywhere within the NAV source
code tree.
"""

import sys
import os

_mydir = os.path.dirname(sys.argv[0])
_top_srcdir = os.path.abspath(os.path.join(_mydir, '..'))
sys.path.insert(0, os.path.join(_top_srcdir, 'python'))
os.chdir(_mydir)

from nav.pgsync import main

main()

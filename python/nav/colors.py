#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Simple tools for terminal color support"""
import sys
from functools import wraps
import curses
from curses import (COLOR_BLACK, COLOR_BLUE, COLOR_CYAN, COLOR_GREEN,
                    COLOR_MAGENTA, COLOR_RED, COLOR_WHITE, COLOR_YELLOW)

__all__ = ['COLOR_BLACK', 'COLOR_BLUE', 'COLOR_CYAN', 'COLOR_GREEN',
           'COLOR_MAGENTA', 'COLOR_RED', 'COLOR_WHITE', 'COLOR_YELLOW',
           'colorize', 'set_foreground', 'reset_foreground', 'print_color']

try:
    curses.setupterm()
    _set_color = curses.tigetstr('setaf') or ''
    _reset_color = curses.tigetstr('sgr0') or ''
except curses.error:
    # silently ignore errors and turn off colors
    _set_color = ''
    _reset_color = ''


def colorize(color):
    """Decorator that changes the foreground color of any terminal output from
    a function, provided that the current terminal supports it.

    Example::

    @colorize(COLOR_YELLOW):
    def hello_world():
        print "Hello world!"

    """
    def _colorize(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            try:
                set_foreground(color)
                return func(*args, **kwargs)
            finally:
                reset_foreground()
        return _wrapper
    return _colorize


def print_color(string, color, newline=True):
    """Prints a string to stdout using a specific color"""
    set_foreground(color)
    sys.stdout.write(string + ('\n' if newline else ''))
    reset_foreground()


def set_foreground(color):
    """Sets the current foreground color of the terminal"""
    if sys.stdout.isatty():
        sys.stdout.write(curses.tparm(_set_color, color))
        sys.stdout.flush()


def reset_foreground():
    """Resets the foreground color of the terminal"""
    if sys.stdout.isatty():
        sys.stdout.write(_reset_color)
        sys.stdout.flush()

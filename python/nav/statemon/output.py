import os, sys, commands, string
try:
    import termios
except ImportError:
    import TERMIOS
    termios = TERMIOS
from types import *

enable_color = 1

def progress(ratio, length=40, col=1, cols=("yellow", None, "cyan"),
            nocol="=."):
    """Text mode progress bar.

    ratio   - current position / total (e.g. 0.6 is 60%)
    length  - bar size
    col     - color bar
    cols    - tuple: (elapsed, left, percentage num)
    nocol   - string, if default="=.", bar is [=======.....]
    """

    # TODO: percent display in the middle of the bar
    if ratio > 1:
        ratio = 1
    elchar, leftchar = nocol
    elapsed = int(round(ratio*length))
    left = length - elapsed
    bar = elchar*elapsed + leftchar*left
    bar = bar[:length]
    if col:
        c_elapsed, c_left, perc = cols
        bar = color(' '*elapsed, "gray", c_elapsed)
        bar = bar + color(' '*left, "gray", c_left)
    else:
        bar = elchar*elapsed + leftchar*left
    return bar

def color(text, fg, bg=None):
    """Return colored text.

    Uses terminal color codes; set avk_util.enable_color to 0 to
    return plain un-colored text. If fg is a tuple, it's assumed to
    be (fg, bg).
    """

    if type(fg) == TupleType:
        fg, bg = fg
    xterm = 0
    if os.environ["TERM"] == "xterm": 
        xterm = 1
    if enable_color:
        col_dict = {
            "black"     :   "30m",
            "red"       :   "31m",
            "green"     :   "32m",
            "brown"     :   "33m",
            "blue"      :   "34m",
            "purple"    :   "35m",
            "cyan"      :   "36m",
            "lgray"     :   "37m",
            "gray"      :   "1;30m",
            "lred"      :   "1;31m",
            "lgreen"    :   "1;32m",
            "yellow"    :   "1;33m",
            "lblue"     :   "1;34m",
            "pink"      :   "1;35m",
            "lcyan"     :   "1;36m",
            "white"     :   "1;37m",
        }
        b = "0m"
        s = "\033["
        clear = "0m"
        # In xterm, brown comes out as yellow..
        if xterm and fg == "yellow": fg = "brown"
        f = col_dict[fg]
        if bg:
            if bg == "yellow" and xterm: 
                bg = "brown"
            try: 
                b = col_dict[bg].replace('3', '4', 1)
            except KeyError: 
                pass
        return "%s%s%s%s%s%s%s" % (s, b, s, f, text, s, clear)
    else:
        return text

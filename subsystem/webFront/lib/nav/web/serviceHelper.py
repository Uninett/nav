"""
"""

import os
import re
try:
    import nav.path
    _checkerDir = os.path.join(nav.path.pythonlibdir, "nav/statemon/checker")
except:
    # not properly installed
    _checkerDir = "/usr/local/nav/navme/subsystem/statemon/lib/checker"
_checkerPattern = "Checker.py"
_descrPattern = 'Checker.descr'
_defaultArgs = ['port', 'timeout']
_regexp=re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)",re.M)

def getCheckers():
    """
    Returns a list of available checkers.
    """
    files = os.listdir(_checkerDir)
    result = []
    for file in files:
        if len(file) > len(_checkerPattern) and file[len(file)-len(_checkerPattern):]==_checkerPattern:
            result.append(file[:-len(_checkerPattern)].lower())
    return result

def getDescription(checkerName):
    """
    Returns a description of the service checker
    """
    descr = {}
    try:
        filename = os.path.join(_checkerDir, "%s%s" % (checkerName.capitalize(), _descrPattern))
        file = open(filename)
    except:
        #print "could not open file ", filename
        return
    for (key, value) in _regexp.findall(file.read()):
        if key == "description":
            descr[key] = value
        else:
            descr[key] = value.split(' ')
    return descr
    

import os, os.path, nav.path
import sys

def readConfig(filename, splitChar='='):
    """Reads a key=value type config file. If the specified path does
    not begin at the root, the file is search for in the default NAV
    configuration directory.  Returns a dictionary of the key/value
    pairs that were read."""

    if filename[0] != os.sep:
        filename = os.path.join(nav.path.sysconfdir, filename)

    configuration = {}
    file = open(filename, 'r')
    for line in file.readlines():
        line = line.strip()
        # Unless the line is a comment, we parse it
        if len(line) and line[0] != '#':
            # Split the key/value pair (max 1 split)
            try:
                (key, value) = line.split(splitChar, 1)
                value = value.split('#', 1)[0] # Remove end-of-line comments
                configuration[key.strip()] = value.strip()
            except ValueError:
                sys.stderr.write("Config file %s has errors.\n" % filename)

    file.close()
    return configuration

#!/usr/bin/env python

import re,sys

# First, dump the contents of the live snmpoid table like this:
#   pg_dump -a -d -u -f dump.sql -t snmpoid manage 
# Then pipe the file through this script and direct the output to a new file.
#

#
# Fields should be ordered as:
# snmpoidid, oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex
#
print "BEGIN;"
for line in sys.stdin:
    if line.startswith("INSERT"):

        name = re.search("\d+\,\ (.*?)\,",line).group(1)
        line = re.sub("\d+\, ","",line)
        line = re.sub("INTO snmpoid","INTO snmpoid (oidkey, snmpoid, descr, oidsource, uptodate, getnext, match_regex, decodehex)",line)
        print "DELETE FROM snmpoid WHERE oidkey=%s;" % name
        print line + "\n"

print "COMMIT;"

#!/usr/bin/env python
import psycopg, os, sys

#
# This script will connect to a live manage database and dump the
# contents of the snmpoid table in a format suitable for re-insertion
# at the same or a different site.
#
# Make sure the environment variable PGASSWORD is set before running the script.
# Should be rewritten to ask for a password if none is known.
#

dbname = "manage"
dbuser = os.getenv('PGUSER')
if not dbuser:
    dbuser = "postgres"
dbpasswd = os.getenv('PGPASSWORD')

connection = psycopg.connect('host=localhost dbname=%s user=%s password=%s' %
                             (dbname, dbuser, dbpasswd))
cursor = connection.cursor()
cursor.execute("SELECT oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex FROM snmpoid")

print "BEGIN;"
for row in cursor.fetchall():
    newrow = []
    for col in row:
        if col is None:
            newrow.append('NULL')
        else:
            newrow.append("'%s'" % str(col))
    print "DELETE FROM snmpoid WHERE oidkey=%s;" % newrow[0]
    print "INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext, match_regex, decodehex)",
    print "VALUES (%s);" % ",".join(newrow)
    print
    
print "COMMIT;"

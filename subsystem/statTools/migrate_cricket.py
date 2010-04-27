#!/usr/bin/env python
"""
Script to migrate from pre 3.6 versions of NAV to 3.6.
"""
import sys
from os.path import join
from nav.db import getConnection
from nav.rrd.rrdtool_utils import edit_datasource

def main(sysname):
    conn = getConnection('default')
    c = conn.cursor()

    option = ""
    if sysname:
        option = "AND sysname ~ '%s'" % sysname

    # Fetch all datasources which matches 'temp', order them so that the
    # highest comes first. This is important when deleting multiple datasources
    # from the file.
    q = """
    SELECT rrd_datasourceid, path, filename, name FROM netbox 
    JOIN rrd_file USING (netboxid)
    JOIN rrd_datasource USING (rrd_fileid)
    WHERE (path ~ '/routers' OR path ~ '/switches')
    AND descr ~ 'temp' %s
    ORDER BY path, filename, name desc
    """ % option

    c.execute(q)

    for id, path, filename, ds in c.fetchall():
        rrdfile = join(path, filename)
        print "Deleting %s from %s" % (ds, rrdfile)
        try:
            edit_datasource(rrdfile, ds, 'remove')
        except Exception, e:
            print e
            continue
        print "Deleting %s from database" % id

        delete = "DELETE FROM rrd_datasource WHERE rrd_datasourceid = %s"
        c.execute(delete, (id,))
        conn.commit()


if __name__ == '__main__':
    sysname = None
    if len(sys.argv) > 1:
        sysname = sys.argv[1]

    main(sysname)


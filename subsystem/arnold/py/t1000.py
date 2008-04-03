#!/usr/bin/python

import nav.arnold
import nav.db
import os

def main():

    # Connect to arnold-database, make cursor
    arnoldconn = nav.db.getConnection('default', 'arnold')
    arnoldc = arnoldconn.cursor()
    
    # Connect to manage-database, make cursor
    manageconn = nav.db.getConnection('default', 'manage')
    managec = manageconn.cursor()


    # Fetch all mac-addresses that we have blocked, check if they are
    # active somewhere else.

    query = """SELECT identityid, mac, blocked_reasonid, swportid, determined
    FROM identity
    WHERE blocked_status='disabled'
    AND lastchanged < now() + '-1 hour'"""

    try:
        arnoldc.execute(query)
    except nav.db.driver.ProgrammingError, why:
        print why


    rows = arnoldc.dictfetchall()

    for row in rows:
        print "%s is blocked, checking for activity..." %row['mac'] ,


        q = "SELECT sysname, module, port FROM cam WHERE mac=%s AND end_time = 'infinity'"
        try:
            managec.execute(q, (row['mac'],))
        except nav.db.driver.ProgrammingError, why:
            print why


        # If this mac-address is active behind another port, block it.

        if managec.rowcount > 0:

            print "active."

            # Fill id-array with needed variables
            id['ip'] = row['ip']
            id['mac'] = row['mac']
                

            sw = nav.arnold.findSwportIDinfo(row['swportid'])


            print "Blocking %s %s:%s" %(sw['sysname'], sw['module'], sw['port'])


            # Find and set autoenable and autoenablestep
            autoenable = 0
            stepq = "SELECT autoenablestep FROM event WHERE blocked_reasonid = %s AND identityid = %s AND autoenablestep IS NOT NULL ORDER BY eventtime DESC"
            try:
                arnoldc.execute(stepq, (row['blocked_reasonid'], row['identityid']))
            except nav.db.driver.ProgrammingError, why:
                print why
            autoenablestep = arnoldc.fetchone()[0]

            username = os.getlogin()
            comment = "Blocked automatically when switching ports"


            # Try to block port using arnold-library
            try:
                nav.arnold.blockPort(id, sw, autoenable, autoenablestep, row['determined'], row['blocked_reasonid'], comment, username)
            except (nav.arnold.AlreadyBlockedError, nav.arnold.ChangePortStatusError, nav.arnold.DbError), why:
                print why

        else:
            print "not active."



if __name__ == '__main__':
    main()


#!/usr/bin/env python
"""
This script does two things:
- Finds all rrd-files on the filesystem that has not been updated in a 
  given time, and deletes them.
- Finds all rrd-files in the database that does not exist on the filesystem
  and deletes the tuples in the database. 
"""

import re
import time
import sys
import os
from os.path import *
from optparse import OptionParser

from nav.db import getConnection

# Default threshold in days for deleting files based on modification time.
MODIFIEDTHRESHOLD = 365

def main(opts):

    if opts.db:
        clean_database()
    elif opts.path:
        clean_filesystem(opts.path, opts.delete)

def clean_database():
    """
    Search the rrd database for tuples that do not have a corresponding
    file. 
    """

    conn = getConnection("default")
    c = conn.cursor()

    query = """
    SELECT rrd_fileid, path, filename
    FROM rrd_file
    ORDER BY path, filename
    """
    c.execute(query)

    to_be_deleted = []
    for fileid, path, filename in c.fetchall():
        fullpath = join(path, filename)
        if not exists(fullpath):
            to_be_deleted.append((fileid, fullpath))

    if len(to_be_deleted) > 0:
        print "Deleting tuples from the database regarding:"
        for id, fullpath in to_be_deleted:
            print fullpath
            c.execute("DELETE FROM rrd_file WHERE rrd_fileid=%s", (id,))
        conn.commit()
        print "%s tuples deleted from database." % len(to_be_deleted)
    else:
        print "All files existed, nothing done."

    return


def clean_filesystem(path, delete):
    """
    Finds all rrd files in path and deletes them if not modified the last 
    MODIFIEDTHRESHOLD days 
    """

    def clean_directory(delete, directory, files):
        """
        This method is called for every directory in path.
        """
        pattern = re.compile("\.rrd$")
        threshold = MODIFIEDTHRESHOLD * 24 * 60 * 60

        files_to_delete = []
        for file in files:
            filename = join(directory, file)
            if isdir(filename):
                continue

            if pattern.search(filename):
                # Check last modification time
                last_mod_time = getmtime(filename)
                time_since_mod = now - last_mod_time
                if time_since_mod > threshold:
                    print "%s has not been modified since %s." % (filename,
                                                    time.ctime(last_mod_time))
                    files_to_delete.append(filename)

        if len(files_to_delete) > 0:
            filesize = 0
            counter = 0
            for file in files_to_delete:
                if delete:
                    try:
                        filesize += getsize(file)
                        os.remove(file)
                        counter += 1
                        # Also remove .meta file if it exists
                        # Not crucial as it has no impact.
                        try:
                            metafile = re.sub('\.rrd$', '.meta', file)
                            os.remove(metafile)
                        except:
                            pass
                    except OSError, ose:
                        print "Could not remove %s: %s" % (file, ose.strerror)
                        continue
                    except Exception, e:
                        print "Exception removing %s: %s" % (file, e)

            if delete:
                print "Deleted %s files, freeing %s kbytes" % (counter,
                                                           int(filesize / 1024))

    now = time.time()
    walk(path, clean_directory, delete)



if __name__ == '__main__':

    usage = """usage: %%prog [options]
    Deletes rrd-files (-f) or database tuples (-d). Only lists files as 
    default, if you want to actually delete them use the --DELETE flag. 
    The default modification threshold for deleting a file is %s 
    days. """ % MODIFIEDTHRESHOLD

    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--database", action="store_true", dest="db",
                      help="Clean database")
    parser.add_option("-f", "--filesystem", dest="path",
                      help="Clean filesystem given path to rrd-files.")
    parser.add_option("-t", "--threshold", dest="days",
                      help="Threshold in modification days for deleting files")
    parser.add_option("--DELETE", action="store_true", dest="delete",
                      default=False,
                  help="Set this flag to actually delete the files")

    opts, args = parser.parse_args()
    if opts.days:
        try:
            days = int(opts.days)
            MODIFIEDTHRESHOLD = days
        except ValueError, e:
            print "Input to -t must be an integer."
            sys.exit()
        except:
            print "Error parsing -t"
            sys.exit()
    
    if not (opts.db or opts.path):
        parser.print_help()
    else:
        main(opts)

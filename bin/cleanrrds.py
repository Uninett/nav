#!/usr/bin/env python
#
# Copyright (C) 2010 Norwegian University of Science and Technology
# Copyright (C) 2011 UNINETT AS
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
"""This program can do three things:

- Find all RRD files on the filesystem that has not been updated in a
  given time, and delete them.
- Find all references to non-existant RRD files in the database
  and deletes those tuples from the database.
- Remove stale references to pping RRD files from the database when there are
  duplicate entries.

"""

import re
import time
import os
from os.path import join, exists, isdir, getmtime, getsize, walk
from optparse import OptionParser
from collections import defaultdict

from nav.models.rrd import RrdFile
from django.db import transaction

# Default threshold in days for deleting files based on modification time.
MODIFIEDTHRESHOLD = 365

def main():
    """Parses program arguments and runs accordingly"""
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
    parser.add_option("-t", "--threshold", dest="days", type="int",
                      default=MODIFIEDTHRESHOLD,
                      help="Threshold in modification days for deleting files")
    parser.add_option("--DELETE", action="store_true", dest="delete",
                      default=False,
                  help="Set this flag to actually delete the files")

    opts, _args = parser.parse_args()

    if not (opts.db or opts.path):
        parser.print_help()
    else:
        run(opts)

def run(opts):
    """Runs according to given options"""
    if opts.db:
        clean_database()
        clean_pping_dupes()
    elif opts.path:
        clean_filesystem(opts.path, opts.days, opts.delete)

@transaction.commit_on_success
def clean_database():
    """Deletes database records referencing RRD files that don't exist on the
    filesystem.

    """
    rrds = RrdFile.objects.all().order_by('path', 'filename')

    to_be_deleted = [rrd for rrd in rrds
                     if not exists(rrd.get_file_path())]

    if len(to_be_deleted) > 0:
        print "Deleting references to non-existant RRD files from database:"
        for rrd in to_be_deleted:
            print rrd.get_file_path()
            rrd.delete()
        print "%s tuples deleted from database." % len(to_be_deleted)

@transaction.commit_on_success
def clean_pping_dupes():
    """Deletes database records referencing duplicate pping response time RRD
    files.

    Only the reference to the newest file is kept.

    """
    files_for_box = defaultdict(list)
    for rrd in RrdFile.objects.filter(subsystem="pping"):
        files_for_box[rrd.netbox_id].append(rrd)

    def _mtime_sortkey(rrd):
        path = rrd.get_file_path()
        return getmtime(path) if exists(path) else 0

    deleteable = []
    for files in files_for_box.values():
        files.sort(key=_mtime_sortkey, reverse=True)
        deleteable.extend(files[1:])

    if deleteable:
        print "\nDeleting stale ping response time duplicates for:"
        for rrd in deleteable:
            print "%s: %s" % (rrd.netbox.sysname,
                              rrd.get_file_path())
            rrd.delete()
        print "%s tuples delete from database." % len(deleteable)


def clean_filesystem(path, threshold, delete):
    """Recursively deletes all RRD files in path that haven't been modified in
    the last threshold number of days.
    """
    threshold = threshold * 24 * 60 * 60

    def clean_directory(delete, directory, files):
        """
        This method is called for every directory in path.
        """
        pattern = re.compile("\.rrd$")

        files_to_delete = []
        for fname in files:
            filename = join(directory, fname)
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
            for fname in files_to_delete:
                if delete:
                    try:
                        filesize += getsize(fname)
                        os.remove(fname)
                        counter += 1
                        # Also remove .meta file if it exists
                        # Not crucial as it has no impact.
                        try:
                            metafile = re.sub('\.rrd$', '.meta', fname)
                            os.remove(metafile)
                        except OSError:
                            pass
                    except OSError, err:
                        print "Could not remove %s: %s" % (fname, err.strerror)
                        continue
                    except Exception, err:
                        print "Exception removing %s: %s" % (fname, err)

            if delete:
                print "Deleted %s files, freeing %s kbytes" % (
                    counter, int(filesize / 1024))

    now = time.time()
    walk(path, clean_directory, delete)



if __name__ == '__main__':
    main()

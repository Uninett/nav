#!/usr/bin/env bash
#
# Copyright 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# This script will run an SQL file through PostgreSQL and create an
# error report if errors are found.
#
# For some strange reason, NAV sql scripts like to drop all tables and
# sequences before they are created.  These don't exist in an empty
# database, and these DROPs are therefore errors.  This script will
# filter out lines matching the regex "^DROP", by commenting them out.
#

if test -z "$1"; then
  echo You must supply an SQL script as a parameter
  exit 1
fi
sql="$1"
if ! test -f "$sql"; then
  echo The file $sql does not exist or is not a regular file
  exit 1
fi
tmp=${TMPDIR:-/var/tmp}
uniq=$$

if test -z "$PGUSER"; then
  read -p "Enter a PostgreSQL user name: " PGUSER
  export PGUSER
fi
if test -z "$PGPASSWORD"; then
  read -p "Enter a password for this user: " -s PGPASSWORD
  echo
  export PGPASSWORD
fi

filteredsql=${tmp}/sqltest.${uniq}
echo Filtering DROPs from sql file \> ${filteredsql}
perl -p -e 's/^DROP/-- DROP/i' ${sql} > ${filteredsql}

db=test_${uniq}
echo Creating test database \(${db}\)
createdb ${db} && createlang plpgsql ${db}

errorlog=${tmp}/sqltest.error.${uniq}
echo Processing SQL
psql -f ${filteredsql} ${db} > /dev/null 2> ${errorlog}
fgrep ERROR ${errorlog}
rm -f ${errorlog}

echo Dropping test database \(${db}\)
dropdb ${db}
rm ${filteredsql}

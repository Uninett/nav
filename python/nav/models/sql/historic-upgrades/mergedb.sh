#!/bin/sh
# Copyright 2008 Uninett AS
# License: GPLv3
# Author: Morten Brekkevold <morten.brekkevold@uninett.no>
#
newnavdb=nav
navdbuser=nav
nocreatedb=
nocreateuser=
nodump=
dumplocation=.

while getopts 'd:u:Dhnl:' OPTION
do
  case $OPTION in
      d) newnavdb="$OPTARG"
          ;;
      u) navdbuser="$OPTARG"
          ;;
      D) nocreatedb=1
          ;;
      n) nodump=1
          ;;
      l) dumplocation="$OPTARG"
	  ;;

      ?) cat <<EOF >&2
Copyright 2008 Uninett AS

This script automates the task of merging the four NAV 3.4 databases
into a single multi-namespaced NAV 3.5 database.

Usage: $(basename $0): [-d dbname] [-u dbuser] [-D] [-n]

Options:
  -d dbname      specify the name of the database to create and merge to, 
                 default value is nav
  -u dbuser      specify the name of the database user to own the database
                 and the relations therein, default value is nav
  -D             don't create a database, assume dbname already exists
  -l path        path to the directory where dump files will be created,
                 default is the current working directory
  -n             do not create dump files, assume they already exist in 
                 the dump path (manage-dump.sql, navprofiles-dump.sql,
                 logger-dump.sql arnold-dump.sql)

Environment variables:
  PGHOST         the postgresql host to connect to
  PGPORT         the port postgresql listens to
  PGUSER         the postgresql user to connect as when creating the
                 database and dumping/loading data from the old ones,
                 should be a superuser
  PGPASSWORD     the password to use when connecting as \$PGUSER
 
EOF
          exit 1
          ;;
  esac
done

if [ ! -d "$dumplocation" ]; then
    echo directory "$dumplocation" does not exist
    exit 1
fi

if [ ! "$nocreatedb" ]; then
    echo Creating database $newnavdb, owned by $navdbuser
    createdb --owner=$navdbuser --encoding=utf-8 $newnavdb || exit 1

    echo Installing PL/PgSQL language to database $newnavdb
    createlang plpgsql $newnavdb || exit 1
fi

if [ ! "$nodump" ]; then
    cat <<EOF
Dumping existing NAV databases to current directory.

WARNING: This will only dump the public namespace of each database.
It will not dump table privileges.  If you have locally added
namespaces/schemas and/or privileges to any of the databases, you're
on your own.
EOF

    for db in manage navprofiles logger arnold; do
        echo Dumping $db...
        pg_dump -f "$dumplocation/$db-dump.sql" --schema=public \
	    --no-owner --verbose --no-acl $db || exit 1
    done
fi

echo "Loading dumps into database $newnavdb"
echo "---"
cat <<EOF | psql --quiet $newnavdb || exit 1
-- Make nav own the public schema.  We do this so the nav user has access to
-- alter the public namespace.
ALTER SCHEMA public OWNER TO $navdbuser;

-- Work as the nav user
SET SESSION AUTHORIZATION '$navdbuser';
SET client_min_messages = warning;

-- Restore the manage dump into the 'public' schema, rename it to 'manage' and
-- create a new 'public' schema
\i $dumplocation/manage-dump.sql
ALTER SCHEMA public RENAME TO manage;
CREATE SCHEMA public;

-- Restore the navprofiles dump into the 'public' schema, rename it to
-- 'profiles' and create a new 'public' schema
\i $dumplocation/navprofiles-dump.sql
ALTER SCHEMA public RENAME TO profiles;
CREATE SCHEMA public;

-- Restore the logger dump into the 'public' schema, rename it to 'logger' and
-- create a new 'public' schema
\i $dumplocation/logger-dump.sql
ALTER SCHEMA public RENAME TO logger;
CREATE SCHEMA public;

-- Restore the arnold dump into the 'public' schema, rename it to 'arnold' and
-- create a new 'public' schema
\i $dumplocation/arnold-dump.sql
ALTER SCHEMA public RENAME TO arnold;
CREATE SCHEMA public;

CREATE SCHEMA radius;
ALTER DATABASE $newnavdb SET search_path = manage,profiles,logger,arnold,radius;
EOF

echo "---"

cat <<EOF
SUCCESS! Databases manage, navprofiles, logger and arnold were
(apparently) merged into the new $newnavdb database.

Your old NAV databases were not dropped, in case you still want them
for something.  You can delete them manually when they are no longer
needed, by issuing this command as the postgres superuser:

  for db in manage navprofiles logger arnold; do dropdb \$db; done

EOF

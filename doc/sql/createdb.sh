#!/bin/sh
# Copyright 2008 UNINETT AS
# License: GPLv2
# Author: Morten Brekkevold <morten.brekkevold@uninett.no>
#
navdb=nav
navdbuser=nav
navdbuserpass=
nocreatedb=
nocreateuser=

while getopts 'd:u:DUhp:' OPTION
  do
  case $OPTION in
      d) navdb="$OPTARG"
	  ;;
      u) navdbuser="$OPTARG"
	  ;;
      D) nocreatedb=1
	  ;;
      U) nocreateuser=1
	  ;;
      p) navdbuserpass="$OPTARG"
	  ;;

      ?) cat <<EOF >&2
Copyright 2008 UNINETT AS

This script automates the task of creating and initializing a NAV
PostgreSQL database.

Usage: $(basename $0): [-d dbname] [-u dbuser] [-D] [-U]

Options:
  -d dbname      specify the name of the database to initialize, default 
                 value is nav
  -u dbuser      specify the name of the database user to own the database
                 and the relations therein, default value is nav
  -p password    do not prompt for a password for dbuser when it is
                 created, but use this instead
  -D             don't create a database, use an existing one
  -U             don't create a database user, use an existing one

Environment variables:
  PGHOST         the postgresql host to connect to
  PGPORT         the port postgresql listens to
  PGUSER         the postgresql user to connect as when creating the user,
                 database and schema
  PGPASSWORD     the password to use when connecting as \$PGUSER
 
EOF
	  exit 2
	  ;;
  esac
done

if [ ! "$nocreateuser" ]; then
    echo Creating database user $navdbuser
    if [ -z "$navdbuserpass" ]; then
	createuser --pwprompt --no-superuser --no-createdb --no-createrole \
	    $navdbuser || exit 3
    else
	createuser --no-superuser --no-createdb --no-createrole \
	    $navdbuser || exit 3
	psql -c "ALTER USER $navdbuser WITH PASSWORD '$navdbuserpass';" \
            template1 || exit 3
    fi
fi

if [ ! "$nocreatedb" ]; then
    echo Creating database $navdb, owned by $navdbuser
    createdb --owner=$navdbuser --encoding=utf-8 $navdb || exit 4

    echo Installing PL/PgSQL language to database $navdb
    createlang plpgsql $navdb || exit 5
fi

echo "Initializing database $NAVDB"
echo "---"
cat <<EOF | psql --quiet $navdb || exit 6
SET SESSION AUTHORIZATION '$navdbuser';
SET client_min_messages = warning;

-- Create schemas
CREATE SCHEMA manage;
CREATE SCHEMA profiles;
CREATE SCHEMA logger;
CREATE SCHEMA arnold;

-- Now, initialize the database
SET search_path = manage;
\i manage.sql
\i types.sql
\i snmpoid.sql

SET search_path = profiles;
\i navprofiles.sql

SET search_path = logger;
\i logger.sql

SET search_path = arnold;
\i arnold.sql

SET search_path = radius;
\i radius.sql

ALTER DATABASE $navdb SET search_path = manage,profiles,logger,arnold,radius;
SET search_path = manage,profiles,logger,arnold,radius;

-- Build indexes now
\i indexes.sql
EOF

echo "---"
echo "Done."
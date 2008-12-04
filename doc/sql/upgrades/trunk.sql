/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.5 to the current trunk revision (i.e. the tip of the default
 * development branch).  Please update this with every change you make to the
 * database initialization scripts.  It will eventually become the update
 * script for the next release.
 *
 * If you are keeping your installation in sync with the default branch, you
 * should watch this file for changes and run them when updating (check the
 * diffs!).  We also recommend running navschema.py on each schema upgrade,
 * to ensure that your database's search path is alway up to date.
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql nav <username>
 *
*/

BEGIN;

-- Add alerthistid foreign key so that we can use alerthistory in
-- alertengine at a latter point in time.
ALTER TABLE manage.alertq ADD alerthistid integer NULL;
ALTER TABLE manage.alertq ADD CONSTRAINT alertq_alerthistid_fkey
  FOREIGN KEY (alerthistid)
  REFERENCES manage.alerthist (alerthistid)
  ON UPDATE CASCADE
  ON DELETE SET NULL;

-- Remove this field which was added in an earlier 3.5 beta.
ALTER TABLE manage.alertq DROP closed;

-- Update two radius indexes
DROP INDEX radiusacct_stop_user_index;
CREATE INDEX radiusacct_stop_user_index ON radiusacct (AcctStopTime, lower(UserName));

DROP INDEX radiuslog_username_index;
CREATE INDEX radiuslog_username_index ON radiuslog(lower(UserName));

COMMIT;

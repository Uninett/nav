/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.5.0b2 to 3.5.0b3
 *
 * *************** NB NB NB NB NB NB NB ***************
 *
 * This upgrade script assumes you have merged your NAV databases into
 * a single, multi-namespaced database and run 3.5.0b1.sql and
 * 3.5.0b2.sql.  If you haven't, please read the release notes for NAV
 * 3.5 and the instructions in doc/sql/upgrades/README .
 *
 * *************** NB NB NB NB NB NB NB ***************
 *
 * Connect to PostgreSQL and run this script as the nav database owner
 * like this:
 *
 *  psql -f 3.5.0b3.sql <db_name> <username>
 *
 * When you are done, make sure the database search path is correct,
 * by running the new program navschema.py.  Otherwise your radius
 * module might not work.
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

-- Insert the new version number if we got this far.
INSERT INTO nav_schema_version (version) VALUES ('3.5.0b3');
COMMIT;

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
-- Insert schema changes here.

-- Force all foreign key constraints to follow the exact same naming
-- pattern: <tablename>_<column_name>_fkey 
--
-- This should change about 7 "wrongly" named foreign keys on the
-- netbox, accountalertqueue and log_message_type tables, and any
-- foreign key whose name has been automatically set to '$<number>' by
-- older versions of PostgreSQL.
UPDATE pg_constraint
SET conname=cl.relname || '_' || pa.attname || '_fkey'
FROM pg_class cl, pg_attribute pa, pg_namespace nsp
WHERE
  contype = 'f' AND
  conname <> (cl.relname || '_' || pa.attname || '_fkey') AND
  connamespace = nsp.oid AND
  nspname IN ('manage', 'profiles', 'arnold', 'logger', 'radius') AND
  conrelid = cl.oid AND
  pa.attrelid = cl.oid AND
  conkey[1] = pa.attnum
;

ALTER TABLE org DROP CONSTRAINT "org_parent_fkey";
ALTER TABLE org ADD CONSTRAINT org_parent_fkey 
                               FOREIGN KEY (parent) REFERENCES org (orgid)
                               ON UPDATE CASCADE;

-- Index to speed up ipdevinfo queries for the first cam entry from a box
CREATE INDEX cam_netboxid_start_time_btree ON cam USING btree (netboxid, start_time);

-- Try to provide consistency between code and db names.
ALTER TABLE alertsubscription RENAME ignore_closed_alerts TO ignore_resolved_alerts;

COMMIT;

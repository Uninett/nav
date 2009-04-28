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

ALTER TABLE org DROP CONSTRAINT "$1";
ALTER TABLE org ADD CONSTRAINT org_parent_fkey 
                               FOREIGN KEY (parent) REFERENCES org (orgid)
                               ON UPDATE CASCADE;

-- Index to speed up ipdevinfo queries for the first cam entry from a box
CREATE INDEX cam_netboxid_start_time_btree ON cam USING btree (netboxid, start_time);

-- Django needs an ID field
ALTER TABLE navbarlink DROP CONSTRAINT accountnavbar_pkey;
ALTER TABLE navbarlink ADD UNIQUE (accountid, navbarlinkid);
CREATE SEQUENCE navbarlink_id_seq;
ALTER TABLE navbarlink_id_seq OWNER TO nav;
ALTER TABLE navbarlink ADD COLUMN id integer NOT NULL PRIMARY KEY DEFAULT nextval('accountnavbar_id_seq');

COMMIT;

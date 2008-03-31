/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.3 to the current trunk revision.  Please update this with every
 * change you make to the database initialization scripts.  It will eventually
 * become the update script for the next release.
 *
 * Also, if you are keeping your installation in sync with trunk, you should
 * watch this file for changes and run them when updating (check the diffs!)
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql manage <username>
 *
*/


--
-- Add field 'contact' to org-table in manage-database
--

\connect manage

ALTER TABLE org ADD contact VARCHAR;


--
-- The following changes to the arnold-database are necessary to migrate to new version of Arnold.
--

\connect arnold

-- Create new table for storing of quarantine vlans.
CREATE TABLE quarantine_vlans (
quarantineid SERIAL PRIMARY KEY,
vlan INT,
description VARCHAR
);

-- Changes regarding table blocked_reasons
ALTER TABLE blocked_reason RENAME text TO name;

-- Changes regarding table identity
ALTER TABLE identity DROP CONSTRAINT identity_blocked_status;
ALTER TABLE identity ADD CONSTRAINT identity_blocked_status CHECK (blocked_status='disabled' OR blocked_status='enabled' OR blocked_status='quarantined');

ALTER TABLE identity DROP COLUMN swsysname;
ALTER TABLE identity DROP COLUMN swvendor;
ALTER TABLE identity DROP COLUMN swip;
ALTER TABLE identity DROP COLUMN swmodule;
ALTER TABLE identity DROP COLUMN swport;
ALTER TABLE identity DROP COLUMN swifindex;
ALTER TABLE identity DROP COLUMN community;
ALTER TABLE identity DROP COLUMN multiple;
ALTER TABLE identity DROP COLUMN secret;
ALTER TABLE identity DROP COLUMN userlock;

ALTER TABLE identity ADD fromvlan INT;
ALTER TABLE identity ADD tovlan INT;

-- Changes regarding table block
ALTER TABLE block DROP COLUMN private;
ALTER TABLE block DROP COLUMN userid;

ALTER TABLE block ADD activeonvlans VARCHAR;
ALTER TABLE block ADD detainmenttype VARCHAR CHECK (detainmenttype='disable' OR detainmenttype='quarantine');
ALTER TABLE block ADD quarantineid INT REFERENCES quarantine_vlans ON UPDATE CASCADE ON DELETE CASCADE;

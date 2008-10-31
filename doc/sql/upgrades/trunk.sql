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
 * diffs!)
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql nav <username>
 *
*/

-- Alert senders
INSERT INTO alertsender VALUES (1, 'Email', 'email');
INSERT INTO alertsender VALUES (2, 'SMS', 'sms');
INSERT INTO alertsender VALUES (3, 'Jabber', 'jabber'); 

-- Fix for LP#285331 Duplicate RRD file references
-- Delete oldest entries if there are duplicate rrd file references
DELETE FROM rrd_file 
WHERE rrd_fileid IN (SELECT b.rrd_fileid
                     FROM rrd_file a
                     JOIN rrd_file b ON (a.path = b.path AND 
                                         a.filename=b.filename AND 
                                         a.rrd_fileid > b.rrd_fileid)
		     );

-- Modify rrd_file to prevent duplicate path/filename entries
ALTER TABLE rrd_file ADD CONSTRAINT rrd_file_path_filename_key UNIQUE (path, filename);

------------------------------------------------------------------------------
-- simple schema version check table
------------------------------------------------------------------------------
CREATE TABLE manage.nav_schema_version (
    version VARCHAR NOT NULL,
    time TIMESTAMP NOT NULL DEFAULT NOW()
);

-- FIXME: Insert default as version name.  This should be updated on
-- each NAV release branch.
INSERT INTO nav_schema_version (version) VALUES ('default');

-- Ensure only a single row will ever exist in this table.
CREATE OR REPLACE RULE nav_schema_version_insert AS ON INSERT TO nav_schema_version
    DO INSTEAD UPDATE nav_schema_version SET version=NEW.version, time=NOW();

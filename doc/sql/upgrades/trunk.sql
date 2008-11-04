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

-- Remove floating devices.
-- Devices that don't have a serial and no connected modules or netboxes.
-- Triggers on delete on module and netbox.
CREATE OR REPLACE FUNCTION manage.remove_floating_devices() RETURNS TRIGGER AS '
    BEGIN
        DELETE FROM device WHERE
            deviceid NOT IN (SELECT deviceid FROM netbox) AND
            deviceid NOT IN (SELECT deviceid FROM module) AND
            serial IS NULL;
        RETURN NULL;
        END;
    ' language 'plpgsql';

CREATE TRIGGER trig_module_delete_prune_devices
    AFTER DELETE ON module
    FOR EACH STATEMENT
    EXECUTE PROCEDURE remove_floating_devices();

CREATE TRIGGER trig_netbox_delete_prune_devices
    AFTER DELETE ON netbox
    FOR EACH STATEMENT
    EXECUTE PROCEDURE remove_floating_devices();

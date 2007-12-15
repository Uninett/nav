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

-- Clean install of 3.3.0 caused this rule never to be created.  Recreate it
-- here for those who started out with clean 3.3.0 installs.
CREATE OR REPLACE RULE close_arp_prefices AS ON DELETE TO prefix
  DO UPDATE arp SET end_time=NOW(), prefixid=NULL 
     WHERE prefixid=OLD.prefixid;

-- Django needs a single column it can treat as primary key :-(
ALTER TABLE netboxcategory ADD COLUMN id SERIAL;
ALTER TABLE netbox_vtpvlan ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE netboxsnmpoid ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE serviceproperty ADD COLUMN id SERIAL;
ALTER TABLE maint_component ADD COLUMN id SERIAL;
ALTER TABLE message_to_maint_task ADD COLUMN id SERIAL;
ALTER TABLE alertqmsg ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alertqvar ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alerthistmsg ADD COLUMN id SERIAL PRIMARY KEY;
ALTER TABLE alerthistvar ADD COLUMN id SERIAL PRIMARY KEY;

/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.2 to the current trunk revision.  Please update this with every
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

-- Close invalid moduleState states in alerthist.
UPDATE alerthist SET end_time=now()
WHERE eventtypeid = 'moduleState' 
  AND subid IS NOT NULL
  AND subid NOT IN (SELECT moduleid FROM module) 
  AND end_time = 'infinity';

-- New rule to automatically close module related alert states when modules
-- are deleted.
CREATE RULE close_alerthist_modules AS ON DELETE TO module
  DO UPDATE alerthist SET end_time=NOW() 
     WHERE eventtypeid='moduleState' 
       AND end_time='infinity'
       AND subid=OLD.moduleid;

-- Added constraint to prevent accidental duplicates in the alerttype table.
ALTER TABLE alerttype ADD CONSTRAINT alerttype_eventalert_unique UNIQUE
(eventtypeid, alerttype);

-- Renamed eventengine source from deviceTracker to deviceManagement
DELETE FROM subsystem WHERE name = 'deviceTracker';
INSERT INTO subsystem (name) VALUES ('deviceManagement');

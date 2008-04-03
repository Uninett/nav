/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.2 to 3.3.  THIS SCRIPT WILL NOT WORK ON POSTGRESQL
 * VERSIONS PRIOR TO 8.0.
 *
 * Run the script as the nav database user like this:
 *
 *  psql -f 3.3.0.sql manage nav
 *
 * Also make sure to run types.sql and snmpoid.sql to make sure your type and
 * snmpoid tables are up-to-date:
 *
 *  psql -f types.sql manage nav
 *  psql -f snmpoid.sql manage nav
 *
*/

\c manage
BEGIN;
LOCK TABLE arp IN ACCESS EXCLUSIVE MODE;
LOCK TABLE cam IN ACCESS EXCLUSIVE MODE;

-- Close invalid moduleState states in alerthist.
UPDATE alerthist SET end_time=now()
WHERE eventtypeid = 'moduleState' 
  AND subid IS NOT NULL
  AND subid NOT IN (SELECT moduleid FROM module) 
  AND end_time = 'infinity';

-- New rule to automatically close module related alert states when modules
-- are deleted.
CREATE OR REPLACE RULE close_alerthist_modules AS ON DELETE TO module
  DO UPDATE alerthist SET end_time=NOW() 
     WHERE eventtypeid IN ('moduleState', 'linkState')
       AND end_time='infinity'
       AND deviceid=OLD.deviceid;

-- Added constraint to prevent accidental duplicates in the alerttype table.
ALTER TABLE alerttype ADD CONSTRAINT alerttype_eventalert_unique UNIQUE
(eventtypeid, alerttype);

-- Renamed eventengine source from deviceTracker to deviceManagement
UPDATE subsystem SET name = 'deviceManagement' WHERE name = 'deviceTracker';
-- Add snmptrapd subsystem
INSERT INTO subsystem (SELECT 'snmptrapd' 
                       WHERE NOT EXISTS (SELECT * 
                                         FROM subsystem
                                         WHERE name='snmptrapd'));

-- Create index on alerthist.start_time
CREATE INDEX alerthist_start_time_btree ON alerthist USING btree (start_time);


-- Now, change the datatype of cam.mac and arp.mac from CHAR(12) to MACADDR.
-- Also change the datatype of cam.port from INT to VARCHAR.
-- This operation will only work on PostgreSQL 8 and newer.  An alternative
-- way to convert the tables, suitable for PostgreSQL 7.4, can be found in the
-- comments below (NOTE however, that using this method on PostgreSQL 7.4 may
-- take several hours to complete, depending on the size of your cam/arp
-- tables!)

-- First, the cam table
ALTER TABLE cam ALTER COLUMN mac TYPE macaddr USING mac::macaddr;
ALTER TABLE cam ALTER COLUMN port TYPE varchar;

-- -- Alternative method for PostgreSQL 7.4:
-- BEGIN;
-- LOCK TABLE cam IN ACCESS EXCLUSIVE MODE;
-- ALTER TABLE cam ADD COLUMN mac2 macaddr;
-- ALTER TABLE cam ADD COLUMN port2 VARCHAR;
-- UPDATE cam SET mac2 = mac::text::macaddr, port2 = port::VARCHAR;
-- ALTER TABLE cam DROP COLUMN mac;
-- ALTER TABLE cam DROP COLUMN port;
-- ALTER TABLE cam RENAME COLUMN mac2 TO mac;
-- ALTER TABLE cam RENAME COLUMN port2 TO port;
-- ALTER TABLE cam ALTER COLUMN mac SET NOT NULL;
-- CREATE INDEX cam_mac_btree ON cam USING btree (mac);
-- ALTER TABLE cam ADD CONSTRAINT cam_unique UNIQUE (netboxid,sysname,module,port,mac,start_time);
-- END;

-- Alter the port value for all open cam entries, set it to be the interface name.
UPDATE cam SET port=interface FROM swport JOIN module USING (moduleid) WHERE cam.netboxid=module.netboxid AND swport.ifindex=cam.ifindex AND end_time='infinity';

-- Then the arp table, but we need to drop the netboxmac view first, since it
-- depends on the mac column
DROP VIEW netboxmac;
ALTER TABLE arp ALTER COLUMN mac TYPE macaddr USING mac::macaddr;


-- -- Alternative method for PostgreSQL 7.4 (still need to drop netboxmac first!)
-- BEGIN;
-- LOCK TABLE arp IN ACCESS EXCLUSIVE MODE;
-- ALTER TABLE arp ADD COLUMN mac2 macaddr;
-- UPDATE arp SET mac2 = mac::text::macaddr;
-- ALTER TABLE arp DROP COLUMN mac;
-- ALTER TABLE arp RENAME COLUMN mac2 TO mac;
-- ALTER TABLE arp ALTER COLUMN mac SET NOT NULL;
-- CREATE INDEX arp_mac_btree ON arp USING btree (mac);
-- END;

-- Recreate the netboxmac view.
CREATE VIEW netboxmac AS  
(SELECT DISTINCT ON (mac) netbox.netboxid, arp.mac
 FROM netbox
 JOIN arp ON (arp.arpid = (SELECT arp.arpid FROM arp WHERE arp.ip=netbox.ip AND end_time='infinity' LIMIT 1)))
UNION DISTINCT
(SELECT DISTINCT ON (mac) module.netboxid,mac
 FROM arp
 JOIN gwportprefix gwp ON
  (arp.ip=gwp.gwip AND (hsrp=true OR (SELECT COUNT(*) FROM gwportprefix WHERE gwp.prefixid=gwportprefix.prefixid AND hsrp=true) = 0))
 JOIN gwport USING(gwportid)
 JOIN module USING (moduleid)
 WHERE arp.end_time='infinity');

-- Performed the following unscientific timings on a AMD Athlon 64 X2 Dual
-- Core Processor 3800+ with 1GB RAM and a single SATA disk, converting
-- arp.mac and cam.mac from char(12) to macaddr data type.  The cam table
-- contained 1,432,162 rows, the arp table 753,499 rows:
--
-- The acrobatic PostgreSQL 7.4 method: 2h39m16s
-- The simpler PostgreSQL 8.x method:   0h04m48s


-- Rule to automatically close arp entries related to a given prefix
CREATE RULE close_arp_prefices AS ON DELETE TO prefix
  DO UPDATE arp SET end_time=NOW(), prefixid=NULL 
     WHERE prefixid=OLD.prefixid;

END;

\c navprofiles
BEGIN;

-- Fix error in sysname matching
UPDATE matchfield SET valueid='netbox.sysname' WHERE matchfieldid=15;

END;

/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.0_beta7 to 3.0_beta8.  
 *
 * A design fault and a programming error made it possible to assign
 * multiple netboxes to the same physical device (serial number), and
 * also multiple modules to the same physical device.  In the real
 * world, it is (or at least should be!) impossible for two physical
 * devices to have the same serial number.  We try to fix any
 * occurences of this problem in an existing NAV installation by
 * creating new, empty devices for each of the existing netbox entries
 * that refer to the same deviceids, and then reassigning the netboxes
 * to these new devices.  The same goes for modules.  When restarted,
 * the new getDeviceData should find the serial numbers of these
 * netboxes/modules and update the device entries appropriately.
 *
 * Please be aware, though, that this may have adverse side effects on
 * the device histories recorded in the NAV database - you are advised
 * to re-seed your NAV database for production purposes.
 *
 * Connect to PostgreSQL as the postgres superuser and run this script
 * like this:
 *
 * psql -f 3.0_beta8.sql manage postgres
 *
 * Please, also run the updated snmpoid.sql script over again, like
 * this:
 *
 * psql -f snmpoid.sql manage postgres
 *
 *
*/

BEGIN;
-- First, we must eliminate all instances of duplicate device
-- references in the netbox table.  We create new, empty device
-- entries for the netboxes having duplicates.  Then we do the same
-- for the module table.
\echo Finding duplicate device references in netbox
SELECT netboxid, nextval ('public.device_deviceid_seq'::text) AS newdevid
INTO TEMP TABLE netbox_reassignment
FROM netbox
WHERE deviceid IN (SELECT deviceid
                   FROM netbox
                   GROUP BY deviceid HAVING count(netboxid) > 1);
\echo Creating new devices
INSERT INTO device SELECT newdevid FROM netbox_reassignment;
\echo Reassigning the netboxes to the new devices and adding the UNIQUE(deviceid) constraint to the netbox table
UPDATE netbox SET deviceid = newdevid FROM netbox_reassignment d
WHERE netbox.netboxid = d.netboxid;
ALTER TABLE netbox ADD CONSTRAINT netbox_deviceid_key UNIQUE(deviceid);


\echo Finding duplicate device references in module
SELECT moduleid, nextval ('public.device_deviceid_seq'::text) AS newdevid
INTO TEMP TABLE module_reassignment
FROM module
WHERE deviceid IN (SELECT deviceid
                   FROM module
                   GROUP BY deviceid HAVING count(moduleid) > 1);
\echo Creating new devices
INSERT INTO device SELECT newdevid FROM module_reassignment;
\echo Reassigning the modules to the new devices and adding the UNIQUE(deviceid) constraint to the module table
UPDATE module SET deviceid = newdevid FROM module_reassignment d
WHERE module.moduleid = d.moduleid;
ALTER TABLE module ADD CONSTRAINT module_deviceid_key UNIQUE(deviceid);


-- Fix poorly named column
ALTER TABLE gwport RENAME COLUMN ospf TO metric;

-- subid field changes type
ALTER TABLE eventq RENAME COLUMN subid TO subid_old;
ALTER TABLE eventq ADD COLUMN subid VARCHAR;
UPDATE eventq SET subid=subid_old;
ALTER TABLE eventq DROP COLUMN subid_old;

ALTER TABLE alertq RENAME COLUMN subid TO subid_old;
ALTER TABLE alertq ADD COLUMN subid VARCHAR;
UPDATE alertq SET subid=subid_old;
ALTER TABLE alertq DROP COLUMN subid_old;

ALTER TABLE alerthist RENAME COLUMN subid TO subid_old;
ALTER TABLE alerthist ADD COLUMN subid VARCHAR;
UPDATE alerthist SET subid=subid_old;
ALTER TABLE alerthist DROP COLUMN subid_old;

-- Fix bug in default value (all events were set to table creation
-- time)
ALTER TABLE eventq ALTER COLUMN time SET DEFAULT NOW ();

INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('moduleState','moduleDownWarning','Warning sent before declaring the module down.');

UPDATE alerttype 
SET alerttype='serialChanged', 
    alerttypedesc='Serial number for the device has changed.'
WHERE eventtypeid='info' AND alerttype='deviceRecreated';

-- New table
CREATE TABLE alertqvar (
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  UNIQUE(alertqid, var) -- only one val per var per event
);
CREATE INDEX alertqvar_alertqid_btree ON alertqvar USING btree (alertqid);


-- Redo the vlanPlot groups
DELETE FROM vp_netbox_grp_info WHERE name IN ('Bynett', 'Kjernenett', 'Testnett');
INSERT INTO vp_netbox_grp_info (vp_netbox_grp_infoid,name,hideicons) VALUES (0,'_Top',true);

-- Reset table privileges, since we created a new table
SELECT nav_grant('navread', false);
SELECT nav_grant('navwrite', true);

COMMIT;

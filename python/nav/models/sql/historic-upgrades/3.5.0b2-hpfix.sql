/*
 * This SQL script removes all modules from devices from the HP
 * vendor, and triggers getDeviceData to re-profile the SNMP OID
 * compatibility of the same devices.
 *
 * This may possibly be necessary to remove lingering side-effects
 * from the HP SwitchStack support that was removed in NAV 3.5.0b2.
 * 
 * If you are experiencing problems related to HP modules, ports and
 * topology after an upgrade to NAV 3.5, stop getDeviceData and run
 * this script as the nav database owner like this:
 *
 * psql -f 3.5.0b2-hpfix.sql <db_name> <username>
 * 
 * You can then start getDeviceData again.
*/

BEGIN;

-- Delete modules from HP devices.  This will cascade to all ports on
-- HP devices as well.  getDeviceData will rediscover the ports when
-- restarted.
DELETE FROM module 
WHERE netboxid IN (SELECT netboxid
                   FROM netbox
                   JOIN type USING (typeid) 
                   WHERE vendorid = 'hp');

-- Tell getDeviceData to re-profile the OID compatibility of HP
-- devices.
UPDATE netbox
SET uptodate = FALSE
FROM type
WHERE 
  netbox.typeid = type.typeid AND
  vendorid = 'hp';

COMMIT;

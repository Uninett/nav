/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.0 to 3.1
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f 3.1.0.sql manage <username>
 *
 * The new subsystem Arnold also needs a new database, while some vendors,
 * types and snmpoids have been added and/or updated.  Therefore you must read
 * doc/sql/README over again and make sure to follow its instructions on how
 * to create the arnold database and run the following scripts:
 *
 *   - arnold.sql
 *   - types.sql
 *   - snmpoid.sql
 *
*/

\c manage

BEGIN;
\echo Changing manage schema

ALTER TABLE snmpoid ADD COLUMN defaultfreq INT4;
ALTER TABLE snmpoid ALTER COLUMN defaultfreq SET DEFAULT 21600;
UPDATE snmpoid SET defaultfreq=21600;
ALTER TABLE snmpoid ALTER COLUMN defaultfreq SET NOT NULL;

-- This view gives the allowed vlan for a given hexstring i swportallowedvlan
CREATE TABLE range (
  num INT NOT NULL PRIMARY KEY
);
INSERT INTO range VALUES (0);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
INSERT INTO range (SELECT num+(SELECT COUNT(*) FROM range) FROM range);
DELETE FROM range WHERE num >= 1000;

CREATE VIEW allowedvlan AS
  (SELECT swportid,num AS allowedvlan FROM swportallowedvlan CROSS JOIN range
    WHERE num < length(decode(hexstring,'hex'))*8 AND (CASE WHEN length(hexstring)=256
    THEN get_bit(decode(hexstring,'hex'),(num/8)*8+7-(num%8))
    ELSE get_bit(decode(hexstring,'hex'),(length(decode(hexstring,'hex'))*8-num+7>>3<<3)-8+(num%8))
    END)=1);

CREATE VIEW allowedvlan_both AS
  (select swportid,swportid as swportid2,allowedvlan from allowedvlan ORDER BY allowedvlan) union
  (select  swport.swportid,to_swportid as swportid2,allowedvlan from swport join allowedvlan
    on (swport.to_swportid=allowedvlan.swportid) ORDER BY allowedvlan);

\echo Adding devBrowse as a subsystem to the event system
INSERT INTO subsystem (name) VALUES ('devBrowse');

\echo Updating existing equipment types in your database
UPDATE "type" SET vendorid='cisco', typename='cisco12416', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Cisco 12416 (GSR) Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.385';
UPDATE "type" SET vendorid='cisco', typename='cisco1751', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Cisco 1751 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.326';
UPDATE "type" SET vendorid='3com', typename='PS40', cdp='0', tftp='0', cs_at_vlan='0', chassis='1', frequency='3600', descr='Portstack 40 hub' WHERE sysobjectid='1.3.6.1.4.1.43.10.27.4.1';
UPDATE "type" SET vendorid='3com', typename='SW1100', cdp=NULL, tftp=NULL, cs_at_vlan='0', chassis='1', frequency='3600', descr='Portswitch 1100' WHERE sysobjectid='1.3.6.1.4.1.43.10.27.4.1.2.1';
UPDATE "type" SET vendorid='3com', typename='SW3300', cdp=NULL, tftp=NULL, cs_at_vlan='0', chassis='1', frequency='3600', descr='Portswitch 3300' WHERE sysobjectid='1.3.6.1.4.1.43.10.27.4.1.2.2';
UPDATE "type" SET vendorid='3com', typename='SW9300', cdp=NULL, tftp=NULL, cs_at_vlan='0', chassis='1', frequency='3600', descr='Portswitch 9300' WHERE sysobjectid='1.3.6.1.4.1.43.1.16.2.2.2.1';
UPDATE "type" SET vendorid='alcatel', typename='alcatel6800', cdp=NULL, tftp=NULL, cs_at_vlan='0', chassis='0', frequency='3600', descr='Alcatel Omniswitch 6800' WHERE sysobjectid='1.3.6.1.4.1.6486.800.1.1.2.1.6.1.1';
UPDATE "type" SET vendorid='cisco', typename='catalyst2924XL', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 2924 XL switch' WHERE sysobjectid='1.3.6.1.4.1.9.1.183';
UPDATE "type" SET vendorid='cisco', typename='catalyst2924XLv', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Catalyst 2924 XLv switch' WHERE sysobjectid='1.3.6.1.4.1.9.1.217';
UPDATE "type" SET vendorid='cisco', typename='catalyst295024G', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Catalyst 2950G-24-E1 switch' WHERE sysobjectid='1.3.6.1.4.1.9.1.428';
UPDATE "type" SET vendorid='cisco', typename='catalyst295048G', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Catalyst 295048G' WHERE sysobjectid='1.3.6.1.4.1.9.1.429';
UPDATE "type" SET vendorid='cisco', typename='catalyst297024TS', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 2970' WHERE sysobjectid='1.3.6.1.4.1.9.1.561';
UPDATE "type" SET vendorid='cisco', typename='catalyst3508GXL', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 3508 GXL switch' WHERE sysobjectid='1.3.6.1.4.1.9.1.246';
UPDATE "type" SET vendorid='cisco', typename='catalyst3524XL', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 3524 XL switch' WHERE sysobjectid='1.3.6.1.4.1.9.1.248';
UPDATE "type" SET vendorid='cisco', typename='catalyst3524tXLEn', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Catalyst 3524tXLEn' WHERE sysobjectid='1.3.6.1.4.1.9.1.287';
UPDATE "type" SET vendorid='cisco', typename='catalyst375024ME', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Catalyst 3750 Metro' WHERE sysobjectid='1.3.6.1.4.1.9.1.574';
UPDATE "type" SET vendorid='cisco', typename='catalyst37xxStack', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 3750' WHERE sysobjectid='1.3.6.1.4.1.9.1.516';
UPDATE "type" SET vendorid='cisco', typename='catalyst4003', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 4003' WHERE sysobjectid='1.3.6.1.4.1.9.5.40';
UPDATE "type" SET vendorid='cisco', typename='catalyst4006', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 4006 sup 2 L3 switch' WHERE sysobjectid='1.3.6.1.4.1.9.1.448';
UPDATE "type" SET vendorid='cisco', typename='catalyst4506', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 4506 sup4 L3 switch' WHERE sysobjectid='1.3.6.1.4.1.9.1.502';
UPDATE "type" SET vendorid='cisco', typename='catalyst4510', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Catalyst 4510' WHERE sysobjectid='1.3.6.1.4.1.9.1.537';
UPDATE "type" SET vendorid='cisco', typename='catalyst6509', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 6509' WHERE sysobjectid='1.3.6.1.4.1.9.1.283';
UPDATE "type" SET vendorid='cisco', typename='cisco1000', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 1000 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.40';
UPDATE "type" SET vendorid='cisco', typename='cisco1003', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 1003 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.41';
UPDATE "type" SET vendorid='cisco', typename='cisco1005', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='Cisco 1005 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.49';
UPDATE "type" SET vendorid='cisco', typename='cisco10720', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Cisco 10720 (YB) Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.397';
UPDATE "type" SET vendorid='cisco', typename='cisco12016', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Cisco 12016 (GSR) Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.273';
UPDATE "type" SET vendorid='cisco', typename='cisco12404', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 12404 (GSR) Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.423';
UPDATE "type" SET vendorid='cisco', typename='cisco1601', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 1601 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.113';
UPDATE "type" SET vendorid='cisco', typename='cisco1602', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 1602 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.114';
UPDATE "type" SET vendorid='cisco', typename='cisco1603', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 1603 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.115';
UPDATE "type" SET vendorid='cisco', typename='cisco1604', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 1604 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.116';
UPDATE "type" SET vendorid='cisco', typename='cisco1721', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 1721 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.444';
UPDATE "type" SET vendorid='cisco', typename='cisco2500', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 2500 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.13';
UPDATE "type" SET vendorid='cisco', typename='cisco2501', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 2501 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.17';
UPDATE "type" SET vendorid='cisco', typename='cisco2502', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 2502 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.18';
UPDATE "type" SET vendorid='cisco', typename='cisco2503', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 2503 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.19';
UPDATE "type" SET vendorid='cisco', typename='cisco2511', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 2511 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.27';
UPDATE "type" SET vendorid='cisco', typename='cisco4500', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Cisco 4500 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.14';
UPDATE "type" SET vendorid='cisco', typename='cisco3620', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 3620 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.122';
UPDATE "type" SET vendorid='cisco', typename='cisco3640', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='Cisco 3640 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.110';
UPDATE "type" SET vendorid='cisco', typename='cisco4000', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='Cisco 4000 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.7';
UPDATE "type" SET vendorid='cisco', typename='cisco4700', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='Cisco 4700 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.50';
UPDATE "type" SET vendorid='cisco', typename='cisco7010', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 7010 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.12';
UPDATE "type" SET vendorid='cisco', typename='cisco7204', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 7204 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.125';
UPDATE "type" SET vendorid='cisco', typename='cisco7204VXR', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 7204VXR Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.223';
UPDATE "type" SET vendorid='cisco', typename='cisco7206', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='Cisco 7206 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.108';
UPDATE "type" SET vendorid='cisco', typename='cisco7206VXR', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Cisco 7206VXR Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.222';
UPDATE "type" SET vendorid='cisco', typename='cisco7505', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 7505 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.48';
UPDATE "type" SET vendorid='cisco', typename='cisco7507', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Cisco 7507 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.45';
UPDATE "type" SET vendorid='cisco', typename='cisco7513', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 7513 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.46';
UPDATE "type" SET vendorid='cisco', typename='ciscoAIRAP1130', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Cisco AP 1130' WHERE sysobjectid='1.3.6.1.4.1.9.1.618';
UPDATE "type" SET vendorid='cisco', typename='wsc2980g', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 2980g' WHERE sysobjectid='1.3.6.1.4.1.9.5.49';
UPDATE "type" SET vendorid='cisco', typename='ciscoAIRAP1210', cdp='1', tftp=NULL, cs_at_vlan='0', chassis='1', frequency='3600', descr='Cisco AP 1200' WHERE sysobjectid='1.3.6.1.4.1.9.1.525';
UPDATE "type" SET vendorid='cisco', typename='ciscoAIRAP350IOS', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco AP 350' WHERE sysobjectid='1.3.6.1.4.1.9.1.552';
UPDATE "type" SET vendorid='cisco', typename='ciscoAS5200', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco AS5200' WHERE sysobjectid='1.3.6.1.4.1.9.1.109';
UPDATE "type" SET vendorid='cisco', typename='ciscoVPN3030', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco 3030 VPN concentrator' WHERE sysobjectid='1.3.6.1.4.1.3076.1.2.1.1.1.2';
UPDATE "type" SET vendorid='cisco', typename='ciscoWSX5302', cdp='1', tftp='1', cs_at_vlan=NULL, chassis='1', frequency='3600', descr='Cisco RSM Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.168';
UPDATE "type" SET vendorid='cisco', typename='wsc2926', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 2926 switch' WHERE sysobjectid='1.3.6.1.4.1.9.5.35';
UPDATE "type" SET vendorid='cisco', typename='wsc2980ga', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 2980ga' WHERE sysobjectid='1.3.6.1.4.1.9.5.51';
UPDATE "type" SET vendorid='cisco', typename='wsc4006', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 4006 switch' WHERE sysobjectid='1.3.6.1.4.1.9.5.46';
UPDATE "type" SET vendorid='cisco', typename='wsc5000', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 5000 switch' WHERE sysobjectid='1.3.6.1.4.1.9.5.7';
UPDATE "type" SET vendorid='cisco', typename='wsc5500', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 5500 switch' WHERE sysobjectid='1.3.6.1.4.1.9.5.17';
UPDATE "type" SET vendorid='cisco', typename='wsc5505', cdp='1', tftp='1', cs_at_vlan='1', chassis='1', frequency='3600', descr='Catalyst 5505 switch' WHERE sysobjectid='1.3.6.1.4.1.9.5.34';
UPDATE "type" SET vendorid='cisco', typename='cisco2514', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Cisco 2514 Router' WHERE sysobjectid='1.3.6.1.4.1.9.1.30';
UPDATE "type" SET vendorid='cisco', typename='catalyst295024', cdp='1', tftp='1', cs_at_vlan='1', chassis='0', frequency='3600', descr='Catalyst 2950-24' WHERE sysobjectid='1.3.6.1.4.1.9.1.324';
UPDATE "type" SET vendorid='hp', typename='hp2524', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='ProCurve Switch 2524' WHERE sysobjectid='1.3.6.1.4.1.11.2.3.7.11.19';
UPDATE "type" SET vendorid='hp', typename='hp2626A', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='ProCurve Switch 2626 (J4900A)' WHERE sysobjectid='1.3.6.1.4.1.11.2.3.7.11.34';
UPDATE "type" SET vendorid='hp', typename='hp2626B', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='ProCurve Switch 2626 (J4900B)' WHERE sysobjectid='1.3.6.1.4.1.11.2.3.7.11.45';
UPDATE "type" SET vendorid='hp', typename='hp2650A', cdp='1', tftp='1', cs_at_vlan='0', chassis='1', frequency='3600', descr='ProCurve Switch 2650 (J4899A)' WHERE sysobjectid='1.3.6.1.4.1.11.2.3.7.11.29';
UPDATE "type" SET vendorid='hp', typename='hp2650B', cdp='1', tftp='1', cs_at_vlan='0', chassis='0', frequency='3600', descr='ProCurve Switch 2650 (J4899B)' WHERE sysobjectid='1.3.6.1.4.1.11.2.3.7.11.44';
UPDATE "type" SET vendorid='nortel', typename='nortel5510', cdp='0', tftp='0', cs_at_vlan='0', chassis='0', frequency='3600', descr='Nortel Baystack 5510-48T Switch' WHERE sysobjectid='1.3.6.1.4.1.45.3.53.1';
\echo Don't forget to run types.sql and snmpoid.sql to insert new vendors, types and snmp OIDs into your database
COMMIT;

\echo Granting rights to navread and navwrite for new tables.
\echo If you're running a setup without these users, you can safely ignore 
\echo errors about their non-existance.
SELECT nav_grant('navread', false);
SELECT nav_grant('navwrite', true);

\c navprofiles
BEGIN;
\echo Adding new system account groups to the navprofiles database
INSERT INTO AccountGroup (id, name, descr) VALUES (3, 'Authenticated users', 'Any authenticated user (logged in)');
COMMIT;

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


-- New consolidated interface table
-- See MIB-II, IF-MIB, RFC 1229
CREATE TABLE manage.interface (
  interfaceid SERIAL NOT NULL,
  netboxid INT4 NOT NULL,
  moduleid INT4,
  ifindex INT4 NOT NULL,
  ifname VARCHAR,
  ifdescr VARCHAR,
  iftype INT4,
  speed DOUBLE PRECISION,
  ifphysaddress MACADDR,
  ifadminstatus INT4, 
  ifoperstatus INT4,
  iflastchange INT4,
  ifconnectorpresent BOOLEAN,
  ifpromiscuousmode BOOLEAN,
  ifalias VARCHAR,

  -- non IF-MIB values
  media VARCHAR,
  vlan INT4,
  trunk BOOLEAN,
  duplex CHAR(1) CHECK (duplex='f' OR duplex='h'), -- f=full, h=half

  to_netboxid INT4, 
  to_interfaceid INT4, 

  gone_since TIMESTAMP,
  
  CONSTRAINT interface_pkey PRIMARY KEY (interfaceid),
  CONSTRAINT interface_netboxid_fkey 
             FOREIGN KEY (netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT interface_moduleid_fkey 
             FOREIGN KEY (moduleid)
             REFERENCES module (moduleid)
             ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT interface_to_netboxid_fkey 
             FOREIGN KEY (to_netboxid) 
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT interface_to_interfaceid_fkey 
             FOREIGN KEY (to_interfaceid) 
             REFERENCES interface (interfaceid)
             ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT interface_interfaceid_netboxid_unique
             UNIQUE (interfaceid, netboxid)
);

-- this should be populated with entries parsed from 
-- http://www.iana.org/assignments/ianaiftype-mib
CREATE TABLE manage.iana_iftype (
  iftype INT4 NOT NULL,
  name VARCHAR NOT NULL,
  descr VARCHAR,

  CONSTRAINT iftype_pkey PRIMARY KEY (iftype)
);

-- ---------------------------------------------------------------- --
-- Convert existing swport and gwport records to interface records. --
-- ---------------------------------------------------------------- --

-- First, map old primary keys to new ones. Prime the interfaceid
-- sequence with the max value of the two existing sequences+1000, so
-- we don't create duplicates.
SELECT setval('interface_interfaceid_seq',  GREATEST( nextval('swport_swportid_seq'), nextval('gwport_gwportid_seq'))+1000);

CREATE TEMPORARY TABLE swport_map AS
  SELECT swportid, nextval('interface_interfaceid_seq') AS new_id FROM swport ORDER BY swportid;

CREATE TEMPORARY TABLE gwport_map AS
  SELECT gwportid, nextval('interface_interfaceid_seq') AS new_id FROM gwport ORDER BY gwportid;

UPDATE swport SET swportid=map.new_id FROM swport_map AS map WHERE map.swportid = swport.swportid;
UPDATE gwport SET gwportid=map.new_id FROM gwport_map AS map WHERE map.gwportid = gwport.gwportid;

-- convert swport records
INSERT INTO interface
  SELECT 
    swportid AS interfaceid,
    netboxid, 
    moduleid, 
    ifindex, 
    interface AS ifname,
    interface AS ifdescr, 
    NULL AS iftype,
    speed,
    NULL AS ifphysaddress,
    CASE link WHEN 'd' THEN 2 ELSE 1 END AS ifadminstatus,
    CASE link WHEN 'y' THEN 1 ELSE 2 END AS ifoperstatus,
    NULL AS iflastchange,
    NULL AS ifconnectorpresent,
    NULL AS ifpromiscuousmode,
    portname AS ifalias,
    media,
    vlan,
    trunk,
    duplex,
    to_netboxid,
    to_swportid AS to_interfaceid
  FROM swport 
  JOIN module USING (moduleid);

-- convert gwport records
INSERT INTO interface
  SELECT 
    gwportid AS interfaceid,
    netboxid, 
    moduleid, 
    ifindex, 
    interface AS ifname, 
    interface AS ifdescr, 
    NULL AS iftype,
    speed,
    NULL AS ifphysaddress,
    CASE link WHEN 'd' THEN 2 ELSE 1 END AS ifadminstatus,
    CASE link WHEN 'y' THEN 1 ELSE 2 END AS ifoperstatus,
    NULL AS iflastchange,
    NULL AS ifconnectorpresent,
    NULL AS ifpromiscuousmode,
    portname AS ifalias,
    NULL AS media,
    NULL AS vlan,
    NULL AS trunk,
    NULL AS duplex,
    to_netboxid,
    to_swportid AS to_interfaceid
  FROM gwport 
  JOIN module USING (moduleid);


-- Routing protocol attributes
CREATE TABLE manage.rproto_attr (
  id SERIAL NOT NULL,
  interfaceid INT4 NOT NULL,
  protoname VARCHAR NOT NULL, -- bgp/ospf/isis
  metric INT4,

  CONSTRAINT rproto_attr_pkey 
             PRIMARY KEY (id),
  CONSTRAINT rproto_attr_interfaceid_fkey
             FOREIGN KEY (interfaceid)
             REFERENCES interface (interfaceid)
);

-- Insert any existing OSPF metric values into the new table
INSERT INTO rproto_attr
  SELECT 
    nextval('rproto_attr_id_seq') AS id,
    gwportid AS interfaceid,
    'ospf' AS protoname,
    metric
  FROM gwport WHERE metric IS NOT NULL;

-- Now begins the arduous task of replacing all foreign keys referring
-- to gwport and swport
ALTER TABLE swp_netbox RENAME COLUMN to_swportid TO to_interfaceid;
ALTER TABLE swp_netbox DROP CONSTRAINT "$3";
ALTER TABLE swp_netbox ADD CONSTRAINT swp_netbox_to_interfaceid_fkey 
                                      FOREIGN KEY (to_interfaceid) REFERENCES interface(interfaceid)
                                      ON UPDATE CASCADE ON DELETE SET NULL;
               
ALTER TABLE gwportprefix RENAME COLUMN gwportid TO interfaceid;
ALTER TABLE gwportprefix DROP CONSTRAINT "$1";
ALTER TABLE gwportprefix ADD CONSTRAINT gwportprefix_interfaceid_fkey 
                                        FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                        ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE swportvlan RENAME COLUMN swportid TO interfaceid;
ALTER TABLE swportvlan DROP CONSTRAINT "$1";
ALTER TABLE swportvlan ADD CONSTRAINT swportvlan_interfaceid_fkey 
                                      FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                      ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE swportvlan_swportid_key RENAME TO swportvlan_interfaceid_key;
ALTER TABLE swportvlan_swportid_btree RENAME TO swportvlan_interfaceid_btree;

ALTER TABLE swportallowedvlan RENAME COLUMN swportid TO interfaceid;
ALTER TABLE swportallowedvlan DROP CONSTRAINT "$1";
ALTER TABLE swportallowedvlan ADD CONSTRAINT swportallowedvlan_interfaceid_fkey
                                             FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                             ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE swportblocked RENAME COLUMN swportid TO interfaceid;
ALTER TABLE swportblocked DROP CONSTRAINT "$1";
ALTER TABLE swportblocked ADD CONSTRAINT swportblocked_interfaceid_fkey
                                         FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                         ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE patch RENAME COLUMN swportid TO interfaceid;
ALTER TABLE patch DROP CONSTRAINT "$1";
ALTER TABLE patch ADD CONSTRAINT patch_interfaceid_fkey 
	                         FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                 ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE patch_swportid_key RENAME TO patch_interfaceid_key;

-- Recreate views that depend on swport or gwport
CREATE OR REPLACE VIEW manage.netboxmac AS  
(SELECT DISTINCT ON (mac) netbox.netboxid, arp.mac
 FROM netbox
 JOIN arp ON (arp.arpid = (SELECT arp.arpid FROM arp WHERE arp.ip=netbox.ip AND end_time='infinity' LIMIT 1)))
UNION DISTINCT
(SELECT DISTINCT ON (mac) module.netboxid,mac
 FROM arp
 JOIN gwportprefix gwp ON
  (arp.ip=gwp.gwip AND (hsrp=true OR (SELECT COUNT(*) FROM gwportprefix WHERE gwp.prefixid=gwportprefix.prefixid AND hsrp=true) = 0))
 JOIN interface USING (interfaceid)
 JOIN module USING (moduleid)
 WHERE arp.end_time='infinity');

DROP VIEW allowedvlan_both;
DROP VIEW allowedvlan;

CREATE OR REPLACE VIEW manage.allowedvlan AS
  (SELECT interfaceid,num AS allowedvlan FROM swportallowedvlan CROSS JOIN range
    WHERE num < length(decode(hexstring,'hex'))*8 AND (CASE WHEN length(hexstring)=256
    THEN get_bit(decode(hexstring,'hex'),(num/8)*8+7-(num%8))
    ELSE get_bit(decode(hexstring,'hex'),(length(decode(hexstring,'hex'))*8-num+7>>3<<3)-8+(num%8))
    END)=1);

CREATE OR REPLACE VIEW manage.allowedvlan_both AS
  (select interfaceid,interfaceid as interfaceid2,allowedvlan from allowedvlan ORDER BY allowedvlan) union
  (select  interface.interfaceid,to_interfaceid as interfaceid2,allowedvlan from interface join allowedvlan
    on (interface.to_interfaceid=allowedvlan.interfaceid) ORDER BY allowedvlan);

-- Then, finally, get rid of the old tables
DROP TABLE gwport;
DROP TABLE swport;

-- View to mimic old swport table
CREATE VIEW manage.swport AS (
  SELECT 
    interfaceid AS swportid,
    moduleid,
    ifindex,
    NULL::INT4 AS port,
    ifdescr AS interface,
    CASE ifadminstatus
      WHEN 1 THEN CASE ifoperstatus
                    WHEN 1 THEN 'y'::CHAR
                    ELSE 'n'::char
                  END
      ELSE 'd'::char
    END AS link,
    speed,
    duplex,
    media,
    vlan,
    trunk,
    ifalias AS portname,
    to_netboxid,
    to_interfaceid AS to_swportid
  FROM interface
  WHERE interfaceid NOT IN (SELECT interfaceid FROM gwportprefix)
);

-- View to mimic old gwport table
CREATE VIEW manage.gwport AS (
  SELECT 
    i.interfaceid AS gwportid,
    moduleid,
    ifindex,
    CASE ifadminstatus
      WHEN 1 THEN CASE ifoperstatus
                    WHEN 1 THEN 'y'::CHAR
                    ELSE 'n'::char
                  END
      ELSE 'd'::char
    END AS link,
    NULL::INT4 AS masterindex,
    ifdescr AS interface,
    speed,
    metric,
    ifalias AS portname,
    to_netboxid,
    to_interfaceid AS to_swportid
  FROM interface i
  JOIN gwportprefix gwpfx ON (i.interfaceid=gwpfx.interfaceid)
  LEFT JOIN rproto_attr ra ON (i.interfaceid=ra.interfaceid AND ra.protoname='ospf')
);

COMMIT;

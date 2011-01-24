/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.5 to 3.6.
 *
 * Connect to PostgreSQL as the postgres superuser like this:
 *
 *  psql -f 3.6.0b1.sql nav postgres
 *
 * Or more likely, like this:
 *
 *  sudo -u postgres psql -f 3.6.0b1.sql nav
 *
*/

BEGIN;
-- Insert schema changes here.

-- Force all foreign key constraints to follow the exact same naming
-- pattern: <tablename>_<column_name>_fkey 
--
-- This should change about 7 "wrongly" named foreign keys on the
-- netbox, accountalertqueue and log_message_type tables, and any
-- foreign key whose name has been automatically set to '$<number>' by
-- older versions of PostgreSQL.
SET SESSION AUTHORIZATION postgres; -- This requires superuser access!
UPDATE pg_constraint
SET conname=cl.relname || '_' || pa.attname || '_fkey'
FROM pg_class cl, pg_attribute pa, pg_namespace nsp
WHERE
  contype = 'f' AND
  conname <> (cl.relname || '_' || pa.attname || '_fkey') AND
  connamespace = nsp.oid AND
  nspname IN ('manage', 'profiles', 'arnold', 'logger', 'radius') AND
  conrelid = cl.oid AND
  pa.attrelid = cl.oid AND
  conkey[1] = pa.attnum
;

ALTER TABLE org DROP CONSTRAINT "org_parent_fkey";
ALTER TABLE org ADD CONSTRAINT org_parent_fkey 
                               FOREIGN KEY (parent) REFERENCES org (orgid)
                               ON UPDATE CASCADE;

-- Index to speed up ipdevinfo queries for the first cam entry from a box
CREATE INDEX cam_netboxid_start_time_btree ON cam USING btree (netboxid, start_time);

-- Try to provide consistency between code and db names.
ALTER TABLE alertsubscription RENAME ignore_closed_alerts TO ignore_resolved_alerts;

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
  baseport INT4,
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

CREATE INDEX interface_to_interfaceid_btree ON interface USING btree (to_interfaceid);

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
    port AS baseport,
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
    NULL AS baseport,
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
ALTER TABLE swp_netbox DROP CONSTRAINT swp_netbox_to_swportid_fkey;
ALTER TABLE swp_netbox ADD CONSTRAINT swp_netbox_to_interfaceid_fkey 
                                      FOREIGN KEY (to_interfaceid) REFERENCES interface(interfaceid)
                                      ON UPDATE CASCADE ON DELETE SET NULL;
               
ALTER TABLE gwportprefix RENAME COLUMN gwportid TO interfaceid;
ALTER TABLE gwportprefix DROP CONSTRAINT gwportprefix_gwportid_fkey;
ALTER TABLE gwportprefix ADD CONSTRAINT gwportprefix_interfaceid_fkey 
                                        FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                        ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE gwportprefix_gwportid_btree RENAME TO gwportprefix_interfaceid_btree;

ALTER TABLE swportvlan RENAME COLUMN swportid TO interfaceid;
ALTER TABLE swportvlan DROP CONSTRAINT swportvlan_swportid_fkey;
ALTER TABLE swportvlan ADD CONSTRAINT swportvlan_interfaceid_fkey 
                                      FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                      ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE swportvlan_swportid_key RENAME TO swportvlan_interfaceid_key;
ALTER TABLE swportvlan_swportid_btree RENAME TO swportvlan_interfaceid_btree;

ALTER TABLE swportallowedvlan RENAME COLUMN swportid TO interfaceid;
ALTER TABLE swportallowedvlan DROP CONSTRAINT swportallowedvlan_swportid_fkey;
ALTER TABLE swportallowedvlan ADD CONSTRAINT swportallowedvlan_interfaceid_fkey
                                             FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                             ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE swportblocked RENAME COLUMN swportid TO interfaceid;
ALTER TABLE swportblocked DROP CONSTRAINT swportblocked_swportid_fkey;
ALTER TABLE swportblocked ADD CONSTRAINT swportblocked_interfaceid_fkey
                                         FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                         ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE patch RENAME COLUMN swportid TO interfaceid;
ALTER TABLE patch DROP CONSTRAINT patch_swportid_fkey;
ALTER TABLE patch ADD CONSTRAINT patch_interfaceid_fkey 
	                         FOREIGN KEY (interfaceid) REFERENCES interface(interfaceid)
                                 ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE patch_swportid_key RENAME TO patch_interfaceid_key;

-- Update tables that may reference swport/gwport without proper referential integrity
UPDATE rrd_file
SET key='interface', value=map.new_id::text 
FROM swport_map AS map
WHERE rrd_file.key = 'swport' AND rrd_file.value::integer = map.swportid;

UPDATE rrd_file
SET key='interface', value=map.new_id::text 
FROM gwport_map AS map
WHERE rrd_file.key = 'gwport' AND rrd_file.value::integer = map.gwportid;

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

-- Drop unnecessary table and update the corresponding allowedvlan view
DROP TABLE manage.range;
CREATE OR REPLACE VIEW allowedvlan AS (
  SELECT 
    interfaceid, vlan AS allowedvlan 
  FROM 
    (SELECT interfaceid, decode(hexstring, 'hex') AS octetstring 
     FROM swportallowedvlan) AS allowed_octets
  CROSS JOIN
    generate_series(0, 4095) AS vlan
  WHERE
    vlan < length(octetstring)*8 AND
    (CASE 
       WHEN length(octetstring)>=128 
         THEN get_bit(octetstring, (vlan/8)*8+7-(vlan%8))
       ELSE get_bit(octetstring,(length(octetstring)*8-vlan+7>>3<<3)-8+(vlan%8))
     END) = 1
);


CREATE OR REPLACE VIEW manage.allowedvlan_both AS
  (select interfaceid,interfaceid as interfaceid2,allowedvlan from allowedvlan ORDER BY allowedvlan) union
  (select  interface.interfaceid,to_interfaceid as interfaceid2,allowedvlan from interface join allowedvlan
    on (interface.to_interfaceid=allowedvlan.interfaceid) ORDER BY allowedvlan);

-- Then, finally, get rid of the old tables
DROP TABLE gwport;
DROP TABLE swport;

-- View to mimic old swport table
CREATE OR REPLACE VIEW manage.swport AS (
  SELECT 
    interfaceid AS swportid,
    moduleid,
    ifindex,
    baseport AS port,
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
CREATE OR REPLACE VIEW manage.gwport AS (
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

-- View to see only switch ports
CREATE OR REPLACE VIEW manage.interface_swport AS (
  SELECT
    interface.*,
    CASE ifadminstatus
      WHEN 1 THEN CASE ifoperstatus
                    WHEN 1 THEN 'y'::CHAR
                    ELSE 'n'::char
                  END
      ELSE 'd'::char
    END AS link
  FROM
    interface
  WHERE
    baseport IS NOT NULL
);

-- View to see only router ports
CREATE OR REPLACE VIEW manage.interface_gwport AS (
  SELECT
    interface.*,
    CASE ifadminstatus
      WHEN 1 THEN CASE ifoperstatus
                    WHEN 1 THEN 'y'::CHAR
                    ELSE 'n'::char
                  END
      ELSE 'd'::char
    END AS link
  FROM
    interface
  JOIN
    (SELECT interfaceid FROM gwportprefix GROUP BY interfaceid) routerports USING (interfaceid)
);


-- Modules aren't necessarily identified using integers, so we add names.
ALTER TABLE module ALTER COLUMN module DROP NOT NULL;
ALTER TABLE module ADD COLUMN name VARCHAR;
ALTER TABLE module DROP CONSTRAINT module_netboxid_key;
UPDATE module SET name = module::text;
ALTER TABLE module ALTER COLUMN name SET NOT NULL;
ALTER TABLE module ADD CONSTRAINT module_netboxid_key UNIQUE (netboxid, name);


-- Add netbox updating rules to snmpoid
CREATE RULE reprofile_netboxes_on_snmpoid_insert
  AS ON INSERT TO snmpoid
  DO ALSO
    UPDATE netbox SET uptodate=false;

CREATE RULE reprofile_netboxes_on_snmpoid_update
  AS ON UPDATE TO snmpoid
  DO ALSO
    UPDATE netbox SET uptodate=false;

DELETE FROM netboxsnmpoid;
ALTER TABLE netboxsnmpoid ALTER COLUMN netboxid SET NOT NULL;
ALTER TABLE netboxsnmpoid ALTER COLUMN snmpoidid SET NOT NULL;


-- Remove product and deviceorder
ALTER TABLE device DROP COLUMN productid;
ALTER TABLE device DROP COLUMN deviceorderid;
ALTER TABLE device DROP COLUMN active;

DROP TABLE deviceorder;
DROP TABLE product;

-- Django needs a simple integer primary key in accountnavbar
ALTER TABLE accountnavbar DROP CONSTRAINT accountnavbar_pkey;
CREATE SEQUENCE profiles.accountnavbar_id_seq;
ALTER TABLE accountnavbar ADD COLUMN id integer NOT NULL PRIMARY KEY DEFAULT nextval('accountnavbar_id_seq');

-- Status preference tables
CREATE SEQUENCE profiles.statuspreference_id_seq START 1000;
CREATE TABLE profiles.statuspreference (
	id integer NOT NULL DEFAULT nextval('statuspreference_id_seq'),
	name varchar NOT NULL,
	position integer NOT NULL,
	type varchar NOT NULL,
	accountid integer NOT NULL,

	services varchar NOT NULL DEFAULT '',
	states varchar NOT NULL DEFAULT 'n,s',

	CONSTRAINT statuspreference_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_accountid_fkey
		FOREIGN KEY (accountid) REFERENCES Account(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE statuspref_id_seq OWNED BY statuspref.id;

CREATE SEQUENCE profiles.statuspreference_organization_id_seq;
CREATE TABLE profiles.statuspreference_organization (
	id integer NOT NULL DEFAULT nextval('statuspreference_organization_id_seq'),
	statuspreference_id integer NOT NULL,
	organization_id varchar NOT NULL,

	CONSTRAINT statuspreference_organization_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_organization_statuspreference_id_key
		UNIQUE(statuspreference_id, organization_id),
	CONSTRAINT statuspreference_organization_statuspreference_id_fkey
		FOREIGN KEY (statuspreference_id) REFERENCES statuspreference(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT statuspreference_organization_organization_id_fkey
		FOREIGN KEY (organization_id) REFERENCES manage.org(orgid)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE statuspref_org_id_seq OWNED BY statuspref_org.id;

CREATE SEQUENCE profiles.statuspreference_category_id_seq;
CREATE TABLE profiles.statuspreference_category (
	id integer NOT NULL DEFAULT nextval('statuspreference_category_id_seq'),
	statuspreference_id integer NOT NULL,
	category_id varchar NOT NULL,

	CONSTRAINT statuspreference_category_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_category_statuspreference_id_key
		UNIQUE(statuspreference_id, category_id),
	CONSTRAINT statuspreference_category_statuspreference_id_fkey
		FOREIGN KEY (statuspreference_id) REFERENCES statuspreference(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT statuspreference_category_category_id_fkey
		FOREIGN KEY (category_id) REFERENCES manage.cat(catid)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE statuspreference_category_id_seq OWNED BY statuspreference_category.id;

-- StatusPreferences for Default user

INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (1, 'IP devices down', 1, 'netbox', 0, 'n');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (2, 'IP devices in shadow', 2, 'netbox', 0, 's');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (3, 'IP devices on maintenance', 3, 'netbox_maintenance', 0, 'n,s');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (4, 'Modules down/in shadow', 4, 'module', 0, 'n,s');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (5, 'Services down', 5, 'service', 0, 'n,s');


-- DeviceHistory rewrite 
-- Django needs an id field for every table.
--
CREATE SEQUENCE manage.eventqvar_id_seq;
ALTER TABLE eventqvar ADD COLUMN id integer NOT NULL
	DEFAULT nextval('eventqvar_id_seq')
	CONSTRAINT eventqvar_pkey PRIMARY KEY;


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

-- Change type on arnold.identity.mac from varchar to macaddr
ALTER TABLE identity ALTER mac TYPE macaddr USING mac::macaddr;

-- Add foreign key to accountalertqueue.alert_id LP#494036
ALTER TABLE accountalertqueue ADD CONSTRAINT accountalertqueue_alert_id_fkey
    FOREIGN KEY(alert_id) REFERENCES alertq(alertqid);

-- View to match each netbox with a prefix
-- Multiple prefixes may match netbox.ip, but only the one with the longest
-- mask is interesting.
CREATE VIEW netboxprefix AS
  SELECT netbox.netboxid,
         (SELECT prefix.prefixid
          FROM prefix
          WHERE netbox.ip << prefix.netaddr::inet
          ORDER BY masklen(prefix.netaddr::inet) DESC
          LIMIT 1) AS prefixid
  FROM netbox;

-- Function to update prefix of all netbox records
CREATE OR REPLACE FUNCTION update_netbox_prefixes() RETURNS TRIGGER AS'
  BEGIN
    UPDATE NETBOX n
    SET prefixid=np.prefixid
    FROM netboxprefix np
    WHERE n.netboxid=np.netboxid;

    RETURN NULL;
  END;
  ' language 'plpgsql';

-- Trigger to update netbox prefixid's on all changes to the prefix table
CREATE TRIGGER update_netbox_on_prefix_changes
  AFTER INSERT OR DELETE OR UPDATE ON prefix FOR EACH STATEMENT EXECUTE PROCEDURE update_netbox_prefixes();


-- Since we are running as the postgres superuser, we've just created a bunch
-- of new relations owned by postgres, and not by the current database owner.
-- This finds any relation in the NAV namespaces that is owned by the postgres
-- superuser, and resets their ownership to the database owner.
UPDATE pg_class
   SET relowner = (SELECT datdba FROM pg_database  WHERE datname=current_database())
 WHERE relowner = (SELECT usesysid
                   FROM pg_user
		   WHERE usename='postgres' AND 
		         relnamespace IN (SELECT oid 
			                  FROM pg_namespace 
					  WHERE nspname IN ('manage', 'arnold', 'logger', 'radius', 'profiles')));

-- Insert event and alerttypes for airespace traphandler
INSERT INTO eventtype (
SELECT 'apState','Tells us whether an access point has disassociated or associated from the controller','y' WHERE NOT EXISTS (
SELECT * FROM eventtype WHERE eventtypeid = 'apState'));

INSERT INTO alertType (
SELECT nextval('alerttype_alerttypeid_seq'), 'apState', 'apUp', 'AP associated with controller' WHERE NOT EXISTS (
SELECT * FROM alerttype WHERE alerttype = 'apUp'));

INSERT INTO alertType (
SELECT nextval('alerttype_alerttypeid_seq'), 'apState', 'apDown', 'AP disassociated from controller' WHERE NOT EXISTS (
SELECT * FROM alerttype WHERE alerttype = 'apDown'));


-- Insert the new version number if we got this far.
INSERT INTO nav_schema_version (version) VALUES ('3.6.0b1');
COMMIT;

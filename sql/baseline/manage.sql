/*
=============================================
        manage
    SQL Initialization script for NAV's
    manage database.  Read the README file
    for more info.
    
    Run the command:
    psql manage -f manage.sql
    
	!! WARNING !!

	This SQL script is encoded as unicode (UTF-8), before you do make
	changes and commit, be 100% sure that your editor does not mess it up.
    
    Check 1 : These norwegian letters looks nice:
    ! æøåÆØÅ !
    Check 2 : This is the Euro currency sign: 
    ! € !
=============================================
*/

-- This table has possibly gone unused since NAV 2
CREATE TABLE status (
  statusid SERIAL PRIMARY KEY,
  trapsource VARCHAR NOT NULL,
  trap VARCHAR NOT NULL,
  trapdescr VARCHAR,
  tilstandsfull CHAR(1) CHECK (tilstandsfull='Y' OR tilstandsfull='N') NOT NULL,
  boksid INT2,
  fra TIMESTAMP NOT NULL,
  til TIMESTAMP
);

CREATE TABLE org (
  orgid VARCHAR(30) PRIMARY KEY,
  parent VARCHAR(30),
  descr VARCHAR,
  contact VARCHAR,
  opt1 VARCHAR,
  opt2 VARCHAR,
  opt3 VARCHAR,
  CONSTRAINT org_parent_fkey FOREIGN KEY (parent) REFERENCES org (orgid)
             ON UPDATE CASCADE
);
INSERT INTO org (orgid, descr, contact) VALUES ('myorg', 'Example organization unit', 'nobody');

CREATE TABLE usage (
  usageid VARCHAR(30) PRIMARY KEY,
  descr VARCHAR NOT NULL
);


CREATE TABLE location (
  locationid VARCHAR(30) PRIMARY KEY,
  descr VARCHAR NOT NULL
);
INSERT INTO location (locationid, descr) VALUES ('mylocation', 'Example location');

CREATE TABLE room (
  roomid VARCHAR(30) PRIMARY KEY,
  locationid VARCHAR(30) REFERENCES location,
  descr VARCHAR,
  opt1 VARCHAR,
  opt2 VARCHAR,
  opt3 VARCHAR,
  opt4 VARCHAR,
  position POINT
);
INSERT INTO room (roomid, locationid, descr) VALUES ('myroom', 'mylocation', 'Example wiring closet');

CREATE TABLE nettype (
  nettypeid VARCHAR PRIMARY KEY,
  descr VARCHAR,
  edit BOOLEAN DEFAULT FALSE
);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('core','core',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('dummy','dummy',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('elink','elink',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('lan','lan',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('link','link',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('loopback','loopbcak',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('reserved','reserved',TRUE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('private','private',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('scope','scope',TRUE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('static','static',FALSE);
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('unknown','unknow',FALSE);

CREATE TABLE vlan (
  vlanid SERIAL PRIMARY KEY,
  vlan INT4,
  nettype VARCHAR NOT NULL REFERENCES nettype(nettypeid) ON UPDATE CASCADE ON DELETE CASCADE,
  orgid VARCHAR(30) REFERENCES org,
  usageid VARCHAR(30) REFERENCES usage,
  netident VARCHAR,
  description VARCHAR
);  

CREATE TABLE prefix (
  prefixid SERIAL PRIMARY KEY,
  netaddr CIDR NOT NULL,
  vlanid INT4 REFERENCES vlan ON UPDATE CASCADE ON DELETE CASCADE,
  UNIQUE(netaddr)
);

CREATE TABLE vendor (
  vendorid VARCHAR(15) PRIMARY KEY
);

CREATE TABLE cat (
  catid VARCHAR(8) PRIMARY KEY,
  descr VARCHAR,
  req_snmp BOOLEAN NOT NULL
);

INSERT INTO cat values ('GW','Routers (layer 3 device)','t');
INSERT INTO cat values ('GSW','A layer 2 and layer 3 device','t');
INSERT INTO cat values ('SW','Core switches (layer 2), typically with many vlans','t');
INSERT INTO cat values ('EDGE','Edge switch without vlans (layer 2)','t');
INSERT INTO cat values ('WLAN','Wireless equipment','t');
INSERT INTO cat values ('SRV','Server','f');
INSERT INTO cat values ('OTHER','Other equipment','f');

CREATE TABLE device (
  deviceid SERIAL PRIMARY KEY,
  serial VARCHAR,
  hw_ver VARCHAR,
  fw_ver VARCHAR,
  sw_ver VARCHAR,
  discovered TIMESTAMP NULL DEFAULT NOW(),
  UNIQUE(serial)
);

CREATE TABLE type (
  typeid SERIAL PRIMARY KEY,
  vendorid VARCHAR(15) NOT NULL REFERENCES vendor ON UPDATE CASCADE ON DELETE CASCADE,
  typename VARCHAR NOT NULL,
  sysObjectID VARCHAR NOT NULL,
  cdp BOOL DEFAULT false,
  tftp BOOL DEFAULT false,
  cs_at_vlan BOOL,
  chassis BOOL NOT NULL DEFAULT true,
  descr VARCHAR,
  UNIQUE (vendorid, typename),
  UNIQUE (sysObjectID)
);

CREATE TABLE snmpoid (
  snmpoidid SERIAL PRIMARY KEY,
  oidkey VARCHAR NOT NULL,
  snmpoid VARCHAR NOT NULL,
  oidsource VARCHAR,
  getnext BOOLEAN NOT NULL DEFAULT true,
  decodehex BOOLEAN NOT NULL DEFAULT false,
  match_regex VARCHAR,
  defaultfreq INT4 NOT NULL DEFAULT 21600,
  uptodate BOOLEAN NOT NULL DEFAULT false,
  descr VARCHAR,
  oidname VARCHAR,
  mib VARCHAR,
  UNIQUE(oidkey)
);

CREATE TABLE netbox (
  netboxid SERIAL PRIMARY KEY,
  ip INET NOT NULL,
  roomid VARCHAR(30) NOT NULL CONSTRAINT netbox_roomid_fkey REFERENCES room ON UPDATE CASCADE,
  typeid INT4 CONSTRAINT netbox_typeid_fkey REFERENCES type ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 NOT NULL CONSTRAINT netbox_deviceid_fkey REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  sysname VARCHAR UNIQUE NOT NULL,
  catid VARCHAR(8) NOT NULL CONSTRAINT netbox_catid_fkey REFERENCES cat ON UPDATE CASCADE ON DELETE CASCADE,
  orgid VARCHAR(30) NOT NULL CONSTRAINT netbox_orgid_fkey REFERENCES org ON UPDATE CASCADE,
  ro VARCHAR,
  rw VARCHAR,
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n' OR up='s'), -- y=up, n=down, s=shadow
  snmp_version INT4 NOT NULL DEFAULT 1,
  upsince TIMESTAMP NOT NULL DEFAULT NOW(),
  uptodate BOOLEAN NOT NULL DEFAULT false, 
  discovered TIMESTAMP NULL DEFAULT NOW(),
  UNIQUE(ip),
  UNIQUE(deviceid)
);

-- These rules make sure to invalidate all netbox SNMP profiles when
-- new snmpoids are inserted, or existing ones updated.
CREATE RULE reprofile_netboxes_on_snmpoid_insert
  AS ON INSERT TO snmpoid
  DO ALSO
    UPDATE netbox SET uptodate=false;

CREATE RULE reprofile_netboxes_on_snmpoid_update
  AS ON UPDATE TO snmpoid
  DO ALSO
    UPDATE netbox SET uptodate=false;

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

CREATE TABLE netboxsnmpoid (
  id SERIAL,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  snmpoidid INT4 NOT NULL REFERENCES snmpoid ON UPDATE CASCADE ON DELETE CASCADE,
  frequency INT4,
  PRIMARY KEY(id),
  UNIQUE(netboxid, snmpoidid)
);  

CREATE TABLE netbox_vtpvlan (
  id SERIAL,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  vtpvlan INT4,
  PRIMARY KEY(id),
  UNIQUE(netboxid, vtpvlan)
);

CREATE TABLE subcat (
    subcatid VARCHAR,
    descr VARCHAR NOT NULL,
    catid VARCHAR(8) NOT NULL REFERENCES cat(catid),
    PRIMARY KEY (subcatid)
);
INSERT INTO subcat (subcatid,descr,catid) VALUES ('AD','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('ADC','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('BACKUP','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('DNS','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('FS','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('LDAP','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('MAIL','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('NOTES','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('STORE','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('TEST','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('UNIX','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('UNIX-STUD','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('WEB','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('WIN','Description','SRV');
INSERT INTO subcat (subcatid,descr,catid) VALUES ('WIN-STUD','Description','SRV'
);

CREATE TABLE netboxcategory (
  id SERIAL,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  category VARCHAR NOT NULL REFERENCES subcat ON UPDATE CASCADE ON DELETE CASCADE,
  PRIMARY KEY(netboxid, category)
);


CREATE TABLE netboxinfo (
  netboxinfoid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  key VARCHAR,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  UNIQUE(netboxid, key, var, val)
);

CREATE TABLE module (
  moduleid SERIAL PRIMARY KEY,
  deviceid INT4 NOT NULL REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  module INT4,
  name VARCHAR NOT NULL,
  model VARCHAR,
  descr VARCHAR,
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n'), -- y=up, n=down
  downsince TIMESTAMP,
  CONSTRAINT module_netboxid_key UNIQUE (netboxid, name),
  UNIQUE(deviceid)
);

CREATE TABLE mem (
  memid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  memtype VARCHAR NOT NULL,
  device VARCHAR NOT NULL,
  size INT4 NOT NULL,
  used INT4,
  UNIQUE(netboxid, memtype, device)
);


-- New consolidated interface table
-- See MIB-II, IF-MIB, RFC 1229
CREATE TABLE interface (
  interfaceid SERIAL NOT NULL,
  netboxid INT4 NOT NULL,
  moduleid INT4,
  ifindex INT4,
  ifname VARCHAR,
  ifdescr VARCHAR,
  iftype INT4,
  speed DOUBLE PRECISION,
  ifphysaddress MACADDR,
  ifadminstatus INT4, -- 1=up, 2=down, 3=testing
  ifoperstatus INT4,  -- 1=up, 2=down, 3=testing, 4=unknown, 5=dormant, 6=notPresent, 7=lowerLayerDown
  iflastchange INT4,
  ifconnectorpresent BOOLEAN,
  ifpromiscuousmode BOOLEAN,
  ifalias VARCHAR,

  -- non IF-MIB values
  baseport INT4,  -- baseport number from BRIDGE-MIB, if any. 
                  -- A non-null value should be a good indicator that this is a switch port.
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
  CONSTRAINT interface_netboxid_ifindex_unique
             UNIQUE (netboxid, ifindex)
);

-- this should be populated with entries parsed from 
-- http://www.iana.org/assignments/ianaiftype-mib
CREATE TABLE iana_iftype (
  iftype INT4 NOT NULL,
  name VARCHAR NOT NULL,
  descr VARCHAR,

  CONSTRAINT iftype_pkey PRIMARY KEY (iftype)
);

CREATE TABLE gwportprefix (
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  prefixid INT4 NOT NULL REFERENCES prefix ON UPDATE CASCADE ON DELETE CASCADE,
  gwip INET NOT NULL,
  hsrp BOOL NOT NULL DEFAULT false,
  UNIQUE(gwip)
);

-- Routing protocol attributes
CREATE TABLE rproto_attr (
  id SERIAL NOT NULL,
  interfaceid INT4 NOT NULL,
  protoname VARCHAR NOT NULL, -- bgp/ospf/isis
  metric INT4,

  CONSTRAINT rproto_attr_pkey 
             PRIMARY KEY (id),
  CONSTRAINT rproto_attr_interfaceid_fkey
             FOREIGN KEY (interfaceid)
             REFERENCES interface (interfaceid)
             ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE swportvlan (
  swportvlanid SERIAL PRIMARY KEY,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  vlanid INT4 NOT NULL REFERENCES vlan ON UPDATE CASCADE ON DELETE CASCADE,
  direction CHAR(1) NOT NULL DEFAULT 'x', -- u=up, n=down, x=undefined?
  UNIQUE (interfaceid, vlanid)
);

CREATE TABLE swportallowedvlan (
  interfaceid INT4 NOT NULL PRIMARY KEY REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  hexstring VARCHAR
);


CREATE TABLE swportblocked (
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT4 NOT NULL,
  PRIMARY KEY(interfaceid, vlan)
);

-- View to mimic old swport table
CREATE VIEW swport AS (
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
CREATE VIEW gwport AS (
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
CREATE VIEW interface_swport AS (
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
CREATE VIEW interface_gwport AS (
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

CREATE TABLE cabling (
  cablingid SERIAL PRIMARY KEY,
  roomid VARCHAR(30) NOT NULL REFERENCES room ON UPDATE CASCADE ON DELETE CASCADE,
  jack VARCHAR NOT NULL,
  building VARCHAR NOT NULL,
  targetroom VARCHAR NOT NULL,
  descr VARCHAR,
  category VARCHAR NOT NULL,
UNIQUE(roomid,jack));

CREATE TABLE patch (
  patchid SERIAL PRIMARY KEY,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  cablingid INT4 NOT NULL REFERENCES cabling ON UPDATE CASCADE ON DELETE CASCADE,
  split VARCHAR NOT NULL DEFAULT 'no',
UNIQUE(interfaceid,cablingid));

-- Remove floating devices.
-- Devices that don't have a serial and no connected modules or netboxes.
-- Triggers on delete on module and netbox.
CREATE OR REPLACE FUNCTION remove_floating_devices() RETURNS TRIGGER AS '
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


------------------------------------------------------------------
------------------------------------------------------------------


CREATE TABLE arp (
  arpid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  prefixid INT4 REFERENCES prefix ON UPDATE CASCADE ON DELETE SET NULL,
  sysname VARCHAR NOT NULL,
  ip INET NOT NULL,
  mac MACADDR NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL DEFAULT 'infinity'
);

-- Rule to automatically close open arp entries related to a given prefix
CREATE OR REPLACE RULE close_arp_prefices AS ON DELETE TO prefix
  DO UPDATE arp SET end_time=NOW(), prefixid=NULL 
     WHERE prefixid=OLD.prefixid AND end_time='infinity';

-- View for listing all IP addresses that appear to be alive at the moment.
CREATE OR REPLACE VIEW manage.live_clients AS
  SELECT arp.ip, arp.mac
    FROM arp
   WHERE arp.end_time = 'infinity';

CREATE TABLE cam (
  camid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  sysname VARCHAR NOT NULL,
  ifindex INT4 NOT NULL,
  module VARCHAR(4),
  port VARCHAR,
  mac MACADDR NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL DEFAULT 'infinity',
  misscnt INT4 DEFAULT '0',
  UNIQUE(netboxid,sysname,module,port,mac,start_time)
);


-- Rules to automatically close open cam and arp entries related to a given netbox
CREATE OR REPLACE RULE netbox_close_arp AS ON DELETE TO netbox
  DO UPDATE arp SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';

CREATE OR REPLACE RULE netbox_close_cam AS ON DELETE TO netbox
  DO UPDATE cam SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';


-- VIEWs -----------------------
CREATE VIEW netboxmac AS  
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

CREATE VIEW prefix_active_ip_cnt AS
(SELECT prefix.prefixid, COUNT(arp.ip) AS active_ip_cnt
 FROM prefix
 LEFT JOIN arp ON arp.ip << prefix.netaddr
 WHERE arp.end_time = 'infinity'
 GROUP BY prefix.prefixid);

CREATE VIEW prefix_max_ip_cnt AS
(SELECT prefixid,
  CASE POW(2,32-MASKLEN(netaddr))-2 WHEN -1 THEN 0
   ELSE
  POW(2,32-MASKLEN(netaddr))-2 END AS max_ip_cnt
 FROM prefix);

-- This view gives the allowed vlan for a given hexstring i swportallowedvlan
CREATE VIEW allowedvlan AS (
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

CREATE VIEW allowedvlan_both AS
  (select interfaceid,interfaceid as interfaceid2,allowedvlan from allowedvlan ORDER BY allowedvlan) union
  (select  interface.interfaceid,to_interfaceid as interfaceid2,allowedvlan from interface join allowedvlan
    on (interface.to_interfaceid=allowedvlan.interfaceid) ORDER BY allowedvlan);

------------------------------------------------------------------------------
-- rrd metadb tables
------------------------------------------------------------------------------

-- This table contains the different systems that has rrd-data.
-- Replaces table eventprocess
CREATE TABLE subsystem (
  name      VARCHAR PRIMARY KEY, -- name of the system, e.g. Cricket
  descr     VARCHAR  -- description of the system
);

INSERT INTO subsystem (name) VALUES ('eventEngine');
INSERT INTO subsystem (name) VALUES ('pping');
INSERT INTO subsystem (name) VALUES ('serviceping');
INSERT INTO subsystem (name) VALUES ('moduleMon');
INSERT INTO subsystem (name) VALUES ('thresholdMon');
INSERT INTO subsystem (name) VALUES ('trapParser');
INSERT INTO subsystem (name) VALUES ('cricket');
INSERT INTO subsystem (name) VALUES ('deviceManagement');
INSERT INTO subsystem (name) VALUES ('getDeviceData');
INSERT INTO subsystem (name) VALUES ('devBrowse');
INSERT INTO subsystem (name) VALUES ('maintenance');
INSERT INTO subsystem (name) VALUES ('snmptrapd');

-- Each rrdfile should be registered here. We need the path to find it,
-- and also a link to which unit or service it has data about to easily be
-- able to select all relevant files to a unit or service. Key and value
-- are meant to be combined and thereby point to a specific row in the db.
CREATE TABLE rrd_file (
  rrd_fileid    SERIAL PRIMARY KEY,
  path      VARCHAR NOT NULL, -- complete path to the rrdfile
  filename  VARCHAR NOT NULL, -- name of the rrdfile (including the .rrd)
  step      INT, -- the number of seconds between each update
  subsystem VARCHAR REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid  INT REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  key       VARCHAR,
  value     VARCHAR,
  CONSTRAINT rrd_file_path_filename_key UNIQUE (path, filename)
);

-- Each datasource for each rrdfile is registered here. We need the name and
-- desc for instance in Cricket. Cricket has the name ds0, ds1 and so on, and
-- to understand what that is for humans we need the descr.
CREATE TABLE rrd_datasource (
  rrd_datasourceid  SERIAL PRIMARY KEY,
  rrd_fileid        INT REFERENCES rrd_file ON UPDATE CASCADE ON DELETE CASCADE,
  name          VARCHAR, -- name of the datasource in the file
  descr         VARCHAR, -- human-understandable name of the datasource
  dstype        VARCHAR CHECK (dstype='GAUGE' OR dstype='DERIVE' OR dstype='COUNTER' OR dstype='ABSOLUTE'),
  units         VARCHAR, -- textual decription of the y-axis (percent, kilo, giga, etc.)
  threshold VARCHAR,
  max   VARCHAR,
  delimiter CHAR(1) CHECK (delimiter='>' OR delimiter='<'),
  thresholdstate VARCHAR CHECK (thresholdstate='active' OR thresholdstate='inactive')
);


-- 
CREATE VIEW rrddatasourcenetbox AS
(SELECT DISTINCT rrd_datasource.descr, rrd_datasource.rrd_datasourceid, sysname
  FROM rrd_datasource
  JOIN rrd_file USING (rrd_fileid)
  JOIN netbox USING (netboxid));

------------------------------------------------------------------------------------------
-- event system tables
------------------------------------------------------------------------------------------

-- event tables
CREATE TABLE eventtype (
  eventtypeid VARCHAR(32) PRIMARY KEY,
  eventtypedesc VARCHAR,
  stateful CHAR(1) NOT NULL CHECK (stateful='y' OR stateful='n')
);
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES 
  ('boxState','Tells us whether a network-unit is down or up.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES 
  ('serviceState','Tells us whether a service on a server is up or down.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('moduleState','Tells us whether a module in a device is working or not.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('thresholdState','Tells us whether the load has passed a certain threshold.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('linkState','Tells us whether a link is up or down.','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('boxRestart','Tells us that a network-unit has done a restart','n');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('info','Basic information','n');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
  ('notification','Notification event, typically between NAV systems','n');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('deviceActive','Lifetime event for a device','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('deviceState','Registers the state of a device','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('deviceNotice','Registers a notice on a device','n');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('maintenanceState','Tells us if something is set on maintenance','y');
INSERT INTO eventtype (eventtypeid,eventtypedesc,stateful) VALUES
    ('apState','Tells us whether an access point has disassociated or associated from the controller','y');

CREATE TABLE eventq (
  eventqid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  target VARCHAR(32) NOT NULL REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  subid VARCHAR,
  time TIMESTAMP NOT NULL DEFAULT NOW (),
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL DEFAULT 'x' CHECK (state='x' OR state='s' OR state='e'), -- x = stateless, s = start, e = end
  value INT4 NOT NULL DEFAULT '100',
  severity INT4 NOT NULL DEFAULT '50'
);

CREATE SEQUENCE eventqvar_id_seq;
CREATE TABLE eventqvar (
  id integer NOT NULL DEFAULT nextval('eventqvar_id_seq'),
  eventqid INT4 REFERENCES eventq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,

  CONSTRAINT eventqvar_pkey PRIMARY KEY(id),
  CONSTRAINT eventqvar_eventqid_key UNIQUE(eventqid, var) -- only one val per var per event
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE eventqvar_id_seq OWNED BY eventqvar.id;



-- alert tables

CREATE TABLE alerttype (
  alerttypeid SERIAL PRIMARY KEY,
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  alerttype VARCHAR,
  alerttypedesc VARCHAR,
  CONSTRAINT alerttype_eventalert_unique UNIQUE (eventtypeid, alerttype)
);
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxDownWarning','Warning sent before declaring the box down.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxShadowWarning','Warning sent before declaring the box in shadow.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxDown','Box declared down.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxUp','Box declared up.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxShadow','Box declared down, but is in shadow.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxState','boxSunny','Box declared up from a previous shadow state.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('moduleState','moduleDownWarning','Warning sent before declaring the module down.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('moduleState','moduleDown','Module declared down.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('moduleState','moduleUp','Module declared up.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('serviceState','httpDown','http service not responding.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('serviceState','httpUp','http service responding.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('maintenanceState','onMaintenance','Box put on maintenance.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('maintenanceState','offMaintenance','Box taken off maintenance.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('thresholdState','exceededThreshold','Threshold exceeded.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('thresholdState','belowThreshold','Value below threshold.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('info','dnsMismatch','Mismatch between sysname and dnsname.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('info','serialChanged','Serial number for the device has changed.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxRestart','coldStart','Tells us that a network-unit has done a coldstart.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('boxRestart','warmStart','Tells us that a network-unit has done a warmstart.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceInIPOperation','Device is in operation as a box.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceInStack','Device is in operation as a module.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceState','deviceRMA','RMA event for device.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceNotice','deviceError','Error situation on device.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceNotice','deviceSwUpgrade','Software upgrade on device.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('deviceNotice','deviceHwUpgrade','Hardware upgrade on device.');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('apState','apUp','AP associated with controller');
INSERT INTO alerttype (eventtypeid,alerttype,alerttypedesc) VALUES
  ('apState','apDown','AP disassociated from controller');

CREATE TABLE alerthist (
  alerthistid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  subid VARCHAR,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP DEFAULT 'infinity',
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  alerttypeid INT4 REFERENCES alerttype ON UPDATE CASCADE ON DELETE CASCADE,
  value INT4 NOT NULL,
  severity INT4 NOT NULL
);

-- Rule to automatically close module related alert states when modules are
-- deleted.
CREATE OR REPLACE RULE close_alerthist_modules AS ON DELETE TO module
  DO UPDATE alerthist SET end_time=NOW() 
     WHERE eventtypeid IN ('moduleState', 'linkState')
       AND end_time='infinity'
       AND deviceid=OLD.deviceid;

CREATE TABLE alerthistmsg (
  id SERIAL,
  alerthistid INT4 REFERENCES alerthist ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  msgtype VARCHAR NOT NULL,
  language VARCHAR NOT NULL,
  msg TEXT NOT NULL,
  PRIMARY KEY(id),
  UNIQUE(alerthistid, state, msgtype, language)
);

CREATE TABLE alerthistvar (
  id SERIAL,
  alerthistid INT4 REFERENCES alerthist ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  PRIMARY KEY(id),
  UNIQUE(alerthistid, state, var) -- only one val per var per state per alert
);


CREATE TABLE alertq (
  alertqid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES subsystem (name) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  subid VARCHAR,
  time TIMESTAMP NOT NULL,
  eventtypeid VARCHAR(32) REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  alerttypeid INT4 REFERENCES alerttype ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  value INT4 NOT NULL,
  severity INT4 NOT NULL,
  alerthistid INTEGER NULL,
  CONSTRAINT alertq_alerthistid_fkey FOREIGN KEY (alerthistid) REFERENCES alerthist (alerthistid)
             ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE alertqmsg (
  id SERIAL,
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  msgtype VARCHAR NOT NULL,
  language VARCHAR NOT NULL,
  msg TEXT NOT NULL,
  PRIMARY KEY(id),
  UNIQUE(alertqid, msgtype, language)
);

CREATE TABLE alertqvar (
  id SERIAL,
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  PRIMARY KEY(id),
  UNIQUE(alertqid, var) -- only one val per var per event
);


------------------------------------------------------------------------------
-- servicemon tables
------------------------------------------------------------------------------

CREATE TABLE service (
  serviceid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  active BOOL DEFAULT true,
  handler VARCHAR,
  version VARCHAR,
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n' OR up='s') -- y=up, n=down, s=shadow
);
CREATE RULE rrdfile_deleter AS 
    ON DELETE TO service 
    DO DELETE FROM rrd_file 
        WHERE key='serviceid' AND value=old.serviceid::text;

CREATE TABLE serviceproperty (
  id SERIAL,
  serviceid INT4 NOT NULL REFERENCES service ON UPDATE CASCADE ON DELETE CASCADE,
  property VARCHAR(64) NOT NULL,
  value VARCHAR,
  PRIMARY KEY(serviceid, property)
);

------------------------------------------------------------------------------
-- messages/maintenance v2 tables
------------------------------------------------------------------------------

CREATE TABLE message (
    messageid SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    tech_description TEXT,
    publish_start TIMESTAMP,
    publish_end TIMESTAMP,
    author VARCHAR NOT NULL,
    last_changed TIMESTAMP,
    replaces_message INT REFERENCES message,
    replaced_by INT REFERENCES message
);

CREATE OR REPLACE FUNCTION message_replace() RETURNS TRIGGER AS '
    DECLARE
        -- Old replaced_by value of the message beeing replaced
        old_replaced_by INTEGER;
    BEGIN
        -- Remove references that are no longer correct
        IF TG_OP = ''UPDATE'' THEN
            IF OLD.replaces_message <> NEW.replaces_message OR
                (OLD.replaces_message IS NOT NULL AND NEW.replaces_message IS NULL) THEN
                EXECUTE ''UPDATE message SET replaced_by = NULL WHERE messageid = ''
                || quote_literal(OLD.replaces_message);
            END IF;
        END IF;

        -- It does not replace any message, exit
        IF NEW.replaces_message IS NULL THEN
            RETURN NEW;
        END IF;

        -- Update the replaced_by field of the replaced message with a
        -- reference to the replacer
        SELECT INTO old_replaced_by replaced_by FROM message
            WHERE messageid = NEW.replaces_message;
        IF old_replaced_by <> NEW.messageid OR old_replaced_by IS NULL THEN
            EXECUTE ''UPDATE message SET replaced_by = ''
            || quote_literal(NEW.messageid)
            || '' WHERE messageid = ''
            || quote_literal(NEW.replaces_message);
        END IF;

        RETURN NEW;
        END;
    ' language 'plpgsql';

CREATE TRIGGER trig_message_replace
	AFTER INSERT OR UPDATE ON message
	FOR EACH ROW
	EXECUTE PROCEDURE message_replace();

CREATE OR REPLACE VIEW message_with_replaced AS
    SELECT
        m.messageid, m.title,
	m.description, m.tech_description,
        m.publish_start, m.publish_end, m.author, m.last_changed,
        m.replaces_message, m.replaced_by,
        rm.title AS replaces_message_title,
        rm.description AS replaces_message_description,
        rm.tech_description AS replaces_message_tech_description,
        rm.publish_start AS replaces_message_publish_start,
        rm.publish_end AS replaces_message_publish_end,
        rm.author AS replaces_message_author,
        rm.last_changed AS replaces_message_last_changed,
        rb.title AS replaced_by_title,
        rb.description AS replaced_by_description,
        rb.tech_description AS replaced_by_tech_description,
        rb.publish_start AS replaced_by_publish_start,
        rb.publish_end AS replaced_by_publish_end,
        rb.author AS replaced_by_author,
        rb.last_changed AS replaced_by_last_changed
    FROM
    	message m LEFT JOIN message rm ON (m.replaces_message = rm.messageid)
    	LEFT JOIN message rb ON (m.replaced_by = rb.messageid);

CREATE TABLE maint_task (
    maint_taskid SERIAL PRIMARY KEY,
    maint_start TIMESTAMP NOT NULL,
    maint_end TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    author VARCHAR NOT NULL,
    state VARCHAR NOT NULL
);

CREATE TABLE maint_component (
    id SERIAL,
    maint_taskid INT NOT NULL REFERENCES maint_task ON UPDATE CASCADE ON DELETE CASCADE,
    key VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    PRIMARY KEY (maint_taskid, key, value)
);

CREATE TABLE message_to_maint_task (
    id SERIAL,
    messageid INT NOT NULL REFERENCES message ON UPDATE CASCADE ON DELETE CASCADE,
    maint_taskid INT NOT NULL REFERENCES maint_task ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (messageid, maint_taskid)
);

CREATE OR REPLACE VIEW maint AS
    SELECT * FROM maint_task NATURAL JOIN maint_component;

------------------------------------------------------------------------------
-- log of schema changes
------------------------------------------------------------------------------
CREATE TABLE schema_change_log (
    id SERIAL PRIMARY KEY,
    major INTEGER NOT NULL,
    minor INTEGER NOT NULL,
    point INTEGER NOT NULL,
    script_name VARCHAR NOT NULL,
    date_applied TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('info','macWarning','Mac appeared on port');

------------------------------------------------------------------------------
-- mac watch table for storing watched mac addresses
------------------------------------------------------------------------------
CREATE TABLE manage.macwatch (
  id SERIAL PRIMARY KEY,
  camid INT REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
  mac MACADDR NOT NULL,
  posted TIMESTAMP,
  userid INT REFERENCES account(id) ON DELETE SET NULL ON UPDATE CASCADE,
  login VARCHAR,
  description VARCHAR,
  created TIMESTAMP DEFAULT NOW()
);

INSERT INTO subsystem (
  SELECT 'macwatch' AS name
  WHERE NOT EXISTS (
    SELECT name FROM subsystem WHERE name='macwatch'));

CREATE OR REPLACE RULE netbox_status_close_arp AS ON UPDATE TO netbox
   WHERE NEW.up='n'
   DO UPDATE arp SET end_time=NOW()
     WHERE netboxid=OLD.netboxid AND end_time='infinity';

UPDATE snmpoid SET uptodate=FALSE WHERE oidsource ILIKE 'cricket';

ALTER TABLE rrd_file DROP CONSTRAINT rrd_file_netboxid_fkey;
ALTER TABLE rrd_file ADD CONSTRAINT rrd_file_netboxid_fkey
  FOREIGN KEY (netboxid) REFERENCES netbox(netboxid)
  ON UPDATE CASCADE ON DELETE CASCADE;

CREATE TABLE manage.sensor (
  sensorid SERIAL PRIMARY KEY,
  netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
  oid VARCHAR,
  unit_of_measurement VARCHAR,
  precision integer default 0,
  data_scale VARCHAR,
  human_readable VARCHAR,
  name VARCHAR,
  internal_name VARCHAR,
  mib VARCHAR
);

CREATE TABLE manage.powersupply_or_fan (
    powersupplyid SERIAL PRIMARY KEY,
    netboxid INT REFERENCES netbox(netboxid) ON DELETE CASCADE ON UPDATE CASCADE,
    deviceid INT REFERENCES device(deviceid) ON DELETE CASCADE ON UPDATE CASCADE,
    name VARCHAR NOT NULL,
    model VARCHAR,
    descr VARCHAR,
    physical_class VARCHAR not null,
    downsince TIMESTAMP default null,
    sensor_oid VARCHAR,
    up CHAR(1) NOT NULL DEFAULT 'u' CHECK (up='y' OR up='n' or up='u' or up='w')
);

INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('snmpAgentState', 'Tells us whether the SNMP agent on a device is down or up.', 'y');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('snmpAgentState', 'snmpAgentDown', 'SNMP agent is down or unreachable due to misconfiguration.');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('snmpAgentState', 'snmpAgentUp', 'SNMP agent is up.');

INSERT INTO subsystem (name) VALUES ('ipdevpoll');

ALTER SEQUENCE eventqvar_id_seq OWNED BY manage.eventqvar.id;
ALTER SEQUENCE accountgroup_accounts_id_seq OWNED BY profiles.accountgroup_accounts.id;
ALTER SEQUENCE accountproperty_id_seq OWNED BY profiles.accountproperty.id;
ALTER SEQUENCE alertsender_id_seq OWNED BY profiles.alertsender.id;
ALTER SEQUENCE alertprofile_id_seq OWNED BY profiles.alertprofile.id;
ALTER SEQUENCE alertaddress_id_seq OWNED BY profiles.alertaddress.id;
ALTER SEQUENCE timeperiod_id_seq OWNED BY profiles.timeperiod.id;
ALTER SEQUENCE filtergroup_group_permission_id_seq OWNED BY profiles.filtergroup_group_permission.id;
ALTER SEQUENCE filtergroup_id_seq OWNED BY profiles.filtergroup.id;
ALTER SEQUENCE filtergroupcontent_id_seq OWNED BY profiles.filtergroupcontent.id;
ALTER SEQUENCE expression_id_seq OWNED BY profiles.expression.id;
ALTER SEQUENCE filter_id_seq OWNED BY profiles.filter.id;
ALTER SEQUENCE operator_operator_id_seq OWNED BY profiles.operator.operator_id;
ALTER SEQUENCE operator_id_seq OWNED BY profiles.operator.id;
ALTER SEQUENCE matchfield_id_seq OWNED BY profiles.matchfield.id;
ALTER SEQUENCE alertsubscription_id_seq OWNED BY profiles.alertsubscription.id;
ALTER SEQUENCE accountnavbar_id_seq OWNED BY profiles.accountnavbar.id;
ALTER SEQUENCE navbarlink_id_seq OWNED BY profiles.navbarlink.id;
ALTER SEQUENCE accountorg_id_seq OWNED BY profiles.accountorg.id;
ALTER SEQUENCE account_id_seq OWNED BY profiles.account.id;
ALTER SEQUENCE accountgroup_id_seq OWNED BY profiles.accountgroup.id;
ALTER SEQUENCE accountgroupprivilege_id_seq OWNED BY profiles.accountgroupprivilege.id;
ALTER SEQUENCE privilege_id_seq OWNED BY profiles.privilege.privilegeid;
ALTER SEQUENCE statuspreference_organization_id_seq OWNED BY profiles.statuspreference_organization.id;
ALTER SEQUENCE statuspreference_id_seq OWNED BY profiles.statuspreference.id;
ALTER SEQUENCE statuspreference_category_id_seq OWNED BY profiles.statuspreference_category.id;

-- Ensure any associated service alerts are closed when a service is deleted
CREATE RULE close_alerthist_services
  AS ON DELETE TO service DO
  UPDATE alerthist SET end_time=NOW()
  WHERE
    eventtypeid='serviceState'
    AND end_time='infinity'
    AND subid = old.serviceid::text;

-- Rule to automatically resolve netbox related alert states when netboxes are
-- deleted.
CREATE OR REPLACE RULE close_alerthist_netboxes AS ON DELETE TO netbox
  DO UPDATE alerthist SET end_time=NOW()
     WHERE netboxid=OLD.netboxid
       AND end_time='infinity';

-- swp_netbox replacement table
CREATE TABLE manage.adjacency_candidate (
  adjacency_candidateid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  to_netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  to_interfaceid INT4 REFERENCES interface ON UPDATE CASCADE ON DELETE SET NULL,
  source VARCHAR NOT NULL,
  misscnt INT4 NOT NULL DEFAULT 0,
  CONSTRAINT adjacency_candidate_uniq UNIQUE(netboxid, interfaceid, to_netboxid, source)
);

DELETE FROM netboxinfo WHERE key='unrecognizedCDP';

-- new unrecognized neighbors table
CREATE TABLE manage.unrecognized_neighbor (
  id SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  interfaceid INT4 NOT NULL REFERENCES interface ON UPDATE CASCADE ON DELETE CASCADE,
  remote_id VARCHAR NOT NULL,
  remote_name VARCHAR NOT NULL,
  source VARCHAR NOT NULL,
  since TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE unrecognized_neighbor IS 'Unrecognized neighboring devices reported by support discovery protocols';

INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (6, 'Thresholds exceeded', 6, 'threshold', 0);
INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (7, 'SNMP agents down', 7, 'snmpagent', 0);
INSERT INTO statuspreference (id, name, position, type, accountid) VALUES (8, 'Links down', 8, 'linkstate', 0);

UPDATE matchfield SET list_limit=1000 WHERE list_limit < 1000;

ALTER TABLE gwportprefix RENAME COLUMN hsrp TO virtual;

-- Create a log table for ipdevpoll job runs
CREATE TABLE manage.ipdevpoll_job_log (
  id BIGSERIAL NOT NULL PRIMARY KEY,
  netboxid INTEGER NOT NULL,
  job_name VARCHAR NOT NULL,
  end_time TIMESTAMP NOT NULL,
  duration DOUBLE PRECISION,
  success BOOLEAN NOT NULL,
  "interval" INTEGER,

  CONSTRAINT ipdevpoll_job_log_netbox_fkey FOREIGN KEY (netboxid)
             REFERENCES netbox (netboxid)
             ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TRIGGER trig_trim_old_ipdevpoll_job_log_entries_on_insert
    AFTER INSERT ON ipdevpoll_job_log
    FOR EACH ROW
    EXECUTE PROCEDURE trim_old_ipdevpoll_job_log_entries();

-- Grant web access to unauthorized ajax requests
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 2, 2, '^/ajax/open/?' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid=2 AND privilegeid=2 AND target='^/ajax/open/?'
  )
;

-- Add column for storing rrd-file category
ALTER TABLE rrd_file ADD category VARCHAR

-- Insert oids used to check for ipv6 interface counters
INSERT INTO snmpoid (oidkey, snmpoid, oidsource, mib)
  SELECT 'ipIfStatsHCInOctets.ipv4', '1.3.6.1.2.1.4.31.3.1.6.1', 'Cricket', 'IP-MIB' WHERE NOT EXISTS (
    SELECT * FROM snmpoid WHERE oidkey = 'ipIfStatsHCInOctets.ipv4'
  )
;

INSERT INTO snmpoid (oidkey, snmpoid, oidsource, mib)
  SELECT 'ipIfStatsHCInOctets.ipv6', '1.3.6.1.2.1.4.31.3.1.6.2', 'Cricket', 'IP-MIB' WHERE NOT EXISTS (
    SELECT * FROM snmpoid WHERE oidkey = 'ipIfStatsHCInOctets.ipv6'
  )
;

-- Grant web access to osm map redirects
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target)
  SELECT 2, 2, '^/info/osm_map_redirect/?' WHERE NOT EXISTS (
    SELECT * FROM AccountGroupPrivilege WHERE accountgroupid=2 AND privilegeid=2 AND target = '^/info/osm_map_redirect/?'
  )
;

-- Grant web access to /info for authenticated users
UPDATE AccountGroupPrivilege SET
        target = '^/(report|status|alertprofiles|machinetracker|browse|preferences|cricket|stats|ipinfo|l2trace|logger|ipdevinfo|geomap|info|netmap)/?'
  WHERE target = '^/(report|status|alertprofiles|machinetracker|browse|preferences|cricket|stats|ipinfo|l2trace|logger|ipdevinfo|geomap)/?'
;

CREATE OR REPLACE FUNCTION trim_old_ipdevpoll_job_log_entries()
RETURNS TRIGGER AS '
    BEGIN
        DELETE FROM ipdevpoll_job_log
        WHERE id IN (SELECT id FROM ipdevpoll_job_log
                     WHERE job_name=NEW.job_name AND netboxid=NEW.netboxid
                     ORDER BY end_time DESC
                     OFFSET 100);
        RETURN NULL;
    END;
    ' language 'plpgsql';

UPDATE snmpoid SET oidsource = 'IP-MIB' WHERE oidkey ~* 'ipIfStatsHCInOctets';

-- automatically close snmpAgentStates when community is removed.

CREATE OR REPLACE FUNCTION close_snmpagentstates_on_community_clear()
RETURNS TRIGGER AS E'
    BEGIN
        IF COALESCE(OLD.ro, \'\') IS DISTINCT FROM COALESCE(NEW.ro, \'\')
           AND COALESCE(NEW.ro, \'\') = \'\' THEN
            UPDATE alerthist
            SET end_time=NOW()
            WHERE netboxid=NEW.netboxid
              AND eventtypeid=\'snmpAgentState\'
              AND end_time >= \'infinity\';
        END IF;
        RETURN NULL;
    END;
    ' language 'plpgsql';

CREATE TRIGGER trig_close_snmpagentstates_on_community_clear
    AFTER UPDATE ON netbox
    FOR EACH ROW
    EXECUTE PROCEDURE close_snmpagentstates_on_community_clear();

-- also close any currently wrongfully open SNMP states
UPDATE alerthist
SET end_time=NOW()
FROM netbox
WHERE eventtypeid='snmpAgentState'
  AND end_time >= 'infinity'
  AND alerthist.netboxid = netbox.netboxid
  AND COALESCE(netbox.ro, '') = '';

INSERT INTO subsystem VALUES ('powersupplywatch');

-- create new event and alert types for fan and psu alerts

INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('psuState', 'Reports state changes in power supply units', 'y');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('psuState', 'psuNotOK', 'A PSU has entered a non-OK state');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('psuState', 'psuOK', 'A PSU has returned to an OK state');


INSERT INTO eventtype (eventtypeid, eventtypedesc, stateful) VALUES
  ('fanState', 'Reports state changes in fan units', 'y');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('fanState', 'fanNotOK', 'A fan unit has entered a non-OK state');

INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('fanState', 'fanOK', 'A fan unit has returned to an OK state');

-- rename logging jobs to ip2mac in ipdevpoll job log table
UPDATE ipdevpoll_job_log SET job_name = 'ip2mac' WHERE job_name = 'logging';

-- Add unit column to snmpoid table for storing of units
ALTER TABLE snmpoid ADD unit VARCHAR;


-- Insert some default units
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c1900Bandwidth';
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c1900BandwidthMax';
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c2900Bandwidth';
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c5000Bandwidth';
UPDATE snmpoid SET unit = 'Mbit/s' WHERE oidkey = 'c5000BandwidthMax';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'cpu1min';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'cpu5min';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'hpcpu';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'hpmem5minFree';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'hpmem5minUsed';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'mem5minFree';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'mem5minUsed';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'ucd_cpuIdle';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'ucd_cpuSystem';
UPDATE snmpoid SET unit = '%' WHERE oidkey = 'ucd_cpuUser';
UPDATE snmpoid SET unit = 'load' WHERE oidkey = 'ucd_load15min';
UPDATE snmpoid SET unit = 'load' WHERE oidkey = 'ucd_load1min';
UPDATE snmpoid SET unit = 'load' WHERE oidkey = 'ucd_load5min';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ucd_memrealAvail';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ucd_memswapAvail';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ucd_memtotalAvail';
UPDATE snmpoid SET unit = 'timeticks' WHERE oidkey = 'sysUpTime';

UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ipIfStatsHCInOctets.ipv6';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ipIfStatsHCInOctets.ipv4';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ifHCInOctets';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifHCInUcastPkts';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ifHCOutOctets';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifHCOutUcastPkts';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInDiscards';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInErrors';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInNUcastPkts';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ifInOctets';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInUcastPkts';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifInUnknownProtos';
UPDATE snmpoid SET unit = 'timeticks' WHERE oidkey = 'ifLastChange';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutDiscards';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutErrors';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutNUcastPkts';
UPDATE snmpoid SET unit = 'bytes' WHERE oidkey = 'ifOutOctets';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutQLen';
UPDATE snmpoid SET unit = 'packets' WHERE oidkey = 'ifOutUcastPkts';

-- automatically close thresholdState when threshold in rrd_datasource is removed.
CREATE OR REPLACE FUNCTION close_thresholdstate_on_threshold_delete()
RETURNS TRIGGER AS E'
  BEGIN
    IF TG_OP = \'DELETE\' THEN
      UPDATE alerthist
        SET end_time = NOW()
          WHERE subid = CAST(OLD.rrd_datasourceid AS text)
            AND eventtypeid = \'thresholdState\'
              AND end_time >= \'infinity\';
    END IF;
    IF TG_OP = \'UPDATE\' THEN
        IF COALESCE(OLD.threshold, \'\') IS 
            DISTINCT FROM COALESCE(NEW.threshold, \'\')
                AND COALESCE(NEW.threshold, \'\') = \'\' THEN
            UPDATE alerthist
                SET end_time = NOW()
                    WHERE subid = CAST(NEW.rrd_datasourceid AS text)
                        AND eventtypeid = \'thresholdState\'
                            AND end_time >= \'infinity\';
        END IF;
    END IF;
    RETURN NULL;
  END;
  'language 'plpgsql';

CREATE TRIGGER trig_close_thresholdstate_on_threshold_delete
    AFTER UPDATE OR DELETE ON rrd_datasource
    FOR EACH ROW
    EXECUTE PROCEDURE close_thresholdstate_on_threshold_delete();

-- also close any currently wrongfully open threshold states
UPDATE alerthist
    SET end_time = NOW()
    FROM rrd_datasource
        WHERE eventtypeid = 'thresholdState'
            AND end_time >= 'infinity'
            AND subid NOT IN
                (SELECT CAST(rrd_datasource.rrd_datasourceid AS text)
                    FROM rrd_datasource);

UPDATE alerthist
    SET end_time = NOW()
    FROM rrd_datasource
        WHERE eventtypeid = 'thresholdState'
            AND end_time >= 'infinity'
            AND alerthist.subid = CAST(rrd_datasource.rrd_datasourceid AS text)
            AND COALESCE(rrd_datasource.threshold, '') = '';

-- Alter unit on octets

UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ipIfStatsHCInOctets.ipv6';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ipIfStatsHCInOctets.ipv4';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ifHCInOctets';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ifHCOutOctets';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ifInOctets';
UPDATE snmpoid SET unit = 'bytes/s' WHERE oidkey = 'ifOutOctets';

-- Added because macwatch may use mac-address prefixes
CREATE TABLE macwatch_match(
  id SERIAL PRIMARY KEY,
  macwatch INT NOT NULL REFERENCES macwatch(id) ON DELETE CASCADE ON UPDATE CASCADE,
  cam INT NOT NULL REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
  posted TIMESTAMP DEFAULT NOW()
);

INSERT INTO macwatch_match (macwatch, cam, posted)
  SELECT id, camid, posted
    FROM macwatch
  WHERE camid IS NOT NULL;

ALTER TABLE macwatch ADD COLUMN prefix_length INT DEFAULT NULL;
ALTER TABLE macwatch ADD CONSTRAINT macwatch_unique_mac UNIQUE (mac);
ALTER TABLE macwatch DROP COLUMN camid;
ALTER TABLE macwatch DROP COLUMN posted;
ALTER TABLE macwatch DROP COLUMN login;

-- Notify the eventEngine immediately as new events are inserted in the queue
CREATE OR REPLACE RULE eventq_notify AS ON INSERT TO eventq DO ALSO NOTIFY new_event;

-- remove useless cam constraints/indexes to prevent index bloat
-- On some installs, the index may already have been manually removed. "DROP
-- CONSTRAINT IF EXISTS" wasn't introduced until PostgreSQL 9,
-- so we make a conditional drop function to accomplish this without errors
-- here:

CREATE OR REPLACE FUNCTION manage.drop_constraint(tbl_schema VARCHAR, tbl_name VARCHAR, const_name VARCHAR) RETURNS void AS $$
DECLARE
    exec_string TEXT;
BEGIN
    exec_string := 'ALTER TABLE ';
    IF tbl_schema != NULL THEN
        exec_string := exec_string || quote_ident(tbl_schema) || '.';
    END IF;
    exec_string := exec_string || quote_ident(tb_name)
        || ' DROP CONSTRAINT '
        || quote_ident(const_name);
    EXECUTE exec_string;
EXCEPTION
    WHEN OTHERS THEN
        NULL;
END;
$$ LANGUAGE plpgsql;

SELECT drop_constraint('manage', 'cam', 'cam_netboxid_key');
DROP INDEX IF EXISTS cam_start_time_btree;

-- Create trigger to delete rrd_file tuples regarding deleted prefix
CREATE OR REPLACE RULE prefix_on_delete_do_clean_rrd_file AS ON DELETE TO prefix
  DO DELETE FROM rrd_file
      WHERE category = 'activeip'
          AND key = 'prefix' AND CAST(value AS int) = OLD.prefixid;

-- Fix uniqueness on quarantine vlans

DELETE FROM quarantine_vlans WHERE quarantineid in (
  SELECT q2.quarantineid
  FROM quarantine_vlans q1
  JOIN quarantine_vlans q2
    ON (q1.vlan = q2.vlan AND q1.quarantineid < q2.quarantineid)
    ORDER BY q1.quarantineid);

ALTER TABLE quarantine_vlans ADD CONSTRAINT quarantine_vlan_unique UNIQUE (vlan);


INSERT INTO schema_change_log (major, minor, point, script_name)
    VALUES (3, 13, 15, 'initial install');

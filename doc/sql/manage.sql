-- Slette alle tabeller

DROP TABLE mem CASCADE;
DROP TABLE swportblocked CASCADE;
DROP TABLE swportallowedvlan CASCADE;
DROP TABLE swportvlan CASCADE;
DROP TABLE gwport CASCADE;
DROP TABLE vlan CASCADE;
DROP TABLE prefix CASCADE;
DROP TABLE gwportprefix CASCADE;
DROP TABLE swport CASCADE;
DROP TABLE module CASCADE;
DROP TABLE netboxcategory;
DROP TABLE netboxinfo;
DROP TABLE netbox CASCADE;
DROP TABLE emotd CASCADE;
DROP TABLE maintenance CASCADE;
DROP TABLE emotd_related CASCADE;
DROP TABLE cat CASCADE;
DROP TABLE device CASCADE;
DROP TABLE product CASCADE;
DROP TABLE vendor CASCADE;
DROP TABLE type CASCADE;
DROP TABLE snmpoid CASCADE;
DROP TABLE typegroup CASCADE;
DROP TABLE room CASCADE;
DROP TABLE location CASCADE;
DROP TABLE usage CASCADE;
DROP TABLE org CASCADE;
DROP TABLE port2off CASCADE;

DROP TABLE swp_netbox CASCADE;
DROP TABLE alertengine;

-------VP - fingra fra fatet, Sigurd:
DROP TABLE vp_netbox_xy CASCADE;
DROP TABLE vp_netbox_grp CASCADE;
DROP TABLE vp_netbox_grp_info CASCADE;

-- Slette alle sekvenser
DROP SEQUENCE netbox_netboxid_seq;
DROP SEQUENCE gwport_gwportid_seq;
DROP SEQUENCE prefix_prefixid_seq;
DROP SEQUENCE type_typeid_seq;
DROP SEQUENCE swport_swportid_seq;
DROP SEQUENCE swp_netbox_swp_netboxid_seq;
DROP SEQUENCE device_deviceid_seq;
DROP SEQUENCE product_productid_seq;
DROP SEQUENCE module_moduleid_seq;
DROP SEQUENCE mem_memid_seq;
DROP SEQUENCE emotd_emotdid_seq;
DROP SEQUENCE maintenance_maintenanceid_seq;

-------------
DROP SEQUENCE vp_netbox_grp_vp_netbox_grp_seq;
DROP SEQUENCE vp_netbox_xy_vp_netbox_xyid_seq;

-- Slette alle indekser

DROP TABLE status CASCADE;
DROP SEQUENCE status_statusid_seq;

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

------------------------------------------------------------------------------------------

CREATE TABLE org (
  orgid VARCHAR(30) PRIMARY KEY,
  parent VARCHAR(30) REFERENCES org (orgid),
  descr VARCHAR,
  opt1 VARCHAR,
  opt2 VARCHAR,
  opt3 VARCHAR
);


CREATE TABLE usage (
  usageid VARCHAR(30) PRIMARY KEY,
  descr VARCHAR NOT NULL
);


CREATE TABLE location (
  locationid VARCHAR(30) PRIMARY KEY,
  descr VARCHAR NOT NULL
);

CREATE TABLE room (
  roomid VARCHAR(30) PRIMARY KEY,
  locationid VARCHAR(30) REFERENCES location,
  descr VARCHAR,
  opt1 VARCHAR,
  opt2 VARCHAR,
  opt3 VARCHAR,
  opt4 VARCHAR
);

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
INSERT INTO nettype (nettypeid,descr,edit) VALUES ('static','static',TRUE);
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

CREATE TABLE product (
  productid SERIAL PRIMARY KEY,
  vendorid VARCHAR(15) NOT NULL REFERENCES vendor ON UPDATE CASCADE ON DELETE CASCADE,
  productno VARCHAR NOT NULL,
  descr VARCHAR,
  UNIQUE (vendorid,productno)
);

CREATE TABLE deviceorder (
  deviceorderid SERIAL PRIMARY KEY,
  registered TIMESTAMP NOT NULL DEFAULT now(),
  ordered DATE,
  arrived TIMESTAMP DEFAULT 'infinity',
  ordernumber VARCHAR,
  comment VARCHAR,
  retailer VARCHAR,
  username VARCHAR,
  orgid VARCHAR(30) REFERENCES org (orgid) ON UPDATE CASCADE ON DELETE SET NULL,
  productid INTEGER REFERENCES product (productid) ON UPDATE CASCADE ON DELETE SET NULL,
  updatedby VARCHAR,
  lastupdated DATE);


CREATE TABLE device (
  deviceid SERIAL PRIMARY KEY,
  productid INT4 REFERENCES product ON UPDATE CASCADE ON DELETE SET NULL,
  serial VARCHAR,
  hw_ver VARCHAR,
  fw_ver VARCHAR,
  sw_ver VARCHAR,
	auto BOOLEAN NOT NULL DEFAULT false,
  active BOOLEAN NOT NULL DEFAULT false,
  deviceorderid INT4 REFERENCES deviceorder (deviceorderid) ON DELETE CASCADE,
  UNIQUE(serial)
-- productid burde vært NOT NULL, men det går ikke nå
);
-- tror ikke uniquene jeg har lagt inn skader.

CREATE TABLE type (
  typeid SERIAL PRIMARY KEY,
  vendorid VARCHAR(15) NOT NULL REFERENCES vendor ON UPDATE CASCADE ON DELETE CASCADE,
  typename VARCHAR NOT NULL,
  sysObjectID VARCHAR NOT NULL,
  cdp BOOL DEFAULT false,
  tftp BOOL DEFAULT false,
  cs_at_vlan BOOL,
  chassis BOOL NOT NULL DEFAULT true,
  frequency INT4,
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
  uptodate BOOLEAN NOT NULL DEFAULT false,
  descr VARCHAR,
  oidname VARCHAR,
  mib VARCHAR,
  UNIQUE(oidkey)
);

CREATE TABLE netbox (
  netboxid SERIAL PRIMARY KEY,
  ip INET NOT NULL,
  roomid VARCHAR(30) NOT NULL REFERENCES room,
  typeid INT4 REFERENCES type ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 NOT NULL REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  sysname VARCHAR UNIQUE,
  catid VARCHAR(8) NOT NULL REFERENCES cat ON UPDATE CASCADE ON DELETE CASCADE,
  subcat VARCHAR,
  orgid VARCHAR(30) NOT NULL REFERENCES org,
  ro VARCHAR,
  rw VARCHAR,
  prefixid INT4 REFERENCES prefix ON UPDATE CASCADE ON DELETE SET null,
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n' OR up='s'), -- y=up, n=down, s=shadow
  snmp_version INT4 NOT NULL DEFAULT 1,
  snmp_agent VARCHAR,
  upsince TIMESTAMP NOT NULL DEFAULT NOW(),
  uptodate BOOLEAN NOT NULL DEFAULT false, 
  UNIQUE(ip),
  UNIQUE(deviceid)
);

CREATE TABLE netboxsnmpoid (
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  snmpoidid INT4 REFERENCES snmpoid ON UPDATE CASCADE ON DELETE CASCADE,
  frequency INT4,
  UNIQUE(netboxid, snmpoidid)
);  

CREATE TABLE netbox_vtpvlan (
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  vtpvlan INT4,
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
  module INT4 NOT NULL,
  model VARCHAR,
  descr VARCHAR,
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n'), -- y=up, n=down
  downsince TIMESTAMP,
  UNIQUE (netboxid, module),
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


CREATE TABLE swport (
  swportid SERIAL PRIMARY KEY,
  moduleid INT4 NOT NULL REFERENCES module ON UPDATE CASCADE ON DELETE CASCADE,
  ifindex INT4 NOT NULL,
  port INT4,
  interface VARCHAR,
  link CHAR(1) CHECK (link='y' OR link='n' OR link='d'), -- y=up, n=down (operDown), d=down (admDown)
  speed DOUBLE PRECISION,
  duplex CHAR(1) CHECK (duplex='f' OR duplex='h'), -- f=full, h=half
  media VARCHAR,
  vlan INT,
  trunk BOOL,
  portname VARCHAR,
  to_netboxid INT4 REFERENCES netbox (netboxid) ON UPDATE CASCADE ON DELETE SET NULL,
  to_swportid INT4 REFERENCES swport (swportid) ON UPDATE CASCADE ON DELETE SET NULL,
  UNIQUE(moduleid, ifindex)
);

CREATE TABLE swp_netbox (
  swp_netboxid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  ifindex INT4 NOT NULL,
  to_netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  to_swportid INT4 REFERENCES swport (swportid) ON UPDATE CASCADE ON DELETE SET NULL,
  misscnt INT4 NOT NULL DEFAULT '0',
  UNIQUE(netboxid, ifindex, to_netboxid)
);

CREATE TABLE gwport (
  gwportid SERIAL PRIMARY KEY,
  moduleid INT4 NOT NULL REFERENCES module ON UPDATE CASCADE ON DELETE CASCADE,
  ifindex INT4 NOT NULL,
  link CHAR(1) CHECK (link='y' OR link='n' OR link='d'), -- y=up, n=down (operDown), d=down (admDown)
  masterindex INT4,
  interface VARCHAR,
  speed DOUBLE PRECISION NOT NULL,
  metric INT4,
  to_netboxid INT4 REFERENCES netbox (netboxid) ON UPDATE CASCADE ON DELETE SET NULL,
  to_swportid INT4 REFERENCES swport (swportid) ON UPDATE CASCADE ON DELETE SET NULL,
  UNIQUE(moduleid, ifindex)
);
CREATE INDEX gwport_to_swportid_btree ON gwport USING btree (to_swportid);

CREATE TABLE gwportprefix (
  gwportid INT4 NOT NULL REFERENCES gwport ON UPDATE CASCADE ON DELETE CASCADE,
  prefixid INT4 NOT NULL REFERENCES prefix ON UPDATE CASCADE ON DELETE CASCADE,
  gwip INET NOT NULL,
  hsrp BOOL NOT NULL DEFAULT false,
  UNIQUE(gwip)
);

CREATE TABLE swportvlan (
  swportvlanid SERIAL PRIMARY KEY,
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlanid INT4 NOT NULL REFERENCES vlan ON UPDATE CASCADE ON DELETE CASCADE,
  direction CHAR(1) NOT NULL DEFAULT 'x', -- u=up, d=down, ...
  UNIQUE (swportid, vlanid)
);

CREATE TABLE swportallowedvlan (
  swportid INT4 NOT NULL PRIMARY KEY REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  hexstring VARCHAR
);


CREATE TABLE swportblocked (
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT4 NOT NULL,
  PRIMARY KEY(swportid, vlan)
);

CREATE TABLE alertengine (
	lastalertqid integer
);

INSERT INTO alertengine (lastalertqid) values(0);

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
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  cablingid INT4 NOT NULL REFERENCES cabling ON UPDATE CASCADE ON DELETE CASCADE,
  split VARCHAR NOT NULL DEFAULT 'no',
UNIQUE(swportid,cablingid));


------------------------------------------------------------------
------------------------------------------------------------------

DROP TABLE arp CASCADE;
DROP TABLE cam CASCADE;
DROP VIEW netboxmac CASCADE;
DROP VIEW prefix_active_ip_cnt CASCADE;
DROP VIEW prefix_max_ip_cnt CASCADE;
DROP TABLE eventtype CASCADE;

DROP SEQUENCE arp_arpid_seq; 
DROP SEQUENCE cam_camid_seq; 

DROP FUNCTION netboxid_null_upd_end_time();

-- arp og cam trenger en spesiell funksjon for å være sikker på at records alltid blir avsluttet
-- Merk at "createlang -U manage -d manage plpgsql" må kjøres først (passord må skrives inn flere ganger!!)
CREATE FUNCTION netboxid_null_upd_end_time () RETURNS opaque AS
  'BEGIN
     IF old.netboxid IS NOT NULL AND new.netboxid IS NULL THEN
       new.end_time = current_timestamp;
     END IF;
     RETURN new;
   end' LANGUAGE plpgsql;

CREATE TABLE arp (
  arpid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  prefixid INT4 REFERENCES prefix ON UPDATE CASCADE ON DELETE SET NULL,
  sysname VARCHAR NOT NULL,
  ip INET NOT NULL,
  mac CHAR(12) NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL DEFAULT 'infinity'
);
CREATE TRIGGER update_arp BEFORE UPDATE ON arp FOR EACH ROW EXECUTE PROCEDURE netboxid_null_upd_end_time();
CREATE INDEX arp_mac_btree ON arp USING btree (mac);
CREATE INDEX arp_ip_btree ON arp USING btree (ip);
CREATE INDEX arp_start_time_btree ON arp USING btree (start_time);
CREATE INDEX arp_end_time_btree ON arp USING btree (end_time);

CREATE TABLE cam (
  camid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  sysname VARCHAR NOT NULL,
  ifindex INT4 NOT NULL,
  module VARCHAR(4),
  port INT4,
  mac CHAR(12) NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL DEFAULT 'infinity',
  misscnt INT4 DEFAULT '0',
  UNIQUE(netboxid,sysname,module,port,mac,start_time)
);
CREATE TRIGGER update_cam BEFORE UPDATE ON cam FOR EACH ROW EXECUTE PROCEDURE netboxid_null_upd_end_time();
CREATE INDEX cam_mac_btree ON cam USING btree (mac);
CREATE INDEX cam_start_time_btree ON cam USING btree (start_time);
CREATE INDEX cam_end_time_btree ON cam USING btree (end_time);
CREATE INDEX cam_misscnt_btree ON cam USING btree (misscnt);


-- VIEWs -----------------------
CREATE VIEW netboxmac AS  
(SELECT DISTINCT ON (mac) netbox.netboxid,mac
 FROM arp
 JOIN netbox USING (ip)
 WHERE arp.end_time='infinity')
UNION
(SELECT DISTINCT ON (mac) module.netboxid,mac
 FROM arp
 JOIN gwportprefix ON (arp.ip=gwportprefix.gwip)
 JOIN gwport USING(gwportid)
 JOIN module USING (moduleid)
 WHERE arp.end_time='infinity');

CREATE VIEW prefix_active_ip_cnt AS
(SELECT prefixid,COUNT(*) AS active_ip_cnt
 FROM arp
 WHERE end_time='infinity'
 GROUP BY prefixid);

CREATE VIEW prefix_max_ip_cnt AS
(SELECT prefixid,
  CASE POW(2,32-MASKLEN(netaddr))-2 WHEN -1 THEN 0
   ELSE
  POW(2,32-MASKLEN(netaddr))-2 END AS max_ip_cnt
 FROM prefix);

-------- vlanPlot tabeller ------
CREATE TABLE vp_netbox_grp_info (
  vp_netbox_grp_infoid SERIAL PRIMARY KEY,
  name VARCHAR NOT NULL,
  hideicons BOOL NOT NULL DEFAULT false,
  iconname VARCHAR,
  x INT4 NOT NULL DEFAULT '0',
  y INT4 NOT NULL DEFAULT '0'
);
-- Default nett
INSERT INTO vp_netbox_grp_info (vp_netbox_grp_infoid,name,hideicons) VALUES (0,'_Top',true);

CREATE TABLE vp_netbox_grp (
  vp_netbox_grp_infoid INT4 REFERENCES vp_netbox_grp_info ON UPDATE CASCADE ON DELETE CASCADE,
  pnetboxid INT4 NOT NULL,
  UNIQUE(vp_netbox_grp_infoid, pnetboxid)
);

CREATE TABLE vp_netbox_xy (
  vp_netbox_xyid SERIAL PRIMARY KEY, 
  pnetboxid INT4 NOT NULL,
  x INT4 NOT NULL,
  y INT4 NOT NULL,
  vp_netbox_grp_infoid INT4 NOT NULL REFERENCES vp_netbox_grp_info ON UPDATE CASCADE ON DELETE CASCADE,
  UNIQUE(pnetboxid, vp_netbox_grp_infoid)
);

-- vPServer bruker
-- CREATE USER vpserver WITH PASSWORD '' NOCREATEDB NOCREATEUSER;
-- CREATE USER navadmin WITH PASSWORD '' NOCREATEDB NOCREATEUSER;
-- CREATE USER getboksmacs WITH PASSWORD '' NOCREATEDB NOCREATEUSER;
-- CREATE USER getportdata WITH PASSWORD '' NOCREATEDB NOCREATEUSER;



-------- vlanPlot end ------

------------------------------------------------------------------------------------------
-- rrd metadb tables
------------------------------------------------------------------------------------------

DROP TABLE subsystem CASCADE;
DROP TABLE rrd_file CASCADE;
DROP TABLE rrd_datasource CASCADE;

DROP SEQUENCE rrd_file_seq;
DROP SEQUENCE rrd_datasource_seq;

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
INSERT INTO subsystem (name) VALUES ('deviceTracker');
INSERT INTO subsystem (name) VALUES ('getDeviceData');
INSERT INTO subsystem (name) VALUES ('emotd');

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
  value     VARCHAR
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

DROP TABLE eventq CASCADE;
DROP SEQUENCE eventq_eventqid_seq;
DROP TABLE eventqvar CASCADE;

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
CREATE INDEX eventq_target_btree ON eventq USING btree (target);
CREATE TABLE eventqvar (
  eventqid INT4 REFERENCES eventq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  UNIQUE(eventqid, var) -- only one val per var per event
);
CREATE INDEX eventqvar_eventqid_btree ON eventqvar USING btree (eventqid);



-- alert tables
DROP TABLE alertq CASCADE;
DROP SEQUENCE alertq_alertqid_seq;
DROP TABLE alertqmsg CASCADE;

CREATE TABLE alerttype (
  alerttypeid SERIAL PRIMARY KEY,
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  alerttype VARCHAR,
  alerttypedesc VARCHAR
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
  severity INT4 NOT NULL
);

CREATE TABLE alertqmsg (
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  msgtype VARCHAR NOT NULL,
  language VARCHAR NOT NULL,
  msg TEXT NOT NULL,
  UNIQUE(alertqid, msgtype, language)
);
CREATE INDEX alertqmsg_alertqid_btree ON alertqmsg USING btree (alertqid);
CREATE TABLE alertqvar (
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  UNIQUE(alertqid, var) -- only one val per var per event
);
CREATE INDEX alertqvar_alertqid_btree ON alertqvar USING btree (alertqid);


DROP TABLE alerthist CASCADE;
DROP SEQUENCE alerthist_alerthistid_seq;
DROP TABLE alerthistmsg CASCADE;
DROP TABLE alerthistvar CASCADE;

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
CREATE INDEX alerthist_end_time_btree ON alerthist USING btree (end_time);

CREATE TABLE alerthistmsg (
  alerthistid INT4 REFERENCES alerthist ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  msgtype VARCHAR NOT NULL,
  language VARCHAR NOT NULL,
  msg TEXT NOT NULL,
  UNIQUE(alerthistid, state, msgtype, language)
);
CREATE INDEX alerthistmsg_alerthistid_btree ON alerthistmsg USING btree (alerthistid);

CREATE TABLE alerthistvar (
  alerthistid INT4 REFERENCES alerthist ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  var VARCHAR NOT NULL,
  val TEXT NOT NULL,
  UNIQUE(alerthistid, state, var) -- only one val per var per state per alert
);
CREATE INDEX alerthistvar_alerthistid_btree ON alerthistvar USING btree (alerthistid);


CREATE TABLE emotd (
    emotdid SERIAL PRIMARY KEY,
    replaces_emotd INT NULL REFERENCES emotd ON UPDATE CASCADE ON DELETE SET NULL,
    -- internal message?
    -- author is username (login) from navprofiles-db
    author VARCHAR NOT NULL,
    last_changed TIMESTAMP NOT NULL,
    title VARCHAR NOT NULL,
    title_en VARCHAR,
    description TEXT NOT NULL,
    description_en TEXT,
    -- a more technical description
    detail TEXT,
    detail_en TEXT,
    -- which users
    affected TEXT,
    affected_en TEXT,
    publish_start TIMESTAMP,
    publish_end TIMESTAMP,
    -- email sent?
    published BOOLEAN NOT NULL DEFAULT False,
    -- estimated downtime
    downtime VARCHAR,
    downtime_en VARCHAR,
    -- "info" or "error"
    type VARCHAR NOT NULL
);                  

-- scheduled - ongoing or old maintenance periods
CREATE TABLE maintenance (
    maintenanceid SERIAL PRIMARY KEY,
    emotdid INT NOT NULL REFERENCES emotd ON UPDATE CASCADE ON DELETE CASCADE,
    maint_start TIMESTAMP NOT NULL,
    maint_end TIMESTAMP NOT NULL,
    state VARCHAR CHECK (state IN ('scheduled','active','passed','overridden'))   
);

-- references to netbox/room/etc.
CREATE TABLE emotd_related (
    emotdid INT REFERENCES emotd ON UPDATE CASCADE ON DELETE CASCADE,
    -- typically "device", "room", etc., normally table name
    key VARCHAR NOT NULL,
    -- the identificator (primary key) of the referenced object
    value VARCHAR NOT NULL,
    PRIMARY KEY(emotdid,key,value)
);

-- maintenanceview, joined maintenance with emotd_related
CREATE OR REPLACE VIEW maintenance_view AS 
    SELECT maintenance.maintenanceid, emotd_related.emotdid, 
    emotd_related.key, emotd_related.value, maintenance.maint_start, 
    maintenance.maint_end, maintenance.state FROM maintenance, 
    emotd_related WHERE (emotd_related.emotdid = maintenance.emotdid);



------------------------------------------------------------------------------------------
-- servicemon tables
------------------------------------------------------------------------------------------

DROP TABLE service CASCADE;
DROP TABLE serviceproperty CASCADE;
DROP SEQUENCE service_serviceid_seq;

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
        WHERE key='serviceid' AND value=old.serviceid;

CREATE TABLE serviceproperty (
serviceid INT4 NOT NULL REFERENCES service ON UPDATE CASCADE ON DELETE CASCADE,
  property VARCHAR(64) NOT NULL,
  value VARCHAR,
  PRIMARY KEY(serviceid, property)
);

------------------------------------------------------------------------------------------
-- GRANTS AND GRUNTS
------------------------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION nav_grant(TEXT, BOOL) RETURNS INTEGER AS '
  DECLARE
    tables_rec   RECORD;
    counter      INTEGER;
    user_name    ALIAS FOR $1;
    write_access ALIAS FOR $2;
    use_priv     TEXT := ''SELECT'';
  BEGIN
    counter := 0;
    IF write_access THEN
      use_priv := ''ALL'';
    END IF;

    FOR tables_rec IN SELECT * FROM pg_tables WHERE schemaname=''public'' LOOP
      EXECUTE ''GRANT '' || use_priv
               || '' ON '' || quote_ident(tables_rec.tablename)
               || '' TO '' || quote_ident(user_name)
               || '';'';
      counter := counter + 1;
    END LOOP;

    FOR tables_rec IN SELECT * FROM pg_views WHERE schemaname=''public'' LOOP
      EXECUTE ''GRANT '' || use_priv
               || '' ON '' || quote_ident(tables_rec.viewname)
               || '' TO '' || quote_ident(user_name)
               || '';'';
      counter := counter + 1;
    END LOOP;

    FOR tables_rec IN SELECT * FROM pg_statio_all_sequences WHERE schemaname=''public'' LOOP
      EXECUTE ''GRANT '' || use_priv
               || '' ON '' || quote_ident(tables_rec.relname)
               || '' TO '' || quote_ident(user_name)
               || '';'';
      counter := counter + 1;
    END LOOP;

    RETURN counter;
  END;
' LANGUAGE 'plpgsql';


SELECT nav_grant('navread', false);
SELECT nav_grant('navwrite', true);

-- Slette alle tabeller
DROP TABLE swportblocked;
DROP TABLE swportallowedvlan;
DROP TABLE swportvlan;
DROP TABLE swport;
DROP TABLE gwport;

DROP TABLE swp_netbox;

DROP TABLE vendor;
DROP TABLE product;
DROP TABLE device;
DROP TABLE cat;
DROP TABLE module;
DROP TABLE mem;
DROP TABLE netboxinfo;
DROP TABLE netbox;
DROP TABLE typegroup;
DROP TABLE type;
DROP TABLE prefix;
DROP TABLE room;
DROP TABLE location;
DROP TABLE usage;
DROP TABLE org;

DROP TABLE netboxdisk;
DROP TABLE netboxinterface;

-------VP - fingra fra fatet, Sigurd:
DROP TABLE vp_netbox_xy;
DROP TABLE vp_netbox_grp;
DROP TABLE vp_netbox_grp_info;

-- Slette alle sekvenser
DROP SEQUENCE netbox_netboxid_seq;
DROP SEQUENCE gwport_gwportid_seq;
DROP SEQUENCE prefix_prefixid_seq;
DROP SEQUENCE type_typeid_seq;
DROP SEQUENCE swport_swportid_seq;
DROP SEQUENCE swportvlan_swportvlanid_seq;
DROP SEQUENCE swp_netbox_swp_netboxid_seq;
DROP SEQUENCE device_deviceid_seq;
DROP SEQUENCE product_productid_seq;
DROP SEQUENCE module_moduleid_seq;
DROP SEQUENCE mem_memid_seq;
-------------
DROP SEQUENCE vp_netbox_grp_vp_netbox_grp_seq;
DROP SEQUENCE vp_netbox_xy_vp_netbox_xyid_seq;

-- Slette alle indekser

---------------------- JM - don't touch

DROP TABLE status;
DROP SEQUENCE status_statusid_seq;

create table status (
statusid serial primary key,
trapsource varchar(30) not null,
trap varchar(25) not null,
trapdescr varchar(250),
tilstandsfull char(1) check (tilstandsfull='Y' or tilstandsfull='N') not null,
boksid int2,
fra timestamp not null,
til timestamp
);

-- smsutko er flyttet til trapdetect-databasen
--create table smsutko (
--id serial primary key,
--brukerid int2 not null,
--tidspunkt timestamp not null,
--melding varchar(145) not null,
--sendt char(1) not null default 'N' check (sendt='Y' or sendt='N' or sendt='I'),
--smsid int4,
--tidsendt timestamp
--); 

------------------------------------------

-- Definerer gruppe nav:
DROP GROUP nav;
CREATE GROUP nav;

------------------------------------------------------------------------------------------

CREATE TABLE org (
  orgid VARCHAR(10) PRIMARY KEY,
--  forelder VARCHAR(10) REFERENCES org,
  parent VARCHAR(10) REFERENCES org,
  descr VARCHAR(80),
  org2 VARCHAR(50),
  org3 VARCHAR(50),
  org4 VARCHAR(50)
);


--CREATE TABLE anv (
CREATE TABLE usage (
--  anvid VARCHAR(10) PRIMARY KEY,
  usageid VARCHAR(10) PRIMARY KEY,
  descr VARCHAR(20) NOT NULL
);


--CREATE TABLE sted (
CREATE TABLE location (
--  stedid VARCHAR(12) PRIMARY KEY,
  locationid VARCHAR(12) PRIMARY KEY,
  descr VARCHAR(60) NOT NULL
);

--CREATE TABLE rom (
CREATE TABLE room (
--  romid VARCHAR(10) PRIMARY KEY,
  roomid VARCHAR(10) PRIMARY KEY,
--  stedid VARCHAR(12) REFERENCES sted,
  locationid VARCHAR(12) REFERENCES location,
  descr VARCHAR(80),
--  rom2 VARCHAR(30),
  room2 VARCHAR(30),
--  rom3 VARCHAR(30),
  room3 VARCHAR(30),
--  rom4 VARCHAR(30),
  room4 VARCHAR(30),
--  rom5 VARCHAR(30)
  room5 VARCHAR(30)
);


--CREATE TABLE prefiks (
CREATE TABLE prefix (
--  prefiksid SERIAL PRIMARY KEY,
  prefixid SERIAL PRIMARY KEY,
--  nettadr varchar(15) NOT NULL,
--  maske VARCHAR(3) NOT NULL,
--fjernet under nav2 uten oppdatering av nav3
  netaddr CIDR NOT NULL,
  rootgwid INT4 UNIQUE,
  vlan INT4,
--  antmask INT2,
  active_ip_cnt INT4,
  max_ip_cnt INT4,
  nettype VARCHAR(10) NOT NULL,
  orgid VARCHAR(10) REFERENCES org,
--  anvid VARCHAR(10) REFERENCES anv,
  usageid VARCHAR(10) REFERENCES usage,
--  nettident VARCHAR(30),
  netident VARCHAR(30),
--  samband VARCHAR(20),
    to_gw VARCHAR(20),
--  komm VARCHAR(20)
  descr VARCHAR(50)
);

CREATE TABLE vendor (
  vendorid varchar(15) primary key
);

CREATE TABLE typegroup (
  typegroupid varchar(15) primary key,
  descr varchar(60)
);

CREATE TABLE cat (
  catid varchar(8) primary key,
  descr varchar(50)
);

CREATE TABLE product (
  productid SERIAL PRIMARY KEY,
  vendorid varchar(15) NOT NULL REFERENCES vendor ON UPDATE CASCADE ON DELETE CASCADE,
  productno VARCHAR(15) NOT NULL,
  descr VARCHAR(50),
  UNIQUE (vendorid,productno)
);


CREATE TABLE device (
  deviceid SERIAL PRIMARY KEY,
  productid INT4 REFERENCES product ON UPDATE CASCADE ON DELETE SET NULL,
  serial VARCHAR(15),
  hw_ver VARCHAR(10),
  sw_ver VARCHAR(10),
  UNIQUE(serial)
-- productid burde vært NOT NULL, men det går ikke nå
);
-- tror ikke uniquene jeg har lagt inn skader.

CREATE TABLE type (
  typeid SERIAL PRIMARY KEY,
  vendorid varchar(15) NOT NULL REFERENCES vendor ON UPDATE CASCADE ON DELETE CASCADE,
  typename VARCHAR(10) NOT NULL,
  typegroupid varchar(15) NOT NULL REFERENCES typegroup ON UPDATE CASCADE ON DELETE CASCADE,
  sysObjectID VARCHAR(30) NOT NULL,
  cdp BOOL DEFAULT false,
  tftp BOOL DEFAULT false,
  descr VARCHAR(50),
  UNIQUE (vendorid,typename)
);

--CREATE TABLE boks (
CREATE TABLE netbox (
--  boksid SERIAL PRIMARY KEY,
  netboxid SERIAL PRIMARY KEY,
--  ip varchar(15) NOT NULL, har vært inet en stund
  ip inet NOT NULL,
--  romid VARCHAR(10) NOT NULL REFERENCES rom,
  roomid VARCHAR(10) NOT NULL REFERENCES room,
  typeid INT4 REFERENCES type ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4 NOT NULL REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  sysname VARCHAR(30) UNIQUE,
  catid VARCHAR(8) NOT NULL REFERENCES cat ON UPDATE CASCADE ON DELETE CASCADE,
--  kat2 VARCHAR(10),
  subcat VARCHAR(10),
  orgid VARCHAR(10) NOT NULL REFERENCES org,
  ro VARCHAR(10),
  rw VARCHAR(10),
--  prefiksid INT4 REFERENCES prefiks ON UPDATE CASCADE ON DELETE SET null,
  prefixid INT4 REFERENCES prefix ON UPDATE CASCADE ON DELETE SET null,
--  boksvia2 integer REFERENCES boks ON UPDATE CASCADE ON DELETE SET null,
--  boksvia3 integer REFERENCES boks ON UPDATE CASCADE ON DELETE SET null,
--  active BOOL DEFAULT true,
--  static BOOL DEFAULT false,
--  watch BOOL DEFAULT false,
--  skygge BOOL DEFAULT false
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n' OR up='s'), -- y=up, n=down, s=shadow
  UNIQUE(ip)
);

CREATE TABLE netboxinfo (
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  key VARCHAR(32),
  var varchar(32) NOT NULL,
  val TEXT NOT NULL
);

CREATE TABLE netboxdisk (
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  path VARCHAR(255) NOT NULL,
  blocksize INT4 NOT NULL DEFAULT 1024,
  PRIMARY KEY (netboxid, path)
);


CREATE TABLE netboxinterface (
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  interf VARCHAR(50) NOT NULL,
  PRIMARY KEY (netboxid, interf)
);

CREATE TABLE module (
  moduleid SERIAL PRIMARY KEY,
  deviceid INT4 NOT NULL REFERENCES device ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  module VARCHAR(4) NOT NULL,
  submodule VARCHAR(8),
  up CHAR(1) NOT NULL DEFAULT 'y' CHECK (up='y' OR up='n'), -- y=up, n=down
  lastseen TIMESTAMP NOT NULL DEFAULT 'NOW()',
  UNIQUE (netboxid,module)
);
-- HVA ER SUBMODULE?
-- DEVICEID BØR VÆRE NOT NULL

CREATE TABLE mem (
  memid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  memtype VARCHAR(10) NOT NULL,
  device VARCHAR(15) NOT NULL,
  size INT4 NOT NULL,
  used INT4
);


CREATE TABLE swp_netbox (
  swp_netboxid SERIAL PRIMARY KEY,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  module VARCHAR(4) NOT NULL,
  port INT4 NOT NULL,
  to_netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  to_module VARCHAR(4),
  to_port INT4,
  misscnt INT4 NOT NULL DEFAULT '0',
  UNIQUE(netboxid,module,port,to_netboxid)
);

CREATE TABLE swport (
  swportid SERIAL PRIMARY KEY,
--  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
--  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
--  modul VARCHAR(4) NOT NULL,
  moduleid INT4 NOT NULL REFERENCES module ON UPDATE CASCADE ON DELETE CASCADE,
  port INT4 NOT NULL,
  ifindex INT4 NOT NULL,
--  status VARCHAR(4) NOT NULL DEFAULT 'down',
  link CHAR(1) NOT NULL DEFAULT 'y' CHECK (link='y' OR link='n' OR link='d'), -- y=up, n=down (operDown), d=down (admDown)
  speed DOUBLE PRECISION NOT NULL,
  duplex CHAR(1) NOT NULL CHECK (duplex='f' OR duplex='h'), -- f=full, h=half
  media VARCHAR(16),
  trunk BOOL NOT NULL DEFAULT false,
--  static BOOL DEFAULT false,  
--  portnavn VARCHAR(30),  
  portname VARCHAR(30),  
--  boksbak INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE SET NULL,
  to_netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
  to_swportid INT4 REFERENCES swport (swportid) ON UPDATE CASCADE ON DELETE SET NULL,
--  vpkatbak VARCHAR(5),
  to_catid VARCHAR(8),
  UNIQUE(moduleid, port)
);

CREATE TABLE gwport (
  gwportid SERIAL PRIMARY KEY,
--  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  netboxid INT4 NOT NULL REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
--  prefiksid INT4 REFERENCES prefiks ON UPDATE CASCADE ON DELETE SET null,
  prefixid INT4 REFERENCES prefix ON UPDATE CASCADE ON DELETE SET null,
  ifindex INT4 NOT NULL,
  masterindex INT4,
--  interf VARCHAR(30),
  interface VARCHAR(30),
  gwip inet,
  speed DOUBLE PRECISION NOT NULL,
  ospf INT4,
--  static BOOL DEFAULT false,
--  boksbak INT4 REFERENCES boks (boksid) ON UPDATE CASCADE ON DELETE SET null,
  to_netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE SET NULL,
--  swportbak INT4 REFERENCES swport (swportid) ON UPDATE CASCADE ON DELETE SET null
  to_swportid INT4 REFERENCES swport (swportid) ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE INDEX gwport_to_swportid_btree ON gwport USING btree (to_swportid);

CREATE TABLE swportvlan (
  swportvlanid SERIAL PRIMARY KEY,
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT4 NOT NULL,
--  retning CHAR(1) NOT NULL DEFAULT 'x',
  direction CHAR(1) NOT NULL DEFAULT 'x', -- u=up, d=down, ...
  UNIQUE (swportid,vlan)
);

CREATE TABLE swportallowedvlan (
  swportid INT4 NOT NULL PRIMARY KEY REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  hexstring varchar(256)
);


CREATE TABLE swportblocked (
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT4 NOT NULL DEFAULT '-1',
  PRIMARY KEY(swportid, vlan)
);


GRANT ALL ON org TO navall;
GRANT ALL ON usage TO navall;
GRANT ALL ON location TO navall;
GRANT ALL ON room TO navall;
GRANT ALL ON prefix TO navall;
GRANT ALL ON type TO navall;
GRANT ALL ON netbox TO navall;
GRANT ALL ON netboxinfo TO navall;
GRANT ALL ON module TO navall;
GRANT ALL ON mem TO navall;
GRANT ALL ON gwport TO navall;
GRANT ALL ON swport TO navall;
GRANT ALL ON swportvlan TO navall;
GRANT ALL ON swportallowedvlan TO navall;
GRANT ALL ON vendor TO navall;
GRANT ALL ON product TO navall;
GRANT ALL ON device TO navall;
GRANT ALL ON cat TO navall;
GRANT ALL ON typegroup TO navall;

GRANT ALL ON netbox_netboxid_seq TO navall;
GRANT ALL ON gwport_gwportid_seq TO navall;
GRANT ALL ON prefix_prefixid_seq TO navall;
GRANT ALL ON swport_swportid_seq TO navall;
GRANT ALL ON swportvlan_swportvlanid_seq TO navall;
GRANT ALL ON module_moduleid_seq TO navall;
GRANT ALL ON mem_memid_seq TO navall;
GRANT ALL ON product_productid_seq TO navall;
GRANT ALL ON device_deviceid_seq TO navall;
GRANT ALL ON type_typeid_seq TO navall;

------------------------------------------------------------------
------------------------------------------------------------------

DROP TABLE arp; 
DROP TABLE cam; 
DROP TABLE port2pkt; 
DROP TABLE pkt2rom;  
DROP VIEW netboxmac;
DROP TABLE eventtype;
DROP TABLE eventprocess;

DROP SEQUENCE arp_arpid_seq; 
DROP SEQUENCE cam_camid_seq; 
DROP SEQUENCE port2pkt_id_seq; 
DROP SEQUENCE pkt2rom_id_seq;
--DROP SEQUENCE vp_netbox_grp_vp_netbox_grp_seq;
--DROP SEQUENCE vp_netbox_xy_vp_netbox_xy_seq;

DROP FUNCTION netboxid_null_upd_end_time();

-- arp og cam trenger en spesiell funksjon for å være sikker på at records alltid blir avsluttet
-- Merk at "createlang -U manage -d manage plpgsql" må kjøres først
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
  sysname VARCHAR(30) NOT NULL,
  ip INET NOT NULL,
  mac VARCHAR(12) NOT NULL,
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
  sysname VARCHAR(30) NOT NULL,
  module VARCHAR(4) NOT NULL,
  port INT4 NOT NULL,
  mac VARCHAR(12) NOT NULL,
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

CREATE TABLE port2pkt (
  id SERIAL PRIMARY KEY,
  boks VARCHAR(15) NOT NULL,
  unit VARCHAR(2) NOT NULL,
  port VARCHAR(2) NOT NULL,
  trom VARCHAR(10) NOT NULL,
  pkt VARCHAR(4) NOT NULL
);


CREATE TABLE pkt2rom (
  id SERIAL PRIMARY KEY,
  trom VARCHAR(10) NOT NULL,
  pkt VARCHAR(4) NOT NULL,
  bygg VARCHAR(15) NOT NULL,
  rom VARCHAR(10) NOT NULL
);


GRANT all ON arp TO navall;
GRANT all ON arp_arpid_seq TO navall;
GRANT SELECT ON cam TO navall;
GRANT all ON port2pkt TO navall;
GRANT all ON port2pkt_id_seq TO navall;
GRANT all ON pkt2rom TO navall;
GRANT all ON pkt2rom_id_seq TO navall;


-- VIEWs -----------------------
CREATE VIEW netboxmac AS  
(SELECT DISTINCT ON (mac) netbox.netboxid,mac
 FROM arp
 JOIN netbox USING (ip)
 WHERE arp.end_time='infinity')
UNION
(SELECT DISTINCT ON (mac) gwport.netboxid,mac
 FROM arp
 JOIN gwport ON (arp.ip=gwport.gwip)
 WHERE arp.end_time='infinity');


-------- vlanPlot tabeller ------
CREATE TABLE vp_netbox_grp_info (
  vp_netbox_grp_infoid SERIAL PRIMARY KEY,
  name VARCHAR(16) NOT NULL,
  x INT4 NOT NULL DEFAULT '0',
  y INT4 NOT NULL DEFAULT '0'
);
-- Default nett
INSERT INTO vp_netbox_grp_info (vp_netbox_grp_infoid,name) VALUES (0,'Bynett');
INSERT INTO vp_netbox_grp_info (name) VALUES ('Kjernenett');
INSERT INTO vp_netbox_grp_info (name) VALUES ('Testnett');

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

GRANT SELECT ON netbox TO vPServer;
GRANT SELECT ON netboxinfo TO vPServer;
GRANT SELECT ON gwport TO vPServer;
GRANT SELECT ON prefix TO vPServer;
GRANT SELECT ON swport TO vPServer;
GRANT SELECT ON swportvlan TO vPServer;
GRANT SELECT,UPDATE ON vp_netbox_grp_info TO vPServer;
GRANT ALL    ON vp_netbox_grp TO vPServer;
GRANT ALL    ON vp_netbox_xy TO vPServer;
GRANT ALL    ON vp_netbox_xy_vp_netbox_xyid_seq TO vPServer;

GRANT SELECT ON netbox TO navadmin;
GRANT SELECT ON type TO navadmin;
GRANT SELECT ON netboxmac TO navadmin;
GRANT SELECT ON gwport TO navadmin;
GRANT SELECT ON prefix TO navadmin; 
GRANT ALL    ON swport TO navadmin;
GRANT ALL    ON swport_swportid_seq TO navadmin;
GRANT ALL    ON swportvlan TO navadmin;
GRANT ALL    ON swportvlan_swportvlanid_seq TO navadmin;
GRANT SELECT,DELETE ON swp_netbox TO navadmin;
GRANT ALL    ON swportallowedvlan TO navadmin;
GRANT SELECT ON swportblocked TO navadmin;

GRANT SELECT ON netbox TO getBoksMacs;
GRANT SELECT ON type TO getBoksMacs;
GRANT SELECT ON swport TO getBoksMacs;
GRANT ALL    ON swportvlan TO getBoksMacs;
GRANT ALL    ON swportvlan_swportvlanid_seq TO getBoksMacs;
GRANT SELECT,UPDATE ON gwport TO getBoksMacs;
GRANT SELECT ON prefix TO getBoksMacs;
GRANT SELECT ON netboxmac TO getBoksMacs;
GRANT ALL    ON swp_netbox TO getBoksMacs;
GRANT ALL    ON swp_netbox_swp_netboxid_seq TO getBoksMacs;
GRANT ALL    ON swportblocked TO getBoksMacs;
GRANT ALL    ON cam TO getBoksMacs;
GRANT ALL    ON cam_camid_seq TO getBoksMacs;

-- GRANT SELECT ON netbox TO getPortData;
-- GRANT SELECT ON type TO getPortData;
-- GRANT ALL    ON swport TO getPortData;
-- GRANT ALL    ON swport_swportid_seq TO getPortData;
-- GRANT ALL    ON swportvlan TO getPortData;
-- GRANT ALL    ON swportvlan_swportvlanid_seq TO getPortData;
-- GRANT ALL    ON swportallowedvlan TO getPortData;
-- GRANT SELECT,UPDATE ON gwport TO getPortData;
-- GRANT ALL    ON gwport_gwportid_seq TO getPortData;
-- GRANT SELECT ON prefiks TO getBoksMacs;

GRANT ALL    ON device TO getDeviceData;
GRANT ALL    ON device_deviceid_seq TO getDeviceData;
GRANT SELECT,UPDATE ON netbox TO getDeviceData;
GRANT SELECT,UPDATE ON netboxinfo TO getDeviceData;
GRANT SELECT ON type TO getDeviceData;
GRANT ALL    ON netboxdisk TO getDeviceData;
GRANT ALL    ON netboxinterface TO getDeviceData;
GRANT ALL    ON cat TO getDeviceData;
GRANT ALL    ON module TO getDeviceData;
GRANT ALL    ON module_moduleid_seq TO getDeviceData;
GRANT ALL    ON swport TO getDeviceData;
GRANT ALL    ON swport_swportid_seq TO getDeviceData;
GRANT ALL    ON swportvlan TO getDeviceData;
GRANT ALL    ON swportvlan_swportvlanid_seq TO getDeviceData;
GRANT ALL    ON swportallowedvlan TO getDeviceData;

-------- vlanPlot end ------


-------- event system tables --------
CREATE TABLE eventtype (
  eventtypeid VARCHAR(32) PRIMARY KEY
);
INSERT INTO eventtype (eventtypeid) VALUES ('boxState');
INSERT INTO eventtype (eventtypeid) VALUES ('serviceState');
INSERT INTO eventtype (eventtypeid) VALUES ('moduleState');
INSERT INTO eventtype (eventtypeid) VALUES ('thresholdState');
INSERT INTO eventtype (eventtypeid) VALUES ('linkState');
INSERT INTO eventtype (eventtypeid) VALUES ('coldStart');
INSERT INTO eventtype (eventtypeid) VALUES ('warmStart');
INSERT INTO eventtype (eventtypeid) VALUES ('info');

CREATE TABLE eventprocess (
  eventprocessid VARCHAR(32) PRIMARY KEY
);
INSERT INTO eventprocess (eventprocessid) VALUES ('eventEngine');
INSERT INTO eventprocess (eventprocessid) VALUES ('pping');
INSERT INTO eventprocess (eventprocessid) VALUES ('serviceping');
INSERT INTO eventprocess (eventprocessid) VALUES ('moduleMon');
INSERT INTO eventprocess (eventprocessid) VALUES ('thresholdMon');
INSERT INTO eventprocess (eventprocessid) VALUES ('trapParser');

DROP TABLE eventq;
DROP SEQUENCE eventq_eventqid_seq;
DROP TABLE eventqvar;

CREATE TABLE eventq (
  eventqid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES eventprocess (eventprocessid) ON UPDATE CASCADE ON DELETE CASCADE,
  target VARCHAR(32) NOT NULL REFERENCES eventprocess (eventprocessid) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  subid INT4,
  time TIMESTAMP NOT NULL DEFAULT 'NOW()',
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL DEFAULT 'x' CHECK (state='x' OR state='s' OR state='e'), -- x = stateless, s = start, e = end
  value INT4 NOT NULL DEFAULT '100',
  severity INT4 NOT NULL DEFAULT '50'
);
CREATE INDEX eventq_target_btree ON eventq USING btree (target);
CREATE TABLE eventqvar (
  eventqid INT4 REFERENCES eventq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR(32) NOT NULL,
  val TEXT NOT NULL
);
CREATE INDEX eventqvar_eventqid_btree ON eventqvar USING btree (eventqid);

-- alert tables
DROP TABLE alertq;
DROP SEQUENCE alertq_alertqid_seq;
DROP TABLE alertqvar;

CREATE TABLE alertq (
  alertqid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES eventprocess (eventprocessid) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  subid INT4,
  time TIMESTAMP NOT NULL,
  eventtypeid VARCHAR(32) REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  value INT4 NOT NULL,
  severity INT4 NOT NULL
);
CREATE TABLE alertqvar (
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  msgtype VARCHAR(32) NOT NULL,
  language VARCHAR(10) NOT NULL,
  msg TEXT NOT NULL,
  UNIQUE(alertqid, msgtype, language)
);

DROP TABLE alerthist;
DROP SEQUENCE alerthist_alerthistid_seq;
DROP TABLE alerthistvar;

CREATE TABLE alerthist (
  alerthistid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES eventprocess (eventprocessid) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  subid INT4,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP DEFAULT 'infinity',
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  value INT4 NOT NULL,
  severity INT4 NOT NULL
);
CREATE INDEX alerthist_end_time_btree ON alerthist USING btree (end_time);
CREATE TABLE alerthistvar (
  alerthistid INT4 REFERENCES alerthist ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR(32) NOT NULL,
  val TEXT NOT NULL
);

--servicemon tables
DROP TABLE service;
DROP TABLE serviceproperty;
DROP SEQUENCE service_serviceid_seq;

CREATE TABLE service (
  serviceid SERIAL PRIMARY KEY,
  netboxid INT4 REFERENCES netbox ON UPDATE CASCADE ON DELETE CASCADE,
  active BOOL DEFAULT true,
  handler VARCHAR(8),
  version VARCHAR(128)
);

CREATE TABLE serviceproperty (
serviceid INT4 NOT NULL REFERENCES service ON UPDATE CASCADE ON DELETE CASCADE,
  property VARCHAR(64) NOT NULL,
  value VARCHAR(64),
  PRIMARY KEY(serviceid, property)
);


GRANT SELECT ON eventtype TO eventengine;
GRANT SELECT ON eventprocess TO eventengine;
GRANT ALL ON eventq TO eventengine;
GRANT ALL ON eventq_eventqid_seq TO eventengine;
GRANT ALL ON eventqvar TO eventengine;
GRANT ALL ON alertq TO eventengine;
GRANT ALL ON alertq_alertqid_seq TO eventengine;
GRANT ALL ON alertqvar TO eventengine;
GRANT ALL ON alerthist TO eventengine;
GRANT ALL ON alerthist_alerthistid_seq TO eventengine;
GRANT ALL ON alerthistvar TO eventengine;
GRANT SELECT,UPDATE ON netbox TO eventengine;
GRANT SELECT ON module TO eventengine;
GRANT SELECT ON swport TO eventengine;
GRANT SELECT ON swportvlan TO eventengine;
GRANT SELECT ON gwport TO eventengine;
GRANT SELECT ON prefix TO eventengine;


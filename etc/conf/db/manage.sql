-- Slette alle views
DROP VIEW boksmac;

-- Slette alle tabeller
DROP TABLE swportallowedvlan;
DROP TABLE swportvlan;
DROP TABLE swport;
DROP TABLE gwport;

DROP TABLE swp_boks;

DROP TABLE module;
DROP TABLE mem;
DROP TABLE boksinfo;
DROP TABLE boks;

DROP TABLE type;
DROP TABLE prefiks;
DROP TABLE rom;
DROP TABLE sted;
DROP TABLE anv;
DROP TABLE org;

-------VP - fingra fra fatet, Sigurd:

DROP TABLE vpBoksXY;
DROP TABLE vpBoksGrp;
DROP TABLE vpBoksGrpInfo;

-- Slette alle sekvenser
DROP SEQUENCE boks_boksid_seq;
DROP SEQUENCE gwport_gwportid_seq;
DROP SEQUENCE prefiks_prefiksid_seq;
DROP SEQUENCE swport_swportid_seq;
DROP SEQUENCE swportvlan_swportvlanid_seq;
DROP SEQUENCE swp_boks_swp_boksid_seq;
DROP SEQUENCE module_moduleid_seq;
DROP SEQUENCE mem_memid_seq;
-------------
DROP SEQUENCE vpboksgrp_vpboksgrpid_seq;
DROP SEQUENCE vpboksgrpinfo_gruppeid_seq;
DROP SEQUENCE vpboksxy_vpboksxyid_seq;

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
CREATE TABLE use (
--  anvid VARCHAR(10) PRIMARY KEY,
  useid VARCHAR(10) PRIMARY KEY,
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
  netaddr inet NOT NULL,
  rootgwid INT2 UNIQUE,
  vlan INT2,
--  antmask INT2,
  computers INT2,
  maxhosts INT2,
  nettype VARCHAR(10) NOT NULL,
  orgid VARCHAR(10) REFERENCES org,
--  anvid VARCHAR(10) REFERENCES anv,
  useid VARCHAR(10) REFERENCES use,
--  nettident VARCHAR(30),
  netident VARCHAR(30),
--  samband VARCHAR(20),
    communication VARCHAR(20),
--  komm VARCHAR(20)
  descr VARCHAR(40)
);


CREATE TABLE type (
typeid SERIAL PRIMARY KEY,
vendorid varchar(15) NOT NULL REFERENCES vendor ON UPDATE CASCADE ON DELETE CASCADE,
typename VARCHAR(10) NOT NULL,
typegroupid varchar(15) NOT NULL REFERENCES typegroup ON UPDATE
CASCADE ON DELETE CASCADE,
sysObjectID VARCHAR(30) NOT NULL,
cdp BOOL DEFAULT false,
tftp BOOL DEFAULT false,
descr VARCHAR(50),
UNIQUE (vendorid,typename)
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
       productid INT4 NOT NULL REFERENCES product ON UPDATE CASCADE ON DELETE CASCADE,
       serial VARCHAR(15),
       sw VARCHAR(10),
       hw VARCHAR(10),
       function VARCHAR(50),
       UNIQUE(serial)
);
-- tror ikke uniquene jeg har lagt inn skader.

--CREATE TABLE boks (
CREATE TABLE boxx (
--  boksid SERIAL PRIMARY KEY,
  boxxid SERIAL PRIMARY KEY,
--  ip varchar(15) NOT NULL, har vært inet en stund
  ip inet NOT NULL,
--  romid VARCHAR(10) NOT NULL REFERENCES rom,
  roomid VARCHAR(10) NOT NULL REFERENCES room,
  typeid INT4 REFERENCES type ON UPDATE CASCADE ON DELETE CASCADE,
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
    up CHAR(1) NOT NULL DEFAULT 'n'
);
-- trenger constraints, det finnes ingen i denne fila jeg kan kopiere.


CREATE TABLE boksinfo (
  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  key VARCHAR(32),
  var varchar(32) NOT NULL,
  val TEXT NOT NULL
);

CREATE TABLE boksinfo_old (
  boksid INT4 NOT NULL PRIMARY KEY REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  main_sw varchar(20),
  serial varchar(15),
  function VARCHAR(100)
);

CREATE TABLE boksdisk (
  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  path VARCHAR(255) NOT NULL,
  blocksize INT4 NOT NULL DEFAULT 1024,
  PRIMARY KEY (boksid, path)
);


CREATE TABLE boksinterface (
  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  interf VARCHAR(50) NOT NULL,
  PRIMARY KEY (boksid, interf)
);

CREATE TABLE module (
       moduleid SERIAL PRIMARY KEY,
       deviceid INT4 REFERENCES device ON UPDATE CASCADE ON DELETE SET NULL,
       boxxid INT4 NOT NULL REFERENCES boxx ON UPDATE CASCADE ON DELETE CASCADE,
       module VARCHAR(4) NOT NULL,
       submodule VARCHAR(8),
       up CHAR(1) NOT NULL DEFAULT 'n',
       lastseen VARCHAR(8),
       UNIQUE (boxxid,module)
);
-- LITT I TVIL OM DATOFORMAT LASTSEEN, KOMMER TILBAKE TIL DETTE SEINERE.
-- UP TRENGER CONSTRAINT
-- HVA ER SUBMODULE?
-- DEVICEID BØR IKKE VÆRE NOT NULL

CREATE TABLE mem (
memid SERIAL PRIMARY KEY,
boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
memtype VARCHAR(10) NOT NULL,
device VARCHAR(15) NOT NULL,
size INTEGER NOT NULL,
used INTEGER
);


CREATE TABLE swp_boks (
  swp_boksid SERIAL PRIMARY KEY,
  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  modul VARCHAR(4) NOT NULL,
  port INT2 NOT NULL,
  boksbak INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  modulbak VARCHAR(4),
  portbak INT2,
  misscnt INT2 NOT NULL DEFAULT '0',
  UNIQUE(boksid,modul,port,boksbak)
);

CREATE TABLE swport (
  swportid SERIAL PRIMARY KEY,
--  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
--  boxxid INT4 NOT NULL REFERENCES boxx ON UPDATE CASCADE ON DELETE CASCADE,
--  modul VARCHAR(4) NOT NULL,
  moduleid INT4 NOT NULL REFERENCES module ON UPDATE CASCADE ON DELETE CASCADE,
  port INT2 NOT NULL,
  ifindex INT4 NOT NULL,
--  status VARCHAR(4) NOT NULL DEFAULT 'down',
    link CHAR(1) NOT NULL DEFAULT 'n',
  speed VARCHAR(10),
  duplex VARCHAR(4),
  media VARCHAR(16),
  trunk BOOL DEFAULT false,
--  static BOOL DEFAULT false,  
  portnavn VARCHAR(30),  
--  boksbak INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE SET NULL,
  boxxbehind INT4 REFERENCES boxx ON UPDATE CASCADE ON DELETE SET NULL,
--  vpkatbak VARCHAR(5),
  vpcatbehind VARCHAR(5),
  UNIQUE(boxxid, moduleid, port)
);
-- trenger du boksbak & vpkatbak, kristian?

CREATE TABLE gwport (
  gwportid SERIAL PRIMARY KEY,
--  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  boxxid INT4 NOT NULL REFERENCES boxx ON UPDATE CASCADE ON DELETE CASCADE,
--  prefiksid INT4 REFERENCES prefiks ON UPDATE CASCADE ON DELETE SET null,
  prefixid INT4 REFERENCES prefix ON UPDATE CASCADE ON DELETE SET null,
  ifindex INT2 NOT NULL,
  masterindex INT2,
--  interf VARCHAR(30),
  interface VARCHAR(30),
  gwip inet,
  speed VARCHAR(10),
  ospf INT2
--  static BOOL DEFAULT false,
--  boksbak INT4 REFERENCES boks (boksid) ON UPDATE CASCADE ON DELETE SET null,
--  swportbak INT4 REFERENCES swport (swportid) ON UPDATE CASCADE ON DELETE SET null
);
-- trenger du boksbak, så får du oversette den selv.

CREATE INDEX gwport_swportbak_btree ON gwport USING btree (swportbak);

CREATE TABLE swportvlan (
  swportvlanid SERIAL PRIMARY KEY,
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT4 NOT NULL,
--  retning CHAR(1) NOT NULL DEFAULT 'x',
  direction CHAR(1) NOT NULL DEFAULT 'x',
  UNIQUE (swportid,vlan)
);

CREATE TABLE swportallowedvlan (
  swportid INT4 NOT NULL PRIMARY KEY REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  hexstring varchar(256),
  static BOOL NOT NULL DEFAULT false
);
-- hva ble det til med static her?


CREATE TABLE swportblocked (
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT2 NOT NULL DEFAULT '-1',
  PRIMARY KEY(swportid, vlan)
);


GRANT ALL ON org TO navall;
GRANT ALL ON use TO navall;
GRANT ALL ON location TO navall;
GRANT ALL ON room TO navall;
GRANT ALL ON prefix TO navall;
GRANT ALL ON type TO navall;
GRANT ALL ON boxx TO navall;
GRANT ALL ON boksinfo TO navall;
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

GRANT ALL ON boxx_boxxid_seq TO navall;
GRANT ALL ON gwport_gwportid_seq TO navall;
GRANT ALL ON prefix_prefixid_seq TO navall;
GRANT ALL ON swport_swportid_seq TO navall;
GRANT ALL ON swportvlan_swportvlanid_seq TO navall;
GRANT ALL ON module_moduleid_seq TO navall;
GRANT ALL ON mem_memid_seq TO navall;
GRANT ALL ON product_productid_seq TO navall;
GRANT ALL ON type_typeid_seq TO navall;

------------------------------------------------------------------
------------------------------------------------------------------

DROP TABLE arp; 
DROP TABLE cam; 
DROP TABLE port2pkt; 
DROP TABLE pkt2rom;  

DROP SEQUENCE arp_arpid_seq; 
DROP SEQUENCE cam_camid_seq; 
DROP SEQUENCE port2pkt_id_seq; 
DROP SEQUENCE pkt2rom_id_seq;

CREATE TABLE boksmac_cache (
  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  mac VARCHAR(12) NOT NULL,
  UNIQUE(boksid,mac)
);

CREATE TABLE arp (
  arpid SERIAL PRIMARY KEY,
  boksid INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE SET NULL,
  prefiksid INT4 REFERENCES prefiks ON UPDATE CASCADE ON DELETE SET NULL,
  kilde VARCHAR(20) NOT NULL,
  ip VARCHAR(15) NOT NULL,
  ip_inet INET NOT NULL,
  mac VARCHAR(12) NOT NULL,
  fra TIMESTAMP NOT NULL,
  til TIMESTAMP NOT NULL DEFAULT 'infinity'
);
CREATE INDEX arp_mac_btree ON arp USING btree (mac);
CREATE INDEX arp_ip_inet_btree ON arp USING btree (ip_inet);
CREATE INDEX arp_fra_btree ON arp USING btree (fra); 
CREATE INDEX arp_til_btree ON arp USING btree (til);

CREATE TABLE cam (
  camid SERIAL PRIMARY KEY,
  boksid INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE SET NULL,
  sysName VARCHAR(30) NOT NULL,
  modul VARCHAR(4) NOT NULL,
  port INT2 NOT NULL,
  mac VARCHAR(12) NOT NULL,
  fra TIMESTAMP NOT NULL,
  til TIMESTAMP NOT NULL DEFAULT 'infinity',
  misscnt INT4 DEFAULT '0',
  UNIQUE(boksid,sysName,modul,port,mac,fra)
);
CREATE INDEX cam_mac_btree ON cam USING btree (mac);
CREATE INDEX cam_fra_btree ON cam USING btree (fra);
CREATE INDEX cam_til_btree ON cam USING btree (til);
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
CREATE VIEW boksmac AS  
(SELECT DISTINCT ON (mac) boks.boksid,mac
 FROM arp
 JOIN boks USING (ip)
 WHERE arp.til='infinity')
UNION
(SELECT DISTINCT ON (mac) gwport.boksid,mac
 FROM arp
 JOIN gwport ON (arp.ip=gwport.gwip)
 WHERE arp.til='infinity');


-------- vlanPlot tabeller ------
CREATE TABLE vpBoksGrpInfo (
  gruppeid SERIAL PRIMARY KEY,              
  name VARCHAR(16) NOT NULL,
  x INT2 NOT NULL DEFAULT '0',
  y INT2 NOT NULL DEFAULT '0'
);
-- Default nett
INSERT INTO vpboksgrpinfo (gruppeid,name) VALUES (0,'Bynett');
INSERT INTO vpboksgrpinfo (name) VALUES ('Kjernenett');
INSERT INTO vpboksgrpinfo (name) VALUES ('Testnett');

CREATE TABLE vpBoksGrp (
  vpBoksGrpId SERIAL PRIMARY KEY,
  gruppeid INT4 REFERENCES vpBoksGrpInfo ON UPDATE CASCADE ON DELETE CASCADE,
  pboksid INT4 NOT NULL,
  UNIQUE(gruppeid, pboksid)
);

CREATE TABLE vpBoksXY (
  vpBoksXYId SERIAL PRIMARY KEY, 
  pboksid INT4 NOT NULL,
  x INT2 NOT NULL,
  y INT2 NOT NULL,
  gruppeid INT4 NOT NULL REFERENCES vpBoksGrpInfo ON UPDATE CASCADE ON DELETE CASCADE,
  UNIQUE(pboksid, gruppeid)
);
-- vPServer bruker
-- CREATE USER vpserver WITH PASSWORD '' NOCREATEDB NOCREATEUSER;
-- CREATE USER navadmin WITH PASSWORD '' NOCREATEDB NOCREATEUSER;
-- CREATE USER getboksmacs WITH PASSWORD '' NOCREATEDB NOCREATEUSER;
-- CREATE USER getportdata WITH PASSWORD '' NOCREATEDB NOCREATEUSER;

GRANT SELECT ON boks TO vPServer;
GRANT SELECT ON boksinfo TO vPServer;
GRANT SELECT ON gwport TO vPServer;
GRANT SELECT ON prefiks TO vPServer;
GRANT SELECT ON swport TO vPServer;
GRANT SELECT ON swportvlan TO vPServer;
GRANT SELECT ON vpBoksGrp TO vPServer;
GRANT SELECT ON vpBoksGrpInfo TO vPServer;
GRANT ALL    ON vpBoksGrp TO vPServer;
GRANT ALL    ON vpBoksGrp_vpboksgrpid_seq TO vPServer;
GRANT UPDATE ON vpBoksGrpInfo TO vPServer;
GRANT ALL    ON vpBoksXY TO vPServer;
GRANT ALL    ON vpboksxy_vpboksxyid_seq TO vPServer;

GRANT SELECT ON boks TO navadmin;
GRANT SELECT ON type TO navadmin;
GRANT SELECT ON boksmac TO navadmin;
GRANT SELECT ON gwport TO navadmin;
GRANT SELECT ON prefiks TO navadmin; 
GRANT ALL    ON swport TO navadmin;
GRANT ALL    ON swport_swportid_seq TO navadmin;
GRANT ALL    ON swportvlan TO navadmin;
GRANT ALL    ON swportvlan_swportvlanid_seq TO navadmin;
GRANT SELECT,DELETE ON swp_boks TO navadmin;
GRANT ALL    ON swportallowedvlan TO navadmin;
GRANT SELECT ON swportblocked TO navadmin;

GRANT SELECT ON boks TO getBoksMacs;
GRANT SELECT ON type TO getBoksMacs;
GRANT SELECT ON swport TO getBoksMacs;
GRANT ALL    ON swportvlan TO getBoksMacs;
GRANT ALL    ON swportvlan_swportvlanid_seq TO getBoksMacs;
GRANT SELECT,UPDATE ON gwport TO getBoksMacs;
GRANT SELECT ON prefiks TO getBoksMacs;
GRANT SELECT ON boksmac TO getBoksMacs;
GRANT ALL    ON boksmac_cache TO getBoksMacs;
GRANT ALL    ON swp_boks TO getBoksMacs;
GRANT ALL    ON swp_boks_swp_boksid_seq TO getBoksMacs;
GRANT ALL    ON swportblocked TO getBoksMacs;
GRANT ALL    ON cam TO getBoksMacs;
GRANT ALL    ON cam_camid_seq TO getBoksMacs;

GRANT SELECT ON boks TO getPortData;
GRANT SELECT ON type TO getPortData;
GRANT ALL    ON swport TO getPortData;
GRANT ALL    ON swport_swportid_seq TO getPortData;
GRANT ALL    ON swportvlan TO getPortData;
GRANT ALL    ON swportvlan_swportvlanid_seq TO getPortData;
GRANT ALL    ON swportallowedvlan TO getPortData;
-- GRANT ALL    ON gwport TO getPortData;
-- GRANT ALL    ON gwport_gwportid_seq TO getPortData;
-- GRANT SELECT ON prefiks TO getBoksMacs;

GRANT SELECT,UPDATE ON boks TO getDeviceData;
GRANT SELECT,UPDATE ON boksinfo TO getDeviceData;
GRANT SELECT ON type TO getDeviceData;
GRANT ALL    ON boksdisk TO getDeviceData;
GRANT ALL    ON boksinterface TO getDeviceData;
GRANT ALL    ON bokscategory TO getDeviceData;
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
  boksid INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  subid INT4,
  time TIMESTAMP NOT NULL DEFAULT 'NOW()',
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL DEFAULT 'x' CHECK (state='x' OR state='s' OR state='e'), -- x = stateless, s = start, e = end
  value INT4 NOT NULL DEFAULT '100',
  severity INT4 NOT NULL DEFAULT '50'
);
CREATE INDEX eventq_target_btree ON eventq USING btree (target);
CREATE INDEX eventqvar_eventqid_btree ON eventqvar USING btree (eventqid);
CREATE TABLE eventqvar (
  eventqid INT4 REFERENCES eventq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR(32) NOT NULL,
  val TEXT NOT NULL
);

-- alert tables
DROP TABLE alertq;
DROP SEQUENCE alertq_alertqid_seq;
DROP TABLE alertqvar;

CREATE TABLE alertq (
  alertqid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES eventprocess (eventprocessid) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4,
  boksid INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  subid INT4,
  time TIMESTAMP NOT NULL,
  eventtypeid VARCHAR(32) REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  state CHAR(1) NOT NULL,
  value INT4 NOT NULL,
  severity INT4 NOT NULL
);
CREATE TABLE alertqvar (
  alertqid INT4 REFERENCES alertq ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR(32) NOT NULL,
  val TEXT NOT NULL
);

DROP TABLE alerthist;
DROP SEQUENCE alerthist_alerthistid_seq;
DROP TABLE alerthistvar;

CREATE TABLE alerthist (
  alerthistid SERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL REFERENCES eventprocess (eventprocessid) ON UPDATE CASCADE ON DELETE CASCADE,
  deviceid INT4,
  boksid INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  subid INT4,
  start_t TIMESTAMP NOT NULL,
  end_t TIMESTAMP DEFAULT 'infinity',
  eventtypeid VARCHAR(32) NOT NULL REFERENCES eventtype ON UPDATE CASCADE ON DELETE CASCADE,
  value INT4 NOT NULL,
  severity INT4 NOT NULL
);
CREATE INDEX alerthist_end_t_btree ON alerthist USING btree (end_t);
CREATE TABLE alerthistvar (
  alerthistid INT4 REFERENCES alerthist ON UPDATE CASCADE ON DELETE CASCADE,
  var VARCHAR(32) NOT NULL,
  val TEXT NOT NULL
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
GRANT SELECT,UPDATE ON boks TO eventengine;
GRANT SELECT ON module TO eventengine;
GRANT SELECT ON swport TO eventengine;
GRANT SELECT ON swportvlan TO eventengine;
GRANT SELECT ON gwport TO eventengine;
GRANT SELECT ON prefiks TO eventengine;


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

-- Legger inn gartmann i nav:
ALTER GROUP nav add user gartmann;

-- Fjerner gartmann fra nav:
ALTER GROUP nav drop user gartmann;

------------------------------------------------------------------------------------------

CREATE TABLE org (
  orgid VARCHAR(10) PRIMARY KEY,
  forelder VARCHAR(10) REFERENCES org,
  descr VARCHAR(80),
  org2 VARCHAR(50),
  org3 VARCHAR(50),
  org4 VARCHAR(50)
);


CREATE TABLE anv (
  anvid VARCHAR(10) PRIMARY KEY,
  descr VARCHAR(20) NOT NULL
);


CREATE TABLE sted (
  stedid VARCHAR(12) PRIMARY KEY,
  descr VARCHAR(60) NOT NULL
);

CREATE TABLE rom (
  romid VARCHAR(10) PRIMARY KEY,
  stedid VARCHAR(12) REFERENCES sted,
  descr VARCHAR(80),
  rom2 VARCHAR(30),
  rom3 VARCHAR(30),
  rom4 VARCHAR(30),
  rom5 VARCHAR(30)
);


CREATE TABLE prefiks (
  prefiksid SERIAL PRIMARY KEY,
  nettadr varchar(15) NOT NULL,
  maske VARCHAR(3) NOT NULL,
  rootgwid INT2 UNIQUE,
  vlan INT2,
  antmask INT2,
  maxhosts INT2,
  nettype VARCHAR(10) NOT NULL,
  orgid VARCHAR(10) REFERENCES org,
  anvid VARCHAR(10) REFERENCES anv,
  nettident VARCHAR(20),
  samband VARCHAR(20),
  komm VARCHAR(20)
);


CREATE TABLE type (
  typeid VARCHAR(10) PRIMARY KEY,
  typegruppe VARCHAR(10) NOT NULL,
  sysObjectID VARCHAR(30) NOT NULL,
  descr VARCHAR(60)
);


CREATE TABLE boks (
  boksid SERIAL PRIMARY KEY,
  ip varchar(15) NOT NULL,
  romid VARCHAR(10) NOT NULL REFERENCES rom,
  typeid VARCHAR(10) REFERENCES type,
  sysName VARCHAR(30) UNIQUE,
  kat VARCHAR(10) NOT NULL,
  kat2 VARCHAR(10),
  orgid VARCHAR(10) NOT NULL REFERENCES org,
  ro VARCHAR(10),
  rw VARCHAR(10),
  prefiksid INT4 REFERENCES prefiks ON UPDATE CASCADE ON DELETE SET null,
  boksvia2 integer REFERENCES boks ON UPDATE CASCADE ON DELETE SET null,
  boksvia3 integer REFERENCES boks ON UPDATE CASCADE ON DELETE SET null,
  active BOOL DEFAULT true,
  static BOOL DEFAULT false,
  watch BOOL DEFAULT false,
  skygge BOOL DEFAULT false
);


CREATE TABLE boksinfo (
boksid INT4 NOT NULL PRIMARY KEY REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
main_sw varchar(20),
serial varchar(15),
function VARCHAR(100)
);

CREATE TABLE module (
moduleid SERIAL PRIMARY KEY,
boksid INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
modulenumber INT4 NOT NULL,
model VARCHAR(10),
descr VARCHAR(25),
serial VARCHAR(15),
hw VARCHAR(10),
sw VARCHAR(10),
ports INT4,
portsUp INT4
);

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
  boksbak INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE swport (
  swportid SERIAL PRIMARY KEY,
  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  ifindex INT2 NOT NULL,
  status VARCHAR(4) NOT NULL DEFAULT 'down',
  speed VARCHAR(10),
  duplex VARCHAR(4),
  trunk BOOL DEFAULT false,
  static BOOL DEFAULT false,  
  modul VARCHAR(4) NOT NULL,
  port INT2 NOT NULL,
  portnavn VARCHAR(30),  
  vpkatbak VARCHAR(5),
  boksbak INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE SET null,
  UNIQUE(boksid, ifindex)
);

CREATE TABLE gwport (
  gwportid SERIAL PRIMARY KEY,
  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE CASCADE,
  prefiksid INT4 REFERENCES prefiks ON UPDATE CASCADE ON DELETE SET null,
  ifindex INT2 NOT NULL,
  masterindex INT2,
  interf VARCHAR(30),
  gwip varchar(15),
  speed VARCHAR(10),
  ospf INT2,
  static BOOL DEFAULT false,
  boksbak INT4 REFERENCES boks (boksid) ON UPDATE CASCADE ON DELETE SET null
  swportbak INT4 REFERENCES swport (swportid) ON UPDATE CASCADE ON DELETE SET null
);
-- not null fjernet fra interf 

CREATE TABLE swportvlan (
  swportvlanid SERIAL PRIMARY KEY,
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT4 NOT NULL,
  retning VARCHAR(1) NOT NULL DEFAULT 'x',
  UNIQUE (swportid,vlan)
);

CREATE TABLE swportallowedvlan (
  swportid INT4 NOT NULL PRIMARY KEY REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  hexstring varchar(256)
);

CREATE TABLE swportblocked (
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT2 NOT NULL DEFAULT '-1',
  PRIMARY KEY(swportid, vlan)
);


GRANT ALL ON org TO navall;
GRANT ALL ON anv TO navall;
GRANT ALL ON sted TO navall;
GRANT ALL ON rom TO navall;
GRANT ALL ON prefiks TO navall;
GRANT ALL ON type TO navall;
GRANT ALL ON boks TO navall;
GRANT ALL ON boksinfo TO navall;
GRANT ALL ON module TO navall;
GRANT ALL ON mem TO navall;
GRANT ALL ON gwport TO navall;
GRANT ALL ON swport TO navall;
GRANT ALL ON swportvlan TO navall;
GRANT ALL ON swportallowedvlan TO navall;

GRANT ALL ON boks_boksid_seq TO navall;
GRANT ALL ON gwport_gwportid_seq TO navall;
GRANT ALL ON prefiks_prefiksid_seq TO navall;
GRANT ALL ON swport_swportid_seq TO navall;
GRANT ALL ON swportvlan_swportvlanid_seq TO navall;
GRANT ALL ON module_moduleid_seq TO navall;
GRANT ALL ON mem_memid_seq TO navall;

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
  boksid INT4 NOT NULL REFERENCES boks ON UPDATE CASCADE ON DELETE SET NULL,
  mac VARCHAR(12) NOT NULL,
  UNIQUE(mac)
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
  til TIMESTAMP
);
CREATE INDEX arp_ip_inet_btree ON arp USING btree (ip_inet);
 
CREATE TABLE cam (
  camid SERIAL PRIMARY KEY,
  boksid INT4 REFERENCES boks ON UPDATE CASCADE ON DELETE SET NULL,
  sysName VARCHAR(30) NOT NULL,
  modul VARCHAR(4) NOT NULL,
  port INT2 NOT NULL,
  mac VARCHAR(12) NOT NULL,
  fra TIMESTAMP NOT NULL,
  til TIMESTAMP,
  UNIQUE(boksid,sysName,modul,port,mac,fra)
);
CREATE INDEX cam_mac_hash ON cam USING hash (mac);
CREATE INDEX cam_til_hash ON cam USING hash (til);
CREATE INDEX cam_til_btree ON cam USING btree (til);
 
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
GRANT all ON cam TO navall;
GRANT all ON cam_camid_seq TO navall;
GRANT all ON port2pkt TO navall;
GRANT all ON port2pkt_id_seq TO navall;
GRANT all ON pkt2rom TO navall;
GRANT all ON pkt2rom_id_seq TO navall;


-- VIEWs -----------------------
CREATE VIEW boksmac AS  
(SELECT DISTINCT ON (mac) boks.boksid,mac
 FROM arp
 JOIN boks USING (ip))
UNION
(SELECT DISTINCT ON (mac) gwport.boksid,mac
 FROM arp,gwport
 WHERE arp.ip=gwport.gwip);


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
CREATE USER vpserver WITH PASSWORD '' NOCREATEDB NOCREATEUSER;
CREATE USER getboksmacs WITH PASSWORD '' NOCREATEDB NOCREATEUSER;
CREATE USER navadmin WITH PASSWORD '' NOCREATEDB NOCREATEUSER;

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

-------- vlanPlot end ------

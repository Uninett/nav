# Definerer gruppe nav:
create group nav;

# Legger inn gartmann i nav:
alter group nav add user gartmann;

# Fjerner gartmann fra nav:
alter group nav drop user gartmann;


# org: descr fra 60 til 80
# boks: type ikke not null fordi ikke definert i nettel.txt

#community har blitt fjernet!
create table community (
id serial primary key,
boksid int4 not null references boks on update cascade on delete cascade,
ro char(10),
rw char(10)
);

grant all on community to group nav;

#ro og rw går inn i boks
#tabellen type lagt til
#boks:sysname 20->30 dns er for lange for 20
#boks:type er ute av drift inntil bruk
#prefiks: vlan ikke not null
#prefiksid references prefiks ikke boks overalt
#swport: lagt til port(nummer) og modul
#boksinfo:sysCon fra 30 til 40
#fremmednøkler til prefiksid peker på prefiks, ikke boks
#boksinfo:sysType char(30):fjernet
#gwport og swport: speed endret til char(10) for å kunne godta opptil 10 000 Tbps eller ned 0.000001 bps. (overkill?);
#alle char endret til varchar
#not null fjernet fra duplex i swport
#not null fjernet fra descr i rom
#############################################

create table org (
id varchar(10) primary key,
forelder varchar(10) references org,
descr varchar(80),
org2 varchar(50),
org3 varchar(50),
org4 varchar(50)
);


create table anv (
id varchar(10) primary key,
descr varchar(20) not null
);


create table sted (
sted varchar(12) primary key,
descr varchar(60) not null
);

create table rom (
id varchar(10) primary key,
sted varchar(12) references sted,
descr varchar(50),
rom2 varchar(10),
rom3 varchar(10),
rom4 varchar(10),
rom5 varchar(10)
);


create table prefiks (
id serial primary key,
nettadr varchar(15) not null,
maske varchar(3) not null,
vlan varchar(4),
nettype varchar(10) not null,
org varchar(10) references org,
anv varchar(10) references anv,
samband varchar(20),
komm varchar(20)
);


create table type (
type varchar(10) primary key,
typegruppe varchar(10) not null,
sysObjectID varchar(30) not null,
descr varchar(60)
);


create table boks (
id serial primary key,
ip varchar(15) not null,
romid varchar(10) not null references rom,
type varchar(10),
sysName varchar(30),
kat varchar(10) not null,
kat2 varchar(10),
drifter varchar(10) not null,
ro varchar(10),
rw varchar(10),
prefiksid int4 references prefiks on update cascade on delete set null,
via2 integer references boks on update cascade on delete set null,
via3 integer references boks on update cascade on delete set null,
active bool default true,
static bool default false,
watch bool default false,
skygge bool default false
);


create table boksinfo (
id serial primary key,
boksid int4 not null references boks on update cascade on delete cascade,
software varchar(13),
sysLoc varchar(50),
sysCon varchar(40),
ais int2,
mem varchar(10),
flashMem varchar(10),
function varchar(100),
supVersion varchar(10)
);



create table gwport (
id serial primary key,
boksid int4 not null references boks on update cascade on delete cascade,
prefiksid int4 references prefiks on update cascade on delete set null,
indeks int2 not null,
interf varchar(30) not null,
gwip varchar(15) not null,
speed varchar(10),
antmask int2,
maxhosts int2,
ospf int2,
hsrppri varchar(1),
static bool default false
);


create table swport (
id serial primary key,
boksid int4 not null references boks on update cascade on delete cascade,
ifindex int2 not null,
status varchar(4) not null default 'down',
speed varchar(10),
duplex varchar(4),
trunk bool default false,
static bool default false,
modul varchar(4) not null,
port int2 not null,
portnavn varchar(30),
boksbak int2 references boks on update cascade on delete set null
);


CREATE TABLE swportvlan (
  id serial primary key,
  swportid INT4 NOT NULL REFERENCES swport ON UPDATE CASCADE ON DELETE CASCADE,
  vlan INT2 NOT NULL,
  retning VARCHAR(1) NOT NULL DEFAULT 'x'
);


### vlanPlot tabeller ###
CREATE TABLE vpBoksGrpInfo (
  gruppeid SERIAL PRIMARY KEY,              
  name VARCHAR(16) NOT NULL
);
# Default nett
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
### vlanPlot end ###

grant all on org to group nav;
grant all on anv to group nav;
grant all on sted to group nav;
grant all on rom to group nav;
grant all on prefiks to group nav;
grant all on type to group nav;
grant all on boks to group nav;
grant all on boksinfo to group nav;
grant all on gwport to group nav;
grant all on swport to group nav;
grant all on swportvlan to group nav;



grant all on boks_id_seq to group nav;
grant all on boksinfo_id_seq to group nav;
grant all on gwport_id_seq to group nav;
grant all on prefiks_id_seq to group nav;
grant all on swport_id_seq to group nav;
grant all on swportvlan_id_seq to group nav;

################################

# Slette alle tabeller og sekvenser:

drop table anv;
drop table boks;
drop table boksinfo;
drop table gwport;
drop table org;
drop table type;
drop table prefiks;
drop table rom;
drop table sted;
drop table swport;
drop table swportvlan;
drop sequence boks_id_seq;
drop sequence boksinfo_id_seq;
drop sequence gwport_id_seq;
drop sequence prefiks_id_seq;
drop sequence swport_id_seq;
drop sequence swportvlan_id_seq;


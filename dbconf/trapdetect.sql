-- Slette alle tabeller
DROP TABLE bruker;
DROP TABLE brukeriorg;
DROP TABLE org;
DROP TABLE smsutko;
DROP TABLE subtrap;
DROP TABLE trap;
DROP TABLE trapeier;
DROP TABLE trapkat;
DROP TABLE unntak;
DROP TABLE varsel;
DROP TABLE varseltype;

-- Slette alle sekvenser

DROP SEQUENCE bruker_id_seq;
DROP SEQUENCE org_id_seq;
DROP SEQUENCE smsutko_id_seq;
DROP SEQUENCE trap_id_seq;
DROP SEQUENCE unntak_id_seq;
DROP SEQUENCE varsel_id_seq;
DROP SEQUENCE varseltype_id_seq;

-- Lage tabeller

create table trap (
id serial primary key,
sykoid varchar(50) not null,
syknavn varchar(50) not null,
friskoid varchar(50),
frisknavn varchar(50),
beskrivelse varchar(200),
type int2
);

create table subtrap (
trapid int2 not null references trap on update cascade on delete cascade,
suboid varchar(50) not null,
navn varchar(50) not null,
primary key (trapid,suboid)
);

create table trapkat (
trapid int2 not null references trap on update cascade on delete cascade,
kat varchar(10) not null,
primary key (trapid,kat)
);

create table org (
id serial primary key,
navn varchar(50)
);

create table bruker (
id serial primary key,
bruker varchar(10) not null,
mail varchar(40),
tlf varchar(8),
status varchar(5) not null default 'fri' check (status='fri' or status='aktiv'),
sms char(1) not null default 'N' check (sms='Y' or sms='N'),
dsms_fra varchar(8) not null default '23:30:30',
dsms_til varchar(8) not null default '06:00:00'
);

create table brukeriorg (
brukerid int2 references bruker on update cascade on delete cascade,
orgid int2 references org on update cascade on delete cascade,
primary key (brukerid,orgid)
);

create table trapeier (
orgid int2 references org on update cascade on delete cascade,
trapid int2 references trap on update cascade on delete cascade,
primary key (orgid,trapid)
);

create table varseltype (
id serial primary key,
navn varchar(9) not null
);

insert into varseltype (navn) values ('sms');
insert into varseltype (navn) values ('dsms');
insert into varseltype (navn) values ('dsms/mail');
insert into varseltype (navn) values ('sms/mail');
insert into varseltype (navn) values ('mail');
insert into varseltype (navn) values ('fri');

create table varsel (
id serial primary key,
brukerid int2 references bruker on update cascade on delete cascade,
trapid int2 references trap on update cascade on delete cascade,
kat varchar(10),
ukat varchar(10),
vtypeid int2 references varseltype on update cascade on delete cascade
);

create table unntak (
id serial primary key,
brukerid int2 references bruker on update cascade on delete cascade,
trapid int2 references trap on update cascade on delete cascade,
boksid int2 not null,
vtypeid int2 references varseltype on update cascade on delete cascade,
status varchar(5) not null check (status='minus' or status='pluss')
);


create table smsutko ( 
id serial primary key, 
brukerid int2 references bruker on update cascade on delete cascade, 
tidspunkt timestamp not null, 
melding varchar(145) not null, 
sendt char(1) not null default 'N' check (sendt='Y' or sendt='N' or sendt='I'), 
smsid int4, 
tidsendt timestamp 
);


-- Gi rettigheter til bruker varsle

GRANT ALL ON bruker TO varsle;
GRANT ALL ON brukeriorg TO varsle;
GRANT ALL ON org TO varsle;
GRANT ALL ON smsutko TO varsle;
GRANT ALL ON subtrap TO varsle;
GRANT ALL ON trap TO varsle;
GRANT ALL ON trapeier TO varsle;
GRANT ALL ON trapkat TO varsle;
GRANT ALL ON unntak TO varsle;
GRANT ALL ON varsel TO varsle;
GRANT ALL ON varseltype TO varsle;

GRANT ALL ON bruker_id_seq TO varsle;
GRANT ALL ON org_id_seq TO varsle;
GRANT ALL ON smsutko_id_seq TO varsle;
GRANT ALL ON trap_id_seq TO varsle;
GRANT ALL ON unntak_id_seq TO varsle;
GRANT ALL ON varsel_id_seq TO varsle;
GRANT ALL ON varseltype_id_seq TO varsle;







--------------------------------------------------------
-- system
-- Hvilket delsystem av nav som er avsender av meldingen
--------------------------------------------------------

DROP TABLE system;
DROP SEQUENCE system_id_seq;

CREATE TABLE system (
  id SERIAL PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  description VARCHAR(50)
);

GRANT ALL ON system TO navlogadmin;
GRANT ALL ON system_id_seq TO navlogadmin;
GRANT SELECT ON system TO navlogweb;
GRANT SELECT ON system_id_seq TO navlogweb;

--------------------------------------------------------
-- priority
-- Prioritetsnivå og beskrivelser
--------------------------------------------------------

DROP TABLE priority;

CREATE TABLE priority (
  id INTEGER PRIMARY KEY,
  priority INTEGER NOT NULL,
  keyword VARCHAR(20) UNIQUE NOT NULL,
  description VARCHAR(50)
);

GRANT ALL ON priority TO navlogadmin;
GRANT SELECT ON priority TO navlogweb;

--------------------------------------------------------
-- type
-- Typer meldinger, sterkt influert av syslog
--------------------------------------------------------

DROP TABLE type;
DROP SEQUENCE type_id_seq;

CREATE TABLE type (
  id SERIAL PRIMARY KEY,
  systemid INTEGER NOT NULL REFERENCES system (id) ON DELETE CASCADE ON UPDATE CASCADE,
  facility VARCHAR(20) NOT NULL,
  mnemonic VARCHAR(30) NOT NULL,
  priorityid INTEGER REFERENCES priority (id) ON DELETE SET NULL ON UPDATE CASCADE,
  defaultmessage VARCHAR(250),
  UNIQUE(systemid,facility,mnemonic)
);

GRANT ALL ON type TO navlogadmin;
GRANT ALL ON type_id_seq TO navlogadmin;
GRANT SELECT ON type TO navlogweb;
GRANT SELECT ON type_id_seq TO navlogweb;

--------------------------------------------------------
-- origin
-- Avsender av meldingene
-- Lurte på å legge category (bokstype) i egen tabell,
-- for å slippe å bruke distinct (som viser seg å være
-- for treg), men lot være fordi origin blir veldig
-- liten.
--------------------------------------------------------

DROP TABLE origin;
DROP SEQUENCE origin_id_seq;

CREATE TABLE origin (
  id SERIAL PRIMARY KEY,
  name VARCHAR(30) UNIQUE NOT NULL,
  systemid INTEGER NOT NULL REFERENCES system(id) ON UPDATE CASCADE ON DELETE CASCADE,
  category VARCHAR(5)
);

GRANT ALL ON origin TO navlogadmin;
GRANT ALL ON origin_id_seq TO navlogadmin;
GRANT SELECT ON origin TO navlogweb;
GRANT SELECT ON origin_id_seq TO navlogweb;

--------------------------------------------------------
-- message
-- Selve meldingen. Består av timestamp, avsender, 
-- type, prioritet og meldingstekst.
--------------------------------------------------------

DROP TABLE message;
DROP SEQUENCE message_id_seq;

CREATE TABLE message (
  id SERIAL PRIMARY KEY,
  time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  originid INTEGER NOT NULL REFERENCES origin (id) ON UPDATE CASCADE ON DELETE SET NULL,
  priority INTEGER REFERENCES priority (id) ON UPDATE CASCADE ON DELETE SET NULL,
  typeid INTEGER NOT NULL REFERENCES type (id) ON UPDATE CASCADE ON DELETE SET NULL,
  message VARCHAR(250)
);

GRANT ALL ON message TO navlogadmin;
GRANT ALL ON message_id_seq TO navlogadmin;
GRANT SELECT ON message TO navlogweb;
GRANT SELECT ON message_id_seq TO navlogweb;

--------------------------------------------------------
-- errorerror
-- Feilmeldinger som ikke er på riktig format blir blant
-- lagt her. Andre ting også.
--------------------------------------------------------

DROP TABLE errorerror;
DROP SEQUENCE errorerror_id_seq;

CREATE TABLE errorerror (
  id SERIAL PRIMARY KEY,
  message VARCHAR(250)
);

GRANT ALL ON errorerror TO navlogadmin;
GRANT ALL ON errorerror_id_seq TO navlogadmin;
GRANT SELECT ON errorerror TO navlogweb;
GRANT SELECT ON errorerror_id_seq TO navlogweb;

--------------------------------------------------------
-- Oppretter indeksering
--------------------------------------------------------

CREATE INDEX message_typeid_hash ON message USING hash (typeid);
CREATE INDEX message_originid_hash ON message USING hash (originid);
CREATE INDEX message_time_btree ON message USING btree (time);

--------------------------------------------------------
-- Oppretter et view
--------------------------------------------------------
DROP VIEW message_view;

CREATE VIEW message_view AS
SELECT originid,typeid,type.systemid,message.priority,category,time FROM origin
JOIN message ON originid=origin.id JOIN type ON typeid=type.id;

GRANT ALL ON message_view TO navlogadmin;
GRANT SELECT ON message_view TO navlogweb;

--------------------------------------------------------
-- Setter inn alle prioritetene
--------------------------------------------------------

insert into priority(id, priority, keyword, description) values (1, 0,'emergencies','System unusable');
insert into priority(id, priority, keyword, description) values (2, 1,'alerts','Immediate action needed');
insert into priority(id, priority, keyword, description) values (3, 2,'critical','Critical conditions');
insert into priority(id, priority, keyword, description) values (4, 3,'errors','Error conditions');
insert into priority(id, priority, keyword, description) values (5, 4,'warnings','Warning conditions');
insert into priority(id, priority, keyword, description) values (6, 5,'notifications','Normal but significant condition');
insert into priority(id, priority, keyword, description) values (7, 6,'informational','Informational messages only');
insert into priority(id, priority, keyword, description) values (8, 7,'debugging','Debugging messages');

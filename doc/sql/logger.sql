--------------------------------------------------------
-- priority
-- Prioritetsnivå og beskrivelser
--------------------------------------------------------

DROP TABLE priority;

CREATE TABLE priority (
  id INTEGER PRIMARY KEY,
  priority INTEGER NOT NULL,
  keyword VARCHAR UNIQUE NOT NULL,
  description VARCHAR
);

--------------------------------------------------------
-- type
-- Typer meldinger, sterkt influert av syslog
--------------------------------------------------------

DROP TABLE type;
DROP SEQUENCE type_id_seq;

CREATE TABLE type (
  id SERIAL PRIMARY KEY,
  facility VARCHAR NOT NULL,
  mnemonic VARCHAR NOT NULL,
  priorityid INTEGER REFERENCES priority (id) ON DELETE SET NULL ON UPDATE CASCADE,
  UNIQUE(facility,mnemonic)
);

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
  name VARCHAR UNIQUE NOT NULL,
  category VARCHAR
);

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
  message VARCHAR
);

--------------------------------------------------------
-- errorerror
-- Feilmeldinger som ikke er på riktig format blir blant
-- lagt her. Andre ting også.
--------------------------------------------------------

DROP TABLE errorerror;
DROP SEQUENCE errorerror_id_seq;

CREATE TABLE errorerror (
  id SERIAL PRIMARY KEY,
  message VARCHAR
);

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
SELECT originid,typeid,message.priority,category,time FROM origin
JOIN message ON originid=origin.id JOIN type ON typeid=type.id;

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

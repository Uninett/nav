--------------------------------------------------------
-- priority
-- PrioritY levels and descriptions
--------------------------------------------------------

DROP TABLE priority;

CREATE TABLE priority (
  priority VARCHAR PRIMARY KEY, -- like greit å la den vare tekst
  keyword VARCHAR UNIQUE NOT NULL,
  description VARCHAR
);

--------------------------------------------------------
-- type
-- Types of messages, ala syslog
--------------------------------------------------------

DROP TABLE type;

CREATE TABLE type (
  type VARCHAR PRIMARY KEY NOT NULL,
  priority INTEGER REFERENCES priority (priority) ON DELETE SET NULL ON UPDATE CASCADE,
);

--------------------------------------------------------
-- category
-- Categorising of origins
--------------------------------------------------------

DROP TABLE category;

CREATE TABLE category (
  category VARCHAR PRIMARY KEY NOT NULL
);

--------------------------------------------------------
-- origin
-- Origins, senders of messages
--------------------------------------------------------

DROP TABLE origin;

CREATE TABLE origin (
  name VARCHAR PRIMARY KEY NOT NULL,
  category VARCHAR
);

--------------------------------------------------------
-- message
-- The messages 
-- time, origin, priority, type and message text.
--------------------------------------------------------

DROP TABLE message;
DROP SEQUENCE message_id_seq;

CREATE TABLE message (
  id SERIAL PRIMARY KEY,
  time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  origin INTEGER NOT NULL REFERENCES origin (origin) ON UPDATE CASCADE ON DELETE SET NULL,
  priority INTEGER REFERENCES priority (priority) ON UPDATE CASCADE ON DELETE SET NULL, -- for overlagring av defaultverdier
  type VARCHAR NOT NULL REFERENCES type (type) ON UPDATE CASCADE ON DELETE SET NULL,
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

CREATE INDEX message_type_hash ON message USING hash (type);
CREATE INDEX message_origin_hash ON message USING hash (origin);
CREATE INDEX message_time_btree ON message USING btree (time);

--------------------------------------------------------
-- Oppretter et view
--------------------------------------------------------
DROP VIEW message_view;

CREATE VIEW message_view AS
SELECT origin,type,message.priority,category,time 
FROM origin INNER JOIN message USING (origin) INNER JOIN type USING (type);

--------------------------------------------------------
-- Setter inn alle prioritetene
--------------------------------------------------------

insert into priority(priority, keyword, description) values (0,'emergencies','System unusable');
insert into priority(priority, keyword, description) values (1,'alerts','Immediate action needed');
insert into priority(priority, keyword, description) values (2,'critical','Critical conditions');
insert into priority(priority, keyword, description) values (3,'errors','Error conditions');
insert into priority(priority, keyword, description) values (4,'warnings','Warning conditions');
insert into priority(priority, keyword, description) values (5,'notifications','Normal but significant condition');
insert into priority(priority, keyword, description) values (6,'informational','Informational messages only');
insert into priority(priority, keyword, description) values (7,'debugging','Debugging messages');


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

--------------------------------------------------------
-- priority
-- Priority levels and descriptions
--------------------------------------------------------

CREATE TABLE priority (
  priority INTEGER PRIMARY KEY,
  keyword VARCHAR UNIQUE NOT NULL,
  description VARCHAR
);

--------------------------------------------------------
-- log_message_type
-- Types of messages, ala syslog
--------------------------------------------------------

CREATE TABLE log_message_type (
  type SERIAL PRIMARY KEY NOT NULL,
  priority INTEGER REFERENCES priority (priority) ON DELETE SET NULL ON UPDATE CASCADE,
  facility VARCHAR NOT NULL,
  mnemonic VARCHAR NOT NULL,
  UNIQUE (priority, facility, mnemonic)
);

--------------------------------------------------------
-- category
-- Categorising of origins
--------------------------------------------------------

CREATE TABLE category (
  category VARCHAR PRIMARY KEY NOT NULL
);

--------------------------------------------------------
-- origin
-- Origins, senders of messages
--------------------------------------------------------

CREATE TABLE origin (
  origin SERIAL PRIMARY KEY NOT NULL,
  name VARCHAR NOT NULL,
  category VARCHAR REFERENCES category(category) ON DELETE SET NULL ON UPDATE CASCADE
);

--------------------------------------------------------
-- log_message
-- The log messages 
-- time, origin, priority, type and message text.
--------------------------------------------------------

CREATE TABLE log_message (
  id SERIAL PRIMARY KEY,
  time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  origin INTEGER NOT NULL REFERENCES origin (origin) ON UPDATE CASCADE ON DELETE SET NULL,
  newpriority INTEGER REFERENCES priority (priority) ON UPDATE CASCADE ON DELETE SET NULL, -- for overlagring av defaultverdier
  type INTEGER NOT NULL REFERENCES log_message_type (type) ON UPDATE CASCADE ON DELETE SET NULL,
  message VARCHAR
);

--------------------------------------------------------
-- errorerror
-- Error messages that couldn't be parsed correctly are
-- put here.  Other stuff also.
--------------------------------------------------------

CREATE TABLE errorerror (
  id SERIAL PRIMARY KEY,
  message VARCHAR
);

--------------------------------------------------------
-- Create a view (wow, really?)
--------------------------------------------------------

CREATE VIEW message_view AS
SELECT origin,type,newpriority,category,time 
FROM origin INNER JOIN log_message USING (origin);

--------------------------------------------------------
-- Insert default priority levels
--------------------------------------------------------

insert into priority(priority, keyword, description) values (0,'emergencies','System unusable');
insert into priority(priority, keyword, description) values (1,'alerts','Immediate action needed');
insert into priority(priority, keyword, description) values (2,'critical','Critical conditions');
insert into priority(priority, keyword, description) values (3,'errors','Error conditions');
insert into priority(priority, keyword, description) values (4,'warnings','Warning conditions');
insert into priority(priority, keyword, description) values (5,'notifications','Normal but significant condition');
insert into priority(priority, keyword, description) values (6,'informational','Informational messages only');
insert into priority(priority, keyword, description) values (7,'debugging','Debugging messages');




-- DROP --

drop table meldinger;
drop sequence meldinger_id_seq;

-- CREATE --

create table meldinger(
       id serial primary key,
       tid timestamp not null,
       boks varchar(30) not null,
       bokstype varchar(5),
       prioritet char(1),
       type varchar(50),
       beskrivelse varchar(200));

create table feillogg(
       id serial primary key,
       logg varchar(255) not null);

create table prioriteter(
       prioritet smallint primary key,
       stikkord varchar(16) not null,
       beskrivelse varchar(32));

-- INDEX --

CREATE INDEX meldinger_tid_btree ON meldinger USING btree (tid);
CREATE INDEX meldinger_tid_hash ON meldinger USING hash (boks);
CREATE INDEX meldinger_type_hash ON meldinger USING hash (type);

-- GRANT --

grant all on meldinger to syslogadmin;
grant all on feillogg to syslogadmin;
grant all on prioriteter to syslogadmin;

-- INSERT --

insert into prioriteter(prioritet, stikkord, beskrivelse) values (0,'emergencies','System unusable');
insert into prioriteter(prioritet, stikkord, beskrivelse) values (1,'alerts','Immediate action needed');
insert into prioriteter(prioritet, stikkord, beskrivelse) values (2,'critical','Critical conditions');
insert into prioriteter(prioritet, stikkord, beskrivelse) values (3,'errors','Error conditions');
insert into prioriteter(prioritet, stikkord, beskrivelse) values (4,'warnings','Warning conditions');
insert into prioriteter(prioritet, stikkord, beskrivelse) values (5,'notifications','Normal but significant condition');
insert into prioriteter(prioritet, stikkord, beskrivelse) values (6,'informational','Informational messages only');
insert into prioriteter(prioritet, stikkord, beskrivelse) values (7,'debugging','Debugging messages');

grant all on meldinger to syslogadmin;
grant all on prioriteter to syslogadmin;
/*

SQL Initialiserings skript.

Dette skriptet sletter ALLE DATA, og legger inn tabellene på nytt.

Kjøres på denne måten:

psql <databasenavn f.eks nav> -f nav.sql

*/

-- DELETE OLD TABLES

DROP SEQUENCE brukergruppeid;
DROP INDEX brukergruppe_pk;
DROP TABLE Brukergruppe;

DROP SEQUENCE brukerid;
DROP INDEX bruker_pk;
DROP INDEX bruker_idx;
DROP TABLE Bruker;

DROP INDEX brukertilgruppe_pk;
DROP TABLE BrukerTilGruppe;

DROP SEQUENCE alarmadresseid;
DROP INDEX alarmadresse_pk;
DROP TABLE Alarmadresse;

DROP SEQUENCE brukerprofilid;
DROP INDEX brukerprofil_pk;
DROP TABLE Brukerprofil;

DROP SEQUENCE tidsperiodeid;
DROP INDEX tidsperiode_pk;
DROP TABLE Tidsperiode;

DROP INDEX varsleadresse_pk;
DROP TABLE VarsleAdresse;

DROP SEQUENCE utstyrgruppeid;
DROP INDEX utstyrgruppe_pk;
DROP TABLE Utstyrgruppe;

DROP SEQUENCE utstyrfilterid;
DROP INDEX utstyrfilter_pk;
DROP TABLE Utstyrfilter;

DROP INDEX rettighet_pk;
DROP TABLE Rettighet;

DROP INDEX brukerrettighet_pk;
DROP TABLE BrukerRettighet;

DROP SEQUENCE filtermatchid;
DROP INDEX filtermatch_pk;
DROP TABLE FilterMatch;

DROP INDEX defaultutstyr_pk;
DROP TABLE DefaultUtstyr;

DROP INDEX overvaakutstyr_pk;
DROP TABLE OvervaakUtstyr;

DROP SEQUENCE utfpriority;
DROP INDEX gruppetilfilter_pk;
DROP TABLE GruppeTilFilter;


-- TABLE DEFINITIONS

CREATE SEQUENCE brukergruppeid;
CREATE TABLE Brukergruppe (
       id integer NOT NULL DEFAULT nextval('brukergruppeid'),
       navn varchar,
       descr varchar,

       CONSTRAINT brukergruppe_pk PRIMARY KEY (id)
);

CREATE SEQUENCE brukerid;
CREATE TABLE Bruker (
       id integer NOT NULL DEFAULT nextval('brukerid'),
       admin integer NOT NULL DEFAULT 1,
       brukernavn varchar CONSTRAINT brukernavn_uniq UNIQUE,
       aktivProfil integer,
       navn varchar,
       passord varchar,
       sms boolean DEFAULT true,
       
       CONSTRAINT bruker_pk PRIMARY KEY (id)
);
CREATE INDEX bruker_idx ON Bruker(brukernavn);

CREATE TABLE BrukerTilGruppe (
       brukerid integer,
       gruppeid integer,
       
       CONSTRAINT brukertilgruppe_pk PRIMARY KEY(brukerid, gruppeid),
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(brukerid) REFERENCES Bruker(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE, 
       CONSTRAINT gruppe_eksisterer
		  FOREIGN KEY(gruppeid) REFERENCES Brukergruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

CREATE SEQUENCE alarmadresseid;
CREATE TABLE Alarmadresse (
       id integer NOT NULL DEFAULT nextval('alarmadresseid'),
       type integer,
       adresse varchar,
       brukerid integer,

       CONSTRAINT alarmadresse_pk PRIMARY KEY(id),
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(brukerid) REFERENCES Bruker(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);


CREATE SEQUENCE brukerprofilid;
CREATE TABLE Brukerprofil (
       id integer NOT NULL DEFAULT nextval('brukerprofilid'),
       brukerid integer NOT NULL,
       navn varchar,

       CONSTRAINT brukerprofil_pk PRIMARY KEY(id),
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(brukerid) REFERENCES Bruker(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

ALTER TABLE Bruker ADD
       CONSTRAINT brukerprofil_eksisterer
		  FOREIGN KEY(aktivProfil) REFERENCES Brukerprofil(id)
		  ON DELETE SET NULL
		  ON UPDATE CASCADE;

CREATE SEQUENCE tidsperiodeid;
CREATE TABLE Tidsperiode (
       id integer NOT NULL DEFAULT nextval('tidsperiodeid'),
       brukerprofilid integer NOT NULL,
       starttid time,
       helg integer,

       CONSTRAINT tidsperiode_pk PRIMARY KEY(id),
       CONSTRAINT brukerprofil_eksisterer
		  FOREIGN KEY(brukerprofilid) REFERENCES Brukerprofil(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

CREATE TABLE VarsleAdresse (
       alarmadresseid integer NOT NULL,
       tidsperiodeid integer NOT NULL,
       vent boolean,

       CONSTRAINT varsleadresse_pk PRIMARY KEY(alarmadresseid, tidsperiodeid),
       CONSTRAINT alarmadresse_eksisterer
		  FOREIGN KEY (alarmadresseid) REFERENCES Alarmadresse(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

CREATE SEQUENCE utstyrfilterid;
CREATE TABLE Utstyrfilter (
       id integer NOT NULL DEFAULT nextval('utstyrfilter'),
       brukerid integer,
       navn varchar,

       CONSTRAINT utstyrfilter_pk PRIMARY KEY(id),
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(brukerid) REFERENCES Bruker(id)
		  ON DELETE SET NULL 
		  ON UPDATE CASCADE
);

CREATE SEQUENCE utstyrgruppeid;
CREATE TABLE Utstyrgruppe (
       id integer NOT NULL DEFAULT nextval('utstyrgruppeid'),
       navn varchar,
       descr varchar,

       CONSTRAINT utstyrgruppe_pk PRIMARY KEY(id)
);

CREATE TABLE Rettighet (
       brukergruppeid integer NOT NULL,
       utstyrgruppeid integer NOT NULL,
       CONSTRAINT rettighet_pk PRIMARY KEY(brukergruppeid, utstyrgruppeid),
       CONSTRAINT brukergruppe_eksisterer
		  FOREIGN KEY(brukergruppeid) REFERENCES Brukergruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT utstyrgruppe_eksisterer
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

CREATE TABLE BrukerRettighet (
       brukerid integer NOT NULL,
       utstyrgruppeid integer NOT NULL,
       CONSTRAINT brukerrettighet_pk PRIMARY KEY(brukerid, utstyrgruppeid),
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(brukerid) REFERENCES Bruker(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT utstyrgruppe_eksisterer
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

CREATE SEQUENCE filtermatchid;
CREATE TABLE FilterMatch (
       id integer NOT NULL DEFAULT nextval('filtermatchid'),
       utstyrfilterid integer NOT NULL,
       matchfelt integer,
       matchtype integer,
       verdi varchar,
       
       CONSTRAINT filtermatch_pk PRIMARY KEY(id),
       CONSTRAINT utstyrfilter_eksisterer
		  FOREIGN KEY(utstyrfilterid) REFERENCES Utstyrfilter(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);


CREATE TABLE DefaultUtstyr (
       brukergruppeid integer NOT NULL,
       utstyrfilterid integer NOT NULL,

       CONSTRAINT defaultutstyr_pk PRIMARY KEY (brukergruppeid, utstyrfilterid),
       CONSTRAINT utstyrfilter_eksisterer
		  FOREIGN KEY(utstyrfilterid) REFERENCES Utstyrfilter(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT brukergruppe_eksisterer
		  FOREIGN KEY(brukergruppeid) REFERENCES Brukergruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

CREATE TABLE OvervaakUtstyr (
       tidsperiodeid integer NOT NULL,
       utstyrgruppeid integer NOT NULL,
       
       CONSTRAINT overvaakutstyr_pk PRIMARY KEY(tidsperiodeid, utstyrgruppeid),
       CONSTRAINT tidsperiode_eksisterer
		  FOREIGN KEY(tidsperiodeid) REFERENCES Tidsperiode(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT utstyrgruppe_eksisterer
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE  
);


CREATE SEQUENCE utfpriority;
CREATE TABLE GruppeTilFilter (
       inkluder boolean NOT NULL,
       prioritet integer NOT NULL DEFAULT nextval('utfpriority') 
       CONSTRAINT priUnique UNIQUE,
       utstyrfilterid integer NOT NULL,
       utstyrgruppeid integer NOT NULL,

       CONSTRAINT gruppetilfilter_pk PRIMARY KEY(utstyrfilterid, utstyrgruppeid),
       CONSTRAINT utstyrgruppeid_eksisterer 
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT utstyrfilter_eksisterer 
		  FOREIGN KEY(utstyrfilterid) REFERENCES Utstyrfilter(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);


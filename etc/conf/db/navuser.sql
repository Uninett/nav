/*

SQL Initialiserings skript.

Dette skriptet sletter ALLE DATA, og legger inn tabellene paa nytt.

UML-diagram for databasen finnes her: 
navme/doc/navuser/system/databasemodell.pdf

Kjoeres paa denne maaten:

psql navuser -f nav.sql

*/

-- DELETE OLD TABLES


DROP TABLE Wapkey CASCADE;

DROP SEQUENCE loggid;
DROP TABLE Logg CASCADE;

DROP SEQUENCE brukergruppeid;
DROP TABLE Brukergruppe CASCADE;

DROP SEQUENCE brukerid;
DROP TABLE Bruker CASCADE;

DROP TABLE BrukerTilGruppe CASCADE;

DROP SEQUENCE alarmadresseid;
DROP TABLE Alarmadresse CASCADE;

DROP SEQUENCE brukerprofilid;
DROP TABLE Brukerprofil CASCADE;

DROP SEQUENCE tidsperiodeid;
DROP TABLE Tidsperiode CASCADE;

DROP SEQUENCE utstyrgruppeid;
DROP TABLE Utstyrgruppe CASCADE;

DROP SEQUENCE utstyrfilterid;
DROP TABLE Utstyrfilter CASCADE;

DROP TABLE Varsle CASCADE;

DROP TABLE Rettighet CASCADE;

DROP TABLE BrukerRettighet CASCADE;

DROP SEQUENCE filtermatchid;
DROP TABLE FilterMatch CASCADE;

DROP TABLE DefaultUtstyr CASCADE;

DROP TABLE GruppeTilFilter CASCADE;



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
       lang varchar DEFAULT 'no',
       aktivProfil integer,
       navn varchar,
       passord varchar,
       sms boolean DEFAULT true,
       kolengde integer NOT NULL DEFAULT 50,

       CONSTRAINT bruker_pk PRIMARY KEY (id)
);
CREATE INDEX bruker_idx ON Bruker(brukernavn);



CREATE TABLE Wapkey (
       brukerid integer NOT NULL,
       key varchar,
       
       CONSTRAINT wapkey_bruker_pk PRIMARY KEY(brukerid),     
       
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(brukerid) REFERENCES Bruker(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);

CREATE SEQUENCE loggid;
CREATE TABLE Logg (
		id integer NOT NULL DEFAULT nextval('loggid'),
       brukerid integer NOT NULL,
       type integer,
       tid timestamptz,       
       descr varchar,
       
       CONSTRAINT loggid_pk PRIMARY KEY(id),     
       
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(brukerid) REFERENCES Bruker(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);


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
       tid time,
       ukedag integer,
       uketid time,

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
       brukerid integer,

       CONSTRAINT utstyrgruppe_pk PRIMARY KEY(id),
       CONSTRAINT bruker_eksisterer
		  FOREIGN KEY(brukerid) REFERENCES Bruker(id)
		  ON DELETE SET NULL 
		  ON UPDATE CASCADE
);


CREATE TABLE Varsle (
	alarmadresseid integer NOT NULL,
	tidsperiodeid integer NOT NULL,
	utstyrgruppeid integer NOT NULL,
	vent integer,

	CONSTRAINT varsleadresse_pk PRIMARY KEY(alarmadresseid, tidsperiodeid, utstyrgruppeid),
	CONSTRAINT alarmadresse_eksisterer
		FOREIGN KEY (alarmadresseid) REFERENCES Alarmadresse(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE,

	CONSTRAINT tidsperiode_eksisterer
		FOREIGN KEY(tidsperiodeid) REFERENCES Tidsperiode(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE,
	CONSTRAINT utstyrgruppe_eksisterer
		FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
			ON DELETE CASCADE
			ON UPDATE CASCADE  
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
       utstyrgruppeid integer NOT NULL,

       CONSTRAINT defaultutstyr_pk PRIMARY KEY (brukergruppeid, utstyrgruppeid),
       CONSTRAINT utstyrgruppe_eksisterer
		  FOREIGN KEY(utstyrgruppeid) REFERENCES Utstyrgruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE,
       CONSTRAINT brukergruppe_eksisterer
		  FOREIGN KEY(brukergruppeid) REFERENCES Brukergruppe(id)
		  ON DELETE CASCADE
		  ON UPDATE CASCADE
);



CREATE TABLE GruppeTilFilter (
       inkluder boolean NOT NULL DEFAULT true,
       positiv boolean NOT NULL DEFAULT true,
       prioritet integer NOT NULL,
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


############################################################################# 
$Id: eMotd.sql,v 1.1 2003/06/16 08:00:53 bgrotan Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/eMotd/scripts/eMotd.sql,v $
############################################################################# 
# enhanced Message of the day - sql-import-script
# cut'n'paste sql for creating neceserry database-tables
#
#
#
############################################################################# 

CREATE TABLE eMOTD (
        msgid SERIAL PRIMARY KEY,
        bruker VARCHAR REFERENCES bruker NOT NULL,
        date TIMESTAMP NOT NULL,
        date_start TIMESTAMP NOT NULL,
        date_end TIMESTAMP NOT NULL,
        type VARCHAR(10) NOT NULL,
        title VARCHAR(250) NOT NULL,
        header_txt VARCHAR NULL,
        body_txt TEXT NULL
); 

CREATE TABLE eMOTD_ref (
	msgid REFERENCES eMOTD UNIQUE,
	key VARCHAR NOT NULL UNIQUE,
	value VARCHAR NOT NULL,
);

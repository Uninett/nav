############################################################################# 
$Id: eMotd.sql,v 1.2 2003/06/16 08:42:49 bgrotan Exp $
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
        bruker VARCHAR NOT NULL,
        date TIMESTAMP NOT NULL,
        date_start TIMESTAMP NOT NULL,
        date_end TIMESTAMP NOT NULL,
        type VARCHAR(10) NOT NULL,
        title VARCHAR(250) NOT NULL,
        header_txt VARCHAR NULL,
        body_txt TEXT NULL
); 

CREATE TABLE eMOTD_ref (
	msgid SERIAL REFERENCES eMOTD 
	      ON UPDATE CASCADE 
              ON DELETE SET NULL,
	key VARCHAR NOT NULL ,
	value VARCHAR NOT NULL,
	PRIMARY KEY (msgid,key)
);

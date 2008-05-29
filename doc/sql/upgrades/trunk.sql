/*
 *
 * This preliminary SQL script is designed to upgrade your NAV
 * database from version 3.4 to the current trunk revision (i.e. the
 * tip of the default development branch).  Please update this with
 * every change you make to the database initialization scripts.  It
 * will eventually become the update script for the next release.
 *
 * Also, if you are keeping your installation in sync with the default
 * branch, you should watch this file for changes and run them when
 * updating (check the diffs!)
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql manage <username>
 *
*/
------------------------------------------------------------------------------
-- mac watch table for storing watched mac addresses
------------------------------------------------------------------------------

CREATE TABLE macwatch (
  id SERIAL PRIMARY KEY,
  camid int REFERENCES cam(camid) ON DELETE CASCADE ON UPDATE CASCADE,
  mac macaddr NOT NULL,
  posted timestamp,
  userid int REFERENCES account(id) ON DELETE SET NULL ON UPDATE CASCADE,
  login varchar,
  description varchar,
  created timestamp default now()
);

INSERT INTO subsystem (name) VALUES ('macwatch');
INSERT INTO alerttype (eventtypeid, alerttype, alerttypedesc) VALUES
  ('info','macWarning','Mac appeared on port');


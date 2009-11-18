/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.5 to the current trunk revision (i.e. the tip of the default
 * development branch).  Please update this with every change you make to the
 * database initialization scripts.  It will eventually become the update
 * script for the next release.
 *
 * If you are keeping your installation in sync with the default branch, you
 * should watch this file for changes and run them when updating (check the
 * diffs!).  We also recommend running navschema.py on each schema upgrade,
 * to ensure that your database's search path is alway up to date.
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql nav <username>
 *
*/

BEGIN;
-- Insert schema changes here.

-- Force all foreign key constraints to follow the exact same naming
-- pattern: <tablename>_<column_name>_fkey 
--
-- This should change about 7 "wrongly" named foreign keys on the
-- netbox, accountalertqueue and log_message_type tables, and any
-- foreign key whose name has been automatically set to '$<number>' by
-- older versions of PostgreSQL.
UPDATE pg_constraint
SET conname=cl.relname || '_' || pa.attname || '_fkey'
FROM pg_class cl, pg_attribute pa, pg_namespace nsp
WHERE
  contype = 'f' AND
  conname <> (cl.relname || '_' || pa.attname || '_fkey') AND
  connamespace = nsp.oid AND
  nspname IN ('manage', 'profiles', 'arnold', 'logger', 'radius') AND
  conrelid = cl.oid AND
  pa.attrelid = cl.oid AND
  conkey[1] = pa.attnum
;

ALTER TABLE org DROP CONSTRAINT "org_parent_fkey";
ALTER TABLE org ADD CONSTRAINT org_parent_fkey 
                               FOREIGN KEY (parent) REFERENCES org (orgid)
                               ON UPDATE CASCADE;

-- Index to speed up ipdevinfo queries for the first cam entry from a box
CREATE INDEX cam_netboxid_start_time_btree ON cam USING btree (netboxid, start_time);

-- Remove product and deviceorder
ALTER TABLE device DROP COLUMN productid;
ALTER TABLE device DROP COLUMN deviceorderid;
ALTER TABLE device DROP COLUMN active;

DROP TABLE deviceorder;
DROP TABLE product;

-- Django needs a simple integer primary key in accountnavbar
ALTER TABLE accountnavbar DROP CONSTRAINT accountnavbar_pkey;
CREATE SEQUENCE accountnavbar_id_seq;
ALTER TABLE accountnavbar ADD COLUMN id integer NOT NULL PRIMARY KEY DEFAULT nextval('accountnavbar_id_seq');


-- Status preference tables
CREATE SEQUENCE statuspreference_id_seq START 1000;
CREATE TABLE statuspreference (
	id integer NOT NULL DEFAULT nextval('statuspreference_id_seq'),
	name varchar NOT NULL,
	position integer NOT NULL,
	type varchar NOT NULL,
	accountid integer NOT NULL,

	services varchar NOT NULL DEFAULT '',
	states varchar NOT NULL DEFAULT 'n,s',

	CONSTRAINT statuspreference_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_accountid_fkey
		FOREIGN KEY (accountid) REFERENCES Account(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE statuspref_id_seq OWNED BY statuspref.id;

CREATE SEQUENCE statuspreference_organization_id_seq;
CREATE TABLE statuspreference_organization (
	id integer NOT NULL DEFAULT nextval('statuspreference_organization_id_seq'),
	statuspreference_id integer NOT NULL,
	organization_id varchar NOT NULL,

	CONSTRAINT statuspreference_organization_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_organization_statuspreference_id_key
		UNIQUE(statuspreference_id, organization_id),
	CONSTRAINT statuspreference_organization_statuspreference_id_fkey
		FOREIGN KEY (statuspreference_id) REFERENCES statuspreference(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT statuspreference_organization_organization_id_fkey
		FOREIGN KEY (organization_id) REFERENCES manage.org(orgid)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE statuspref_org_id_seq OWNED BY statuspref_org.id;

CREATE SEQUENCE statuspreference_category_id_seq;
CREATE TABLE statuspreference_category (
	id integer NOT NULL DEFAULT nextval('statuspreference_category_id_seq'),
	statuspreference_id integer NOT NULL,
	category_id varchar NOT NULL,

	CONSTRAINT statuspreference_category_pkey PRIMARY KEY(id),
	CONSTRAINT statuspreference_category_statuspreference_id_key
		UNIQUE(statuspreference_id, category_id),
	CONSTRAINT statuspreference_category_statuspreference_id_fkey
		FOREIGN KEY (statuspreference_id) REFERENCES statuspreference(id)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	CONSTRAINT statuspreference_category_category_id_fkey
		FOREIGN KEY (category_id) REFERENCES manage.cat(catid)
		ON UPDATE CASCADE
		ON DELETE CASCADE
);
-- Only compatible with PostgreSQL >= 8.2:
-- ALTER SEQUENCE statuspreference_category_id_seq OWNED BY statuspreference_category.id;

-- StatusPreferences for Default user

INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (1, 'IP devices down', 1, 'netbox', 0, 'n');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (2, 'IP devices in shadow', 2, 'netbox', 0, 's');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (3, 'IP devices on maintenance', 3, 'netbox_maintenance', 0, 'n,s');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (4, 'Modules down/in shadow', 4, 'module', 0, 'n,s');
INSERT INTO statuspreference (id, name, position, type, accountid, states) VALUES (5, 'Services down', 5, 'service', 0, 'n,s');


-- DeviceHistory rewrite 
-- Django needs an id field for every table.
--
CREATE SEQUENCE manage.eventqvar_id_seq;
ALTER TABLE eventqvar ADD COLUMN id integer NOT NULL
	DEFAULT nextval('eventqvar_id_seq')
	CONSTRAINT eventqvar_pkey PRIMARY KEY;


-- Remove floating devices.
-- Devices that don't have a serial and no connected modules or netboxes.
-- Triggers on delete on module and netbox.
CREATE OR REPLACE FUNCTION manage.remove_floating_devices() RETURNS TRIGGER AS '
    BEGIN
        DELETE FROM device WHERE
            deviceid NOT IN (SELECT deviceid FROM netbox) AND
            deviceid NOT IN (SELECT deviceid FROM module) AND
            serial IS NULL;
        RETURN NULL;
        END;
    ' language 'plpgsql';

CREATE TRIGGER trig_module_delete_prune_devices
    AFTER DELETE ON module
    FOR EACH STATEMENT
    EXECUTE PROCEDURE remove_floating_devices();

CREATE TRIGGER trig_netbox_delete_prune_devices
    AFTER DELETE ON netbox
    FOR EACH STATEMENT
    EXECUTE PROCEDURE remove_floating_devices();


COMMIT;

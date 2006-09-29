/*
 *
 * This preliminary SQL script is designed to upgrade your NAV database from
 * version 3.1 to the current trunk revision.  Please update this with every
 * change you make to the database initialization scripts.  It will eventually
 * become the update script for the next release.
 *
 * Also, if you are keeping your installation in sync with trunk, you should
 * watch this file for changes and run them when updating (check the diffs!)
 *
 * Connect to PostgreSQL as the postgres superuser or the nav database user
 * like this:
 *
 *  psql -f trunk.sql manage <username>
 *
*/

\c manage
------------------------------------------------------------------------------
-- messages/maintenance v2 tables
------------------------------------------------------------------------------

CREATE TABLE message (
    messageid SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    tech_description TEXT,
    publish_start TIMESTAMP,
    publish_end TIMESTAMP,
    author VARCHAR NOT NULL,
    last_changed TIMESTAMP,
    replaces_message INT REFERENCES message,
    replaced_by INT REFERENCES message
);

CREATE OR REPLACE FUNCTION message_replace() RETURNS TRIGGER AS '
    DECLARE
        -- Old replaced_by value of the message beeing replaced
        old_replaced_by INTEGER;
    BEGIN
        -- Remove references that are no longer correct
        IF TG_OP = ''UPDATE'' THEN
            IF OLD.replaces_message <> NEW.replaces_message OR
                (OLD.replaces_message IS NOT NULL AND NEW.replaces_message IS NULL) THEN
                EXECUTE ''UPDATE message SET replaced_by = NULL WHERE messageid = ''
                || quote_literal(OLD.replaces_message);
            END IF;
        END IF;

        -- It does not replace any message, exit
        IF NEW.replaces_message IS NULL THEN
            RETURN NEW;
        END IF;

        -- Update the replaced_by field of the replaced message with a
        -- reference to the replacer
        SELECT INTO old_replaced_by replaced_by FROM message
            WHERE messageid = NEW.replaces_message;
        IF old_replaced_by <> NEW.messageid OR old_replaced_by IS NULL THEN
            EXECUTE ''UPDATE message SET replaced_by = ''
            || quote_literal(NEW.messageid)
            || '' WHERE messageid = ''
            || quote_literal(NEW.replaces_message);
        END IF;

        RETURN NEW;
        END;
    ' language 'plpgsql';

CREATE TRIGGER trig_message_replace
	AFTER INSERT OR UPDATE ON message
	FOR EACH ROW
	EXECUTE PROCEDURE message_replace();

CREATE OR REPLACE VIEW message_with_replaced AS
    SELECT
        m.messageid, m.title,
	m.description, m.tech_description,
        m.publish_start, m.publish_end, m.author, m.last_changed,
        m.replaces_message, m.replaced_by,
        rm.title AS replaces_message_title,
        rm.description AS replaces_message_description,
        rm.tech_description AS replaces_message_tech_description,
        rm.publish_start AS replaces_message_publish_start,
        rm.publish_end AS replaces_message_publish_end,
        rm.author AS replaces_message_author,
        rm.last_changed AS replaces_message_last_changed,
        rb.title AS replaced_by_title,
        rb.description AS replaced_by_description,
        rb.tech_description AS replaced_by_tech_description,
        rb.publish_start AS replaced_by_publish_start,
        rb.publish_end AS replaced_by_publish_end,
        rb.author AS replaced_by_author,
        rb.last_changed AS replaced_by_last_changed
    FROM
    	message m LEFT JOIN message rm ON (m.replaces_message = rm.messageid)
    	LEFT JOIN message rb ON (m.replaced_by = rb.messageid);

CREATE TABLE maint_task (
    maint_taskid SERIAL PRIMARY KEY,
    maint_start TIMESTAMP NOT NULL,
    maint_end TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    author VARCHAR NOT NULL,
    state VARCHAR NOT NULL
);

CREATE TABLE maint_component (
    maint_taskid INT NOT NULL REFERENCES maint_task ON UPDATE CASCADE ON DELETE CASCADE,
    key VARCHAR NOT NULL,
    value VARCHAR NOT NULL,
    PRIMARY KEY (maint_taskid, key, value)
);

CREATE TABLE message_to_maint_task (
    messageid INT NOT NULL REFERENCES message ON UPDATE CASCADE ON DELETE CASCADE,
    maint_taskid INT NOT NULL REFERENCES maint_task ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (messageid, maint_taskid)
);

CREATE OR REPLACE VIEW maint AS
    SELECT * FROM maint_task NATURAL JOIN maint_component;


--------------------
--- Data changes ---
--------------------
UPDATE snmpoid 
SET oidkey='hpFwVer', desc='Firmware revision number' 
WHERE snmpoid = '1.3.6.1.4.1.11.2.14.11.5.1.1.4.0'
  AND oidkey='hpHwVer';

INSERT INTO subsystem (name) VALUES ('maintenance');

\c navprofiles
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/js/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/style/.*');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/messages2/(active|historic|planned|view|rss)\\b');
INSERT INTO AccountGroupPrivilege (accountgroupid, privilegeid, target) VALUES (2, 2, '^/maintenance2/(calendar|active|historic|planned|view)\\b');

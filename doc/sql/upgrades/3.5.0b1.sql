/*
 *
 * This SQL script is designed to upgrade your NAV database from
 * version 3.4 to 3.5.
 *
 * *************** NB NB NB NB NB NB NB ***************
 *
 * This upgrade scripts assumes you have merged your NAV databases
 * into a single, multi-namespaced database.  If you haven't, please
 * read the instructions in doc/sql/upgrades/README .  A helper script
 * exists to help you merge your databases: doc/sql/mergedb.sh .
 *
 * *************** NB NB NB NB NB NB NB ***************
 *
 * Connect to PostgreSQL and run this script as the nav database owner
 * like this:
 *
 *  psql -f 3.5.0b1.sql <db_name> <username>
 *
*/

BEGIN;
SET client_min_messages TO warning;

-- Rename logger tables to avoid naming confusion with manage schema.
ALTER TABLE logger.message RENAME TO log_message;

ALTER TABLE logger.message_id_seq RENAME TO log_message_id_seq;
ALTER INDEX logger.message_pkey RENAME TO log_message_pkey;
ALTER INDEX logger.message_origin_btree RENAME TO log_message_origin_btree;
ALTER INDEX logger.message_time_btree RENAME TO log_message_time_btree;
ALTER INDEX logger.message_type_btree RENAME TO log_message_type_btree;

ALTER TABLE logger.type RENAME TO log_message_type;
ALTER TABLE logger.type_type_seq RENAME TO log_message_type_type_seq;
ALTER INDEX logger.type_pkey RENAME TO log_message_type_pkey;
ALTER INDEX logger.type_priority_key RENAME TO log_message_type_priority_key;

-- In lack of an ALTER TABLE RENAME CONSTRAINT in pg8.1 we drop and
-- re-create constraints.  Do this to make sure constraints are named
-- according to the table name changes above.
ALTER TABLE logger.log_message DROP CONSTRAINT message_newpriority_fkey;
ALTER TABLE logger.log_message DROP CONSTRAINT message_origin_fkey;
ALTER TABLE logger.log_message DROP CONSTRAINT message_type_fkey;
ALTER TABLE logger.log_message ADD CONSTRAINT log_message_newpriority_fkey
  FOREIGN KEY (newpriority) REFERENCES priority (priority) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE logger.log_message ADD CONSTRAINT log_message_origin_fkey
  FOREIGN KEY (origin) REFERENCES origin (origin) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE logger.log_message ADD CONSTRAINT log_message_type_fkey
  FOREIGN KEY (type) REFERENCES log_message_type (type) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE logger.log_message_type DROP CONSTRAINT type_priority_fkey;
ALTER TABLE logger.log_message_type ADD CONSTRAINT type_priority_fkey
  FOREIGN KEY (priority) REFERENCES priority(priority) ON UPDATE CASCADE ON DELETE SET NULL;

-- combined index for quick lookups when expiring old records.
CREATE INDEX log_message_expiration_btree ON logger.log_message USING btree(newpriority, time);

-- Drop obsolete vlanPlot tables
DROP TABLE vp_netbox_xy;
DROP TABLE vp_netbox_grp;
DROP TABLE vp_netbox_grp_info;

-- Add closed flag to alertq
ALTER TABLE alertq ADD closed BOOLEAN;

--------------------------------------------------------------------------------
-- profiles clean-up:
-- * Rename tables in profiles so they all are english.
-- * Rename indexes.
-- * Add id column to tables that django can use as primary key.
-- * Drop keys and re-add them with new name.
-- * Explicitly name keys/indexes/sequences. Use what Postgres would have named
--   them by default
-- * Delete "old" alerts that where keept for debuging

DELETE FROM alertq WHERE alertqid <= (SELECT lastalertqid FROM alertengine LIMIT 1);

-- Drop some unused tables
DROP TABLE defaultutstyr;
DROP TABLE defaultfilter;
DROP TABLE brukerrettighet;
DROP TABLE logg;
DROP TABLE alertengine;
DROP SEQUENCE logg_id_seq;

-- Remove copy_default_preferences trigger
DROP TRIGGER insert_account ON account;
DROP FUNCTION copy_default_preferences();

-- We wan't english names for everything so here goes:
ALTER TABLE accountingroup RENAME TO accountgroup_accounts;
ALTER TABLE accountgroup_accounts RENAME accountid TO account_id;
ALTER TABLE accountgroup_accounts RENAME groupid TO accountgroup_id;

ALTER TABLE rettighet RENAME TO filtergroup_group_permission;
ALTER TABLE filtergroup_group_permission RENAME utstyrgruppeid TO filtergroup_id;
ALTER TABLE filtergroup_group_permission RENAME accountgroupid TO accountgroup_id;

ALTER TABLE alarmadresse RENAME TO alertaddress;
ALTER TABLE alertaddress RENAME adresse TO address;

ALTER TABLE preference RENAME TO alertpreference;
ALTER TABLE alertpreference DROP COLUMN queuelength;

ALTER TABLE brukerprofil RENAME TO alertprofile;
ALTER TABLE alertprofile RENAME navn TO name;
ALTER TABLE alertprofile RENAME tid TO daily_dispatch_time;
ALTER TABLE alertprofile RENAME ukedag TO weekly_dispatch_day;
ALTER TABLE alertprofile RENAME uketid TO weekly_dispatch_time;

ALTER TABLE tidsperiode RENAME TO timeperiod;
ALTER TABLE timeperiod RENAME brukerprofilid TO alert_profile_id;
ALTER TABLE timeperiod RENAME starttid TO start_time;
ALTER TABLE timeperiod RENAME helg TO valid_during;

ALTER TABLE varsle RENAME TO alertsubscription;
ALTER TABLE alertsubscription RENAME alarmadresseid TO alert_address_id;
ALTER TABLE alertsubscription RENAME tidsperiodeid TO time_period_id;
ALTER TABLE alertsubscription RENAME utstyrgruppeid TO filter_group_id;
ALTER TABLE alertsubscription RENAME vent TO subscription_type;
ALTER TABLE alertsubscription ADD ignore_closed_alerts BOOLEAN DEFAULT false;

ALTER TABLE gruppetilfilter RENAME TO filtergroupcontent;
ALTER TABLE filtergroupcontent RENAME inkluder TO include;
ALTER TABLE filtergroupcontent RENAME positiv TO positive;
ALTER TABLE filtergroupcontent RENAME prioritet TO priority;
ALTER TABLE filtergroupcontent RENAME utstyrfilterid TO filter_id;
ALTER TABLE filtergroupcontent RENAME utstyrgruppeid TO filter_group_id;

ALTER TABLE operator RENAME operatorid TO operator_id;
ALTER TABLE operator RENAME matchfieldid TO match_field_id;

ALTER TABLE filtermatch RENAME TO expression;
ALTER TABLE expression RENAME utstyrfilterid TO filter_id;
ALTER TABLE expression RENAME matchfelt TO match_field_id;
ALTER TABLE expression RENAME matchtype TO operator;
ALTER TABLE expression RENAME verdi TO value;

ALTER TABLE utstyrfilter RENAME TO filter;
ALTER TABLE filter RENAME accountid TO owner_id;
ALTER TABLE filter RENAME navn TO name;

ALTER TABLE utstyrgruppe RENAME TO filtergroup;
ALTER TABLE filtergroup RENAME accountid TO owner_id;
ALTER TABLE filtergroup RENAME navn TO name;

-- Make matchfields/expressions simpler:
--  * Remove value_category
--  * Remove template portion of value_name
ALTER TABLE matchfield RENAME matchfieldid TO id;
ALTER TABLE matchfield RENAME valueid TO value_id;
ALTER TABLE matchfield RENAME valuename TO value_name;
ALTER TABLE matchfield RENAME valuehelp TO value_help;
ALTER TABLE matchfield RENAME valuecategory TO value_category;
ALTER TABLE matchfield RENAME valuesort TO value_sort;
ALTER TABLE matchfield RENAME listlimit TO list_limit;
ALTER TABLE matchfield RENAME datatype TO data_type;
ALTER TABLE matchfield RENAME showlist TO show_list;
ALTER TABLE matchfield DROP COLUMN value_category;
UPDATE matchfield SET value_name = regexp_replace(value_name, E'\\|.*$', '');

ALTER TABLE queue RENAME TO accountalertqueue;
ALTER TABLE accountalertqueue RENAME accountid TO account_id;
ALTER TABLE accountalertqueue RENAME alertid TO alert_id;
ALTER TABLE accountalertqueue RENAME time TO insertion_time;

ALTER TABLE filtergroup RENAME descr TO description;
ALTER TABLE matchfield RENAME descr TO description;

ALTER TABLE accountorg RENAME orgid TO organization_id;
ALTER TABLE accountorg RENAME accountid TO account_id;

-- Rename sequences so they match with the new english table names
-- NOTE Internally a sequence has a column named 'sequence_name' which keeps
-- the name of the sequence. This value will not be changed when renaming
-- sequences, and you can not use UPDATE to set it either.
ALTER TABLE alarmadresse_id_seq RENAME TO alertaddress_id_seq;
ALTER TABLE alertaddress ALTER COLUMN id SET DEFAULT nextval('alertaddress_id_seq');

ALTER TABLE brukerprofil_id_seq RENAME TO alertprofile_id_seq;
ALTER TABLE alertprofile ALTER COLUMN id SET DEFAULT nextval('alertprofile_id_seq');

ALTER TABLE tidsperiode_id_seq RENAME TO timeperiod_id_seq;
ALTER TABLE timeperiod ALTER COLUMN id SET DEFAULT nextval('timeperiod_id_seq');

ALTER TABLE filtermatch_id_seq RENAME TO expression_id_seq;
ALTER TABLE expression ALTER COLUMN id SET DEFAULT nextval('expression_id_seq');

ALTER TABLE utstyrfilter_id_seq RENAME TO filter_id_seq;
ALTER TABLE filter ALTER COLUMN id SET DEFAULT nextval('filter_id_seq');

ALTER TABLE utstyrgruppe_id_seq RENAME TO filtergroup_id_seq;
ALTER TABLE filtergroup ALTER COLUMN id SET DEFAULT nextval('filtergroup_id_seq');

ALTER TABLE queue_id_seq RENAME TO accountalertqueue_id_seq;
ALTER TABLE accountalertqueue ALTER COLUMN id SET DEFAULT nextval('accountalertqueue_id_seq');

-- operator_id_seq should really be called operator_operator_id_seq as it is a
-- sequence for the column operator_id in the table operator.
ALTER TABLE operator_id_seq RENAME TO operator_operator_id_seq;
ALTER TABLE operator ALTER COLUMN operator_id SET DEFAULT nextval('operator_operator_id_seq');


-- Django needs a single column it can treat as primary key :-(
ALTER TABLE accountgroup_accounts DROP CONSTRAINT accountingroup_pk;
CREATE SEQUENCE profiles.accountgroup_accounts_id_seq;
ALTER TABLE accountgroup_accounts ADD COLUMN id integer NOT NULL
	DEFAULT nextval('accountgroup_accounts_id_seq')
	CONSTRAINT accountgroup_accounts_pkey PRIMARY KEY;
ALTER TABLE accountgroup_accounts ADD CONSTRAINT accountgroup_accounts_account_id_key UNIQUE(account_id, accountgroup_id);

ALTER TABLE accountgroupprivilege DROP CONSTRAINT agprivilege_pk;
CREATE SEQUENCE profiles.accountgroupprivilege_id_seq;
ALTER TABLE accountgroupprivilege ADD COLUMN id integer NOT NULL
	DEFAULT nextval('accountgroupprivilege_id_seq')
	CONSTRAINT accountgroupprivilege_pkey PRIMARY KEY;
ALTER TABLE accountgroupprivilege ADD CONSTRAINT accountgroupprivilege_accountgroupid_key UNIQUE(accountgroupid, privilegeid, target);

ALTER TABLE accountorg DROP CONSTRAINT accountorg_pk;
CREATE SEQUENCE profiles.accountorg_id_seq;
ALTER TABLE accountorg ADD COLUMN id integer NOT NULL
	DEFAULT nextval('accountorg_id_seq')
	CONSTRAINT accountorg_pkey PRIMARY KEY;
ALTER TABLE accountorg ADD CONSTRAINT accountorg_accountid_key UNIQUE(account_id, organization_id);
ALTER TABLE accountorg DROP CONSTRAINT account_exists;
ALTER TABLE accountorg ADD CONSTRAINT accountorg_account_id_fkey
	FOREIGN KEY(account_id) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

-- Delete bougs accountorg entries before adding foreign key constraint
DELETE FROM accountorg WHERE organization_id NOT IN (SELECT orgid FROM org);

ALTER TABLE accountorg ADD CONSTRAINT accountorg_organization_id_fkey
	FOREIGN KEY (organization_id) REFERENCES manage.org(orgid)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

CREATE SEQUENCE profiles.accountproperty_id_seq;
ALTER TABLE accountproperty ADD COLUMN id integer NOT NULL
	DEFAULT nextval('accountproperty_id_seq')
	CONSTRAINT accountproperty_pkey PRIMARY KEY;

ALTER TABLE filtergroupcontent DROP CONSTRAINT gruppetilfilter_pk;
CREATE SEQUENCE profiles.filtergroupcontent_id_seq;
ALTER TABLE filtergroupcontent ADD COLUMN id integer NOT NULL
	DEFAULT nextval('filtergroupcontent_id_seq')
	CONSTRAINT filtergroupcontent_pkey PRIMARY KEY;
ALTER TABLE filtergroupcontent ADD CONSTRAINT filtergroupcontent_filter_id_key UNIQUE(filter_id, filter_group_id);

ALTER TABLE operator DROP CONSTRAINT operator_pk;
CREATE SEQUENCE profiles.operator_id_seq;
ALTER TABLE operator ADD COLUMN id integer NOT NULL
	DEFAULT nextval('operator_id_seq')
	CONSTRAINT operator_pkey PRIMARY KEY;
ALTER TABLE operator ADD CONSTRAINT operator_operator_id_key UNIQUE(operator_id, match_field_id);

ALTER TABLE filtergroup_group_permission DROP CONSTRAINT rettighet_pk;
CREATE SEQUENCE profiles.filtergroup_group_permission_id_seq;
ALTER TABLE filtergroup_group_permission ADD COLUMN id integer NOT NULL
	DEFAULT nextval('filtergroup_group_permission_id_seq')
	CONSTRAINT filtergroup_group_permission_pkey PRIMARY KEY;
ALTER TABLE filtergroup_group_permission ADD CONSTRAINT filtergroup_group_permission_accountgroup_id_key UNIQUE(accountgroup_id, filtergroup_id);

ALTER TABLE alertsubscription DROP CONSTRAINT varsleadresse_pk;
CREATE SEQUENCE profiles.alertsubscription_id_seq;
ALTER TABLE alertsubscription ADD COLUMN id integer NOT NULL
	DEFAULT nextval('alertsubscription_id_seq')
	CONSTRAINT alertsubscription_pkey PRIMARY KEY;
ALTER TABLE alertsubscription ADD CONSTRAINT alertsubscription_alert_address_id_key UNIQUE(alert_address_id, time_period_id, filter_group_id);

-- Fix alertqueue
ALTER TABLE accountalertqueue ADD subscription_id integer;
ALTER TABLE accountalertqueue ADD CONSTRAINT accountalertqueue_subscription_fkey
	FOREIGN KEY (subscription_id) REFERENCES alertsubscription(id)
	-- ON UPDATE CASCADE -- FIXME is CASCADE right here?
	-- ON DELETE CASCADE -- FIXME
	;
-- Try to upgrade accountalertqueue.addrid to subscription_id, this will not
-- guarantee a correct upgrade due to the db design issue we are fixing here.
-- We can only we sure that the alert is delivered to the correct address, not
-- necessarily at the correct time.
UPDATE accountalertqueue SET subscription_id = (SELECT id FROM alertsubscription WHERE alert_address_id = addrid LIMIT 1);
ALTER TABLE accountalertqueue DROP addrid;


-- Rename indexes so they match with the new english table names
ALTER INDEX account_pk RENAME TO account_pkey;
ALTER INDEX brukernavn_uniq RENAME TO account_login_key;
ALTER INDEX accountgroup_pk RENAME TO accountgroup_pkey;
ALTER INDEX alarmadresse_pk RENAME TO alertaddress_pkey;
ALTER INDEX brukerprofil_pk RENAME TO alertprofile_pkey;
ALTER INDEX preference_pk RENAME TO alertpreference_pkey;
ALTER INDEX tidsperiode_pk RENAME TO timeperiod_pkey;
ALTER INDEX utstyrgruppe_pk RENAME TO filtergroup_pkey;
ALTER INDEX utstyrfilter_pk RENAME TO filter_pkey;
ALTER INDEX matchfield_pk RENAME TO matchfield_pkey;
ALTER INDEX filtermatch_pk RENAME TO expression_pkey;
ALTER INDEX queue_pkey RENAME TO accountalertqueue_pkey;
ALTER INDEX navbarlink_pk RENAME TO navbarlink_pkey;
ALTER INDEX accountnavbar_pk RENAME TO accountnavbar_pkey;
ALTER INDEX privilege_pk RENAME TO privilege_pkey;
ALTER INDEX privilegename_uniq RENAME TO privilege_privilegename_key;


-- Rename foreign keys so they match with the new english names.
-- Not done so easy. One can't simply rename foreign keys, so we drop them, and
-- then re-add them.
ALTER TABLE accountgroup_accounts DROP CONSTRAINT account_exist;
ALTER TABLE accountgroup_accounts DROP CONSTRAINT group_exist;
ALTER TABLE accountgroup_accounts ADD CONSTRAINT accountgroup_accounts_account_id_fkey
	FOREIGN KEY(account_id) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE accountgroup_accounts ADD CONSTRAINT accountgroup_accounts_accountgroup_id_fkey
	FOREIGN KEY(accountgroup_id) REFERENCES accountgroup(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE accountproperty DROP CONSTRAINT account_exist;
ALTER TABLE accountproperty ADD CONSTRAINT accountproperty_accountid_fkey
	FOREIGN KEY(accountid) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE alertaddress DROP CONSTRAINT account_exist;
ALTER TABLE alertaddress ADD CONSTRAINT alertaddress_accountid_fkey
	FOREIGN KEY(accountid) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE alertprofile DROP CONSTRAINT bruker_eksisterer;
ALTER TABLE alertprofile ADD CONSTRAINT alertprofile_accountid_fkey
	FOREIGN KEY(accountid) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE alertpreference DROP CONSTRAINT account_exist;
ALTER TABLE alertpreference DROP CONSTRAINT brukerprofil_eksisterer;
ALTER TABLE alertpreference ADD CONSTRAINT alertpreference_accountid_fkey
	FOREIGN KEY(accountid) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE alertpreference ADD CONSTRAINT alertpreference_activeprofile_fkey
	FOREIGN KEY(activeprofile) REFERENCES alertprofile(id)
	ON DELETE SET NULL
	ON UPDATE CASCADE;

ALTER TABLE timeperiod DROP CONSTRAINT brukerprofil_eksisterer;
ALTER TABLE timeperiod ADD CONSTRAINT timeperiod_alert_profile_id_fkey
	FOREIGN KEY(alert_profile_id) REFERENCES alertprofile(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE filtergroup DROP CONSTRAINT account_exist;
ALTER TABLE filtergroup ADD CONSTRAINT filtergroup_owner_id_fkey
	FOREIGN KEY(owner_id) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE alertsubscription DROP CONSTRAINT alarmadresse_eksisterer;
ALTER TABLE alertsubscription DROP CONSTRAINT tidsperiode_eksisterer;
ALTER TABLE alertsubscription DROP CONSTRAINT utstyrgruppe_eksisterer;
ALTER TABLE alertsubscription ADD CONSTRAINT alertsubscription_alert_address_id_fkey
	FOREIGN KEY(alert_address_id) REFERENCES alertaddress(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE alertsubscription ADD CONSTRAINT alertsubscription_time_period_id_fkey
	FOREIGN KEY(time_period_id) REFERENCES timeperiod(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE alertsubscription ADD CONSTRAINT alertsubscription_filter_group_id_fkey
	FOREIGN KEY(filter_group_id) REFERENCES filtergroup(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE filtergroup_group_permission DROP CONSTRAINT accountgroup_exist;
ALTER TABLE filtergroup_group_permission DROP CONSTRAINT utstyrgruppe_eksisterer;
ALTER TABLE filtergroup_group_permission ADD CONSTRAINT filtergroup_group_permission_accountgroup_id_fkey
	FOREIGN KEY(accountgroup_id) REFERENCES accountgroup(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE filtergroup_group_permission ADD CONSTRAINT filtergroup_group_permission_filtergroup_id_fkey
	FOREIGN KEY(filtergroup_id) REFERENCES filtergroup(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE filter DROP CONSTRAINT user_exist;
ALTER TABLE filter ADD CONSTRAINT filter_owner_id_fkey
	FOREIGN KEY(owner_id) REFERENCES account(id)
	ON DELETE SET NULL
	ON UPDATE CASCADE;

ALTER TABLE filtergroupcontent DROP CONSTRAINT utstyrgruppeid_eksisterer;
ALTER TABLE filtergroupcontent DROP CONSTRAINT utstyrfilter_eksisterer;
ALTER TABLE filtergroupcontent ADD CONSTRAINT filtergroupcontent_filter_group_id_fkey
	FOREIGN KEY(filter_group_id) REFERENCES filtergroup(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE filtergroupcontent ADD CONSTRAINT filtergroupcontent_filter_id_fkey
	FOREIGN KEY(filter_id) REFERENCES filter(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE expression DROP CONSTRAINT matchfield_exist;
ALTER TABLE expression DROP CONSTRAINT utstyrfilter_eksisterer;
ALTER TABLE expression ADD CONSTRAINT expression_match_field_id_fkey
	FOREIGN KEY(match_field_id) REFERENCES matchfield(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE expression ADD CONSTRAINT expression_filter_id_fkey
	FOREIGN KEY(filter_id) REFERENCES filter(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE operator DROP CONSTRAINT matchfield_eksisterer;
ALTER TABLE operator ADD CONSTRAINT operator_match_field_id_fkey
	FOREIGN KEY(match_field_id) REFERENCES matchfield(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE navbarlink DROP CONSTRAINT account_exists;
ALTER TABLE navbarlink ADD CONSTRAINT navbarlink_accountid_fkey
	FOREIGN KEY(accountid) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE accountnavbar DROP CONSTRAINT account_exists;
ALTER TABLE accountnavbar DROP CONSTRAINT navbarlink_exists;
ALTER TABLE accountnavbar ADD CONSTRAINT accountnavbar_accountid_fkey
	FOREIGN KEY(accountid) REFERENCES account(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE accountnavbar ADD CONSTRAINT accountnavbar_navbarlinkid_fkey
	FOREIGN KEY(navbarlinkid) REFERENCES navbarlink(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;

ALTER TABLE accountgroupprivilege DROP CONSTRAINT accountgroup_exists;
ALTER TABLE accountgroupprivilege DROP CONSTRAINT privilege_exists;
ALTER TABLE accountgroupprivilege ADD CONSTRAINT accountgroupprivilege_accountgroupid_fkey
	FOREIGN KEY (accountgroupid) REFERENCES accountgroup(id)
	ON DELETE CASCADE
	ON UPDATE CASCADE;
ALTER TABLE accountgroupprivilege ADD CONSTRAINT accountgroupprivilege_privilegeid_fkey
	FOREIGN KEY (privilegeid) REFERENCES privilege
	ON DELETE CASCADE
	ON UPDATE CASCADE;

-- FIXME
CREATE SEQUENCE profiles.alertsender_id_seq START 1000;
CREATE TABLE profiles.alertsender (
	id integer NOT NULL DEFAULT nextval('alertsender_id_seq'),
	name varchar(100) NOT NULL,
	handler varchar(100) NOT NULL,

	CONSTRAINT alertsender_unique_name UNIQUE(name),
	CONSTRAINT alertsender_unique_handler UNIQUE(handler),
	CONSTRAINT alertsender_pkey  PRIMARY KEY(id)
);

-- ACCOUNTINGROUP
-- View for compability with older code that thinks accountgroup_accounts is
-- still called accountingroup.
CREATE VIEW profiles.accountingroup AS (
    SELECT
        accountgroup_accounts.account_id AS accountid,
        accountgroup_accounts.accountgroup_id AS groupid
    FROM
        accountgroup_accounts
);


-- report_access is not used by any systems so time to purge it from the db.
DELETE FROM privilege WHERE privilegename = 'report_access';

-- Ensure that users are part of everyone and authenticated groups
CREATE OR REPLACE FUNCTION profiles.group_membership() RETURNS trigger AS $group_membership$
        BEGIN
                IF NEW.id >= 1000 THEN
                        INSERT INTO accountgroup_accounts (accountgroup_id, account_id) VALUES (2, NEW.id);
                        INSERT INTO accountgroup_accounts (accountgroup_id, account_id) VALUES (3, NEW.id);
                END IF; RETURN NULL;
        END;
$group_membership$ LANGUAGE plpgsql;

CREATE TRIGGER group_membership AFTER INSERT ON account
        FOR EACH ROW EXECUTE PROCEDURE group_membership();

-- Add all users to "Everyone" and "Authenticated users" 
INSERT INTO accountgroup_accounts SELECT account.id, 2 FROM account WHERE account.id >= 1000 AND account.id NOT IN (SELECT account.id FROM accountgroup_accounts WHERE accountgroup_id = 2);
INSERT INTO accountgroup_accounts SELECT account.id, 3 FROM account WHERE account.id >= 1000 AND account.id NOT IN (SELECT account.id FROM accountgroup_accounts WHERE accountgroup_id = 3);

INSERT INTO accountgroup_accounts VALUES (0,2); -- add default to Everyone
INSERT INTO accountgroup_accounts VALUES (1,2); -- add admin to Everyone
INSERT INTO accountgroup_accounts VALUES (1,3); -- add admin to Authenticated users

-- Update navbar links
UPDATE navbarlink SET uri = '/userinfo/' WHERE uri = '/index/userinfo';
UPDATE navbarlink SET uri = '/useradmin/' WHERE uri = '/useradmin/index';

-- Allow authenticated users to visit ipdevinfo
INSERT INTO accountgroupprivilege (accountgroupid, privilegeid, target)
VALUES (3, 2, '^/ipdevinfo/?');

-- Allow anonymous users to visit the new /userinfo tool.
INSERT INTO accountgroupprivilege (accountgroupid, privilegeid, target)
VALUES (2, 2, E'^/userinfo/?');


------------------------------------------------------------------------------
-- netmap helper tables
------------------------------------------------------------------------------

CREATE TABLE netmap_position(
sysname VARCHAR PRIMARY KEY NOT NULL,
xpos double precision NOT NULL,
ypos double precision NOT NULL
);

COMMIT;

